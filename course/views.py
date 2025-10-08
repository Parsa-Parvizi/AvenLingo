from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q, Case, When, IntegerField, Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseForbidden, JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Course, Category, Assignment, AssignmentSubmission, LANGUAGE_CHOICES, CLASS_TYPE_CHOICES, ONLINE_CHOICES
from account.models import Teacher
from .forms import AssignmentForm, AssignmentSubmissionForm, AssignmentGradingForm
import re


def all_courses_view(request):
    """نمایش همه کلاس‌ها با جستجو و فیلتر پیشرفته"""
    # شروع با دوره‌های فعال
    courses = Course.objects.select_related('teacher', 'category').filter(is_active=True)
    
    # متغیرهای فیلتر
    level = request.GET.get('level', '').strip()
    age_group = request.GET.get('age_group', '').strip()
    course_type = request.GET.get('type', '').strip()
    language = request.GET.get('language', '').strip()
    class_type = request.GET.get('class_type', '').strip()
    search = request.GET.get('search', '').strip()
    
    # جستجوی پیشرفته و هوشمند
    if search:
        # تقسیم کلمات جستجو
        search_terms = re.findall(r'\w+', search.lower())
        
        if search_terms:
            # ایجاد کوئری پیچیده برای جستجوی هوشمند
            search_queries = Q()
            
            for term in search_terms:
                # جستجو در فیلدهای مختلف با وزن‌های متفاوت
                term_query = (
                    # عنوان دوره (وزن بالا)
                    Q(title__icontains=term) |
                    
                    # نام کامل معلم (وزن بالا)
                    Q(teacher__user__first_name__icontains=term) |
                    Q(teacher__user__last_name__icontains=term) |
                    
                    # توضیحات کوتاه (وزن متوسط)
                    Q(short_description__icontains=term) |
                    
                    # توضیحات کامل (وزن پایین)
                    Q(description__icontains=term) |
                    
                    # دسته‌بندی (وزن متوسط)
                    Q(category__name__icontains=term) |
                    
                    # نوع کلاس (وزن متوسط)
                    Q(class_type__icontains=term) |
                    
                    # سطح (وزن متوسط)
                    Q(level__icontains=term) |
                    
                    # گروه سنی (وزن متوسط)
                    Q(age_group__icontains=term) |
                    
                    # محل برگزاری (وزن پایین)
                    Q(location__icontains=term)
                )
                
                search_queries &= term_query
            
            courses = courses.filter(search_queries)
            
            # اولویت‌بندی نتایج بر اساس میزان تطبیق
            courses = courses.annotate(
                relevance_score=Case(
                    # تطبیق کامل عنوان
                    When(title__iexact=search, then=100),
                    # شروع عنوان با عبارت جستجو
                    When(title__istartswith=search, then=90),
                    # حاوی عبارت جستجو در عنوان
                    When(title__icontains=search, then=80),
                    
                    # تطبیق کامل نام معلم
                    When(Q(teacher__user__first_name__iexact=search) | 
                         Q(teacher__user__last_name__iexact=search), then=85),
                    # شروع نام معلم با عبارت جستجو
                    When(Q(teacher__user__first_name__istartswith=search) | 
                         Q(teacher__user__last_name__istartswith=search), then=75),
                    # حاوی عبارت جستجو در نام معلم
                    When(Q(teacher__user__first_name__icontains=search) | 
                         Q(teacher__user__last_name__icontains=search), then=70),
                    
                    # تطبیق در توضیحات کوتاه
                    When(short_description__icontains=search, then=60),
                    # تطبیق در دسته‌بندی
                    When(category__name__icontains=search, then=55),
                    # تطبیق در نوع کلاس
                    When(class_type__icontains=search, then=50),
                    # تطبیق در سایر فیلدها
                    default=30,
                    output_field=IntegerField()
                )
            ).order_by('-relevance_score', '-is_featured', '-created_at')
    else:
        # ترتیب پیش‌فرض بدون جستجو
        courses = courses.order_by('-is_featured', '-created_at')
    
    # اعمال فیلترها
    if level:
        courses = courses.filter(level=level)
    
    if age_group:
        courses = courses.filter(age_group=age_group)
    
    if course_type:
        if course_type == 'online':
            courses = courses.filter(is_online=True)
        elif course_type == 'offline':
            courses = courses.filter(is_online=False)
        elif course_type == 'in_person':
            courses = courses.filter(is_online=False, location__isnull=False)
    
    if language:
        courses = courses.filter(category__language=language)
    
    if class_type:
        courses = courses.filter(class_type=class_type)
    
    # دریافت دسته‌بندی‌ها برای فیلتر
    categories = Category.objects.filter(is_active=True)
    
    # محاسبه آمار جستجو
    total_courses = Course.objects.filter(is_active=True).count()
    filtered_count = courses.count()
    
    # پیاده‌سازی pagination
    paginator = Paginator(courses, 21)  # 21 کلاس در هر صفحه
    page = request.GET.get('page')
    
    try:
        paginated_courses = paginator.page(page)
    except PageNotAnInteger:
        # اگر صفحه عدد نباشد، صفحه اول را نشان بده
        paginated_courses = paginator.page(1)
    except EmptyPage:
        # اگر صفحه خالی باشد، آخرین صفحه را نشان بده
        paginated_courses = paginator.page(paginator.num_pages)
    
    context = {
        'courses': paginated_courses,
        'categories': categories,
        'current_level': level,
        'current_age_group': age_group,
        'current_type': course_type,
        'current_language': language,
        'current_class_type': class_type,
        'search': search,
        'languages': dict(LANGUAGE_CHOICES),
        'class_types': dict(CLASS_TYPE_CHOICES),
        'online_choices': dict(ONLINE_CHOICES),
        'total_courses': total_courses,
        'filtered_count': filtered_count,
        'has_filters': any([level, age_group, course_type, language, class_type, search]),
    }
    
    return render(request, 'course/all_courses.html', context)


def featured_courses_view(request):
    """نمایش کلاس‌های ویژه"""
    featured_courses = Course.objects.filter(is_active=True, is_featured=True).order_by('-created_at')  # type: ignore
    
    # پیاده‌سازی pagination
    paginator = Paginator(featured_courses, 20)  # 20 کلاس در هر صفحه
    page = request.GET.get('page')
    
    try:
        paginated_courses = paginator.page(page)
    except PageNotAnInteger:
        paginated_courses = paginator.page(1)
    except EmptyPage:
        paginated_courses = paginator.page(paginator.num_pages)
    
    return render(request, 'course/featured_courses.html', {'courses': paginated_courses})


def category_courses_view(request, category_slug):
    """نمایش کلاس‌های یک دسته‌بندی خاص"""
    category = get_object_or_404(Category, slug=category_slug, is_active=True)
    courses = Course.objects.filter(category=category, is_active=True).order_by('-is_featured', '-created_at')  # type: ignore
    
    # پیاده‌سازی pagination
    paginator = Paginator(courses, 21)  # 21 کلاس در هر صفحه
    page = request.GET.get('page')
    
    try:
        paginated_courses = paginator.page(page)
    except PageNotAnInteger:
        paginated_courses = paginator.page(1)
    except EmptyPage:
        paginated_courses = paginator.page(paginator.num_pages)
    
    context = {
        'category': category,
        'courses': paginated_courses,
    }
    
    return render(request, 'course/category_courses.html', context)


def course_detail_view(request, course_slug):
    """نمایش جزئیات کلاس"""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    
    # کلاس‌های مشابه (همیشه 3 تا)
    similar_courses = []
    
    # اول از همان دسته‌بندی بگیریم
    category_courses = Course.objects.filter( # type: ignore
        is_active=True,
        category=course.category
    ).exclude(id=course.id).order_by('-is_featured', '-created_at')[:3]  # type: ignore
    similar_courses.extend(list(category_courses))
    
    # اگر کمتر از 3 تا بود، از همان سطح بگیریم
    if len(similar_courses) < 3:
        level_courses = Course.objects.filter( # type: ignore
            is_active=True,
            level=course.level
        ).exclude(
            id__in=[course.id] + [c.id for c in similar_courses]
        ).order_by('-is_featured', '-created_at')[:(3 - len(similar_courses))]  # type: ignore
        similar_courses.extend(list(level_courses))
    
    # اگر هنوز کمتر از 3 تا است، از همه دوره‌های فعال بگیریم
    if len(similar_courses) < 3:
        other_courses = Course.objects.filter( # type: ignore
            is_active=True
        ).exclude(
            id__in=[course.id] + [c.id for c in similar_courses]
        ).order_by('-is_featured', '-created_at')[:(3 - len(similar_courses))]  # type: ignore
        similar_courses.extend(list(other_courses))
    
    # دیگر دوره‌های استاد (بهترین دوره‌ها)
    teacher_other_courses = Course.objects.filter( # type: ignore
        is_active=True,
        teacher=course.teacher,
        status='published'
    ).exclude(id=course.id).order_by( # type: ignore
        '-is_featured',  # اولویت با دوره‌های ویژه
        '-enrollments__status',  # سپس بر اساس تعداد ثبت‌نام
        '-created_at'  # و در نهایت جدیدترین
    )[:3]  # type: ignore
    
    # Check if user is enrolled in this course
    user_enrollment = None
    if request.user.is_authenticated and hasattr(request.user, 'user_type') and request.user.user_type == 'student':
        try:
            from account.models import Student
            from enrollment.models import Enrollment
            student = Student.objects.get(user=request.user)
            user_enrollment = Enrollment.objects.filter(student=student, course=course).first()
        except Student.DoesNotExist:
            pass
    
    # Calculate available seats (only confirmed enrollments count)
    confirmed_enrollments = course.enrollments.filter(status='confirmed').count()
    available_seats = course.capacity - confirmed_enrollments
    is_full = confirmed_enrollments >= course.capacity
    
    context = {
        'course': course,
        'similar_courses': similar_courses,
        'teacher_other_courses': teacher_other_courses,
        'user_enrollment': user_enrollment,
        'available_seats': available_seats,
        'is_full': is_full,
    }
    
    return render(request, 'course/course_detail.html', context)


def latest_courses_view(request):
    """نمایش آخرین کلاس‌ها"""
    latest_courses = Course.objects.filter(is_active=True).order_by('-created_at')[:6]  # type: ignore
    return render(request, 'course/latest_courses.html', {'courses': latest_courses})


@login_required
def student_course_detail_view(request, course_id):
    """صفحه مخصوص زبان‌آموز برای مشاهده دوره‌های ثبت‌نام شده"""
    # بررسی اینکه کاربر دانش‌آموز است
    if not hasattr(request.user, 'user_type') or request.user.user_type != 'student':
        if hasattr(request.user, 'user_type') and request.user.user_type == 'teacher':
            messages.error(request, 'شما دسترسی لازم برای مشاهده این صفحه را ندارید. شما به عنوان معلم وارد شده‌اید.')
        elif request.user.is_staff or request.user.is_superuser:
            messages.error(request, 'شما دسترسی لازم برای مشاهده این صفحه را ندارید. شما به عنوان ادمین وارد شده‌اید.')
        else:
            messages.error(request, 'شما دسترسی لازم برای مشاهده این صفحه را ندارید.')
        return redirect('core:home')
    
    # دریافت دوره
    course = get_object_or_404(Course, id=course_id, is_active=True)
    
    # بررسی اینکه کاربر در این دوره ثبت‌نام کرده باشد
    try:
        from account.models import Student
        from enrollment.models import Enrollment
        student = Student.objects.get(user=request.user)
        enrollment = Enrollment.objects.get(student=student, course=course, status='confirmed')
    except (Student.DoesNotExist, Enrollment.DoesNotExist):
        messages.error(request, 'شما در این دوره ثبت‌نام نکرده‌اید یا ثبت‌نام شما هنوز تأیید نشده است.')
        return redirect('dashboard:student_calendar')
    
    # دریافت تکالیف دوره
    assignments = Assignment.objects.filter(
        course=course,
        is_active=True
    ).order_by('-created_at')
    
    # بررسی وضعیت ارسال تکالیف برای دانش‌آموز
    assignment_submissions = {}
    for assignment in assignments:
        try:
            submission = AssignmentSubmission.objects.get(
                assignment=assignment,
                student=student
            )
            assignment_submissions[assignment.id] = submission
        except AssignmentSubmission.DoesNotExist:
            assignment_submissions[assignment.id] = None
    
    # اضافه کردن اطلاعات ارسال به هر تکلیف
    for assignment in assignments:
        submission = assignment_submissions[assignment.id]
        if submission:
            assignment.submission_status = submission.status
            assignment.submission_score = submission.score
            assignment.submission_feedback = submission.feedback
        else:
            assignment.submission_status = None
            assignment.submission_score = None
            assignment.submission_feedback = None
        
        # بررسی امکان ارسال تکلیف
        can_submit, message = assignment.can_submit(student)
        assignment.can_submit = can_submit
        assignment.submit_message = message
    
    # اطلاعات دوره و مدرس
    teacher = course.teacher
    
    context = {
        'course': course,
        'enrollment': enrollment,
        'teacher': teacher,
        'student': student,
        'assignments': assignments,
        'assignment_submissions': assignment_submissions,
    }
    
    return render(request, 'course/student_course_detail.html', context)


# Assignment Views
class AssignmentCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ایجاد تکلیف جدید توسط معلم"""
    model = Assignment
    form_class = AssignmentForm
    template_name = 'course/assignment_create.html'
    
    def test_func(self):
        """بررسی اینکه کاربر معلم است"""
        return self.request.user.is_teacher
    
    def get_course(self):
        """دریافت دوره از URL"""
        course_id = self.kwargs.get('course_id')
        return get_object_or_404(Course, id=course_id)
    
    def get_teacher(self):
        """دریافت معلم از کاربر فعلی"""
        try:
            return self.request.user.teacher_profile
        except Teacher.DoesNotExist:
            raise Http404("معلم یافت نشد")
    
    def get_form_kwargs(self):
        """تنظیم معلم و دوره در فرم"""
        kwargs = super().get_form_kwargs()
        kwargs['teacher'] = self.get_teacher()
        kwargs['course'] = self.get_course()
        return kwargs
    
    def get_success_url(self):
        """URL پس از ایجاد موفق تکلیف"""
        return reverse('course:assignment_list', kwargs={'course_id': self.get_course().id})
    
    def get_context_data(self, **kwargs):
        """اضافه کردن اطلاعات اضافی به context"""
        context = super().get_context_data(**kwargs)
        context['course'] = self.get_course()
        context['teacher'] = self.get_teacher()
        return context
    
    def form_valid(self, form):
        """پس از اعتبارسنجی موفق فرم"""
        messages.success(self.request, 'تکلیف با موفقیت ایجاد شد.')
        return super().form_valid(form)


class AssignmentListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """لیست تکالیف یک دوره"""
    model = Assignment
    template_name = 'course/assignment_list.html'
    context_object_name = 'assignments'
    paginate_by = 10
    
    def test_func(self):
        """بررسی دسترسی کاربر"""
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        
        # معلم دوره یا دانش‌آموز ثبت‌نام شده
        if self.request.user.is_teacher:
            return course.teacher.user == self.request.user
        elif self.request.user.is_student:
            return course.students.filter(user=self.request.user).exists()
        return False
    
    def get_queryset(self):
        """دریافت تکالیف دوره"""
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        return Assignment.objects.filter(course=course).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """اضافه کردن اطلاعات اضافی"""
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        
        # اگر کاربر دانش‌آموز است، وضعیت ارسال هر تکلیف را اضافه کن
        if self.request.user.is_student:
            student = get_object_or_404(self.request.user.student_profile)
            assignments_with_status = []
            
            for assignment in context['assignments']:
                can_submit, message = assignment.can_submit(student)
                submission = AssignmentSubmission.objects.filter(
                    assignment=assignment, student=student
                ).first()
                
                assignments_with_status.append({
                    'assignment': assignment,
                    'can_submit': can_submit,
                    'message': message,
                    'submission': submission,
                })
            
            context['assignments_with_status'] = assignments_with_status
        
        return context


class AssignmentDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """جزئیات تکلیف"""
    model = Assignment
    template_name = 'course/assignment_detail.html'
    context_object_name = 'assignment'
    
    def test_func(self):
        """بررسی دسترسی کاربر"""
        assignment = self.get_object()
        
        # معلم دوره یا دانش‌آموز ثبت‌نام شده
        if self.request.user.is_teacher:
            return assignment.course.teacher.user == self.request.user
        elif self.request.user.is_student:
            return assignment.course.students.filter(user=self.request.user).exists()
        return False
    
    def get_context_data(self, **kwargs):
        """اضافه کردن اطلاعات اضافی"""
        context = super().get_context_data(**kwargs)
        assignment = self.get_object()
        
        context['course'] = assignment.course
        
        # اگر کاربر دانش‌آموز است
        if self.request.user.is_student:
            student = get_object_or_404(self.request.user.student_profile)
            can_submit, message = assignment.can_submit(student)
            submission = AssignmentSubmission.objects.filter(
                assignment=assignment, student=student
            ).first()
            
            context['can_submit'] = can_submit
            context['message'] = message
            context['submission'] = submission
            context['student'] = student
        
        # اگر کاربر معلم است
        elif self.request.user.is_teacher:
            submissions = AssignmentSubmission.objects.filter(
                assignment=assignment
            ).select_related('student__user').order_by('-submitted_at')
            
            context['submissions'] = submissions
            context['submission_count'] = submissions.count()
        
        return context


class AssignmentSubmissionView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """ارسال تکلیف توسط دانش‌آموز"""
    model = AssignmentSubmission
    form_class = AssignmentSubmissionForm
    template_name = 'course/assignment_submit.html'
    
    def test_func(self):
        """بررسی اینکه کاربر دانش‌آموز است"""
        return self.request.user.is_student
    
    def get_assignment(self):
        """دریافت تکلیف از URL"""
        assignment_id = self.kwargs.get('assignment_id')
        return get_object_or_404(Assignment, id=assignment_id)
    
    def get_student(self):
        """دریافت دانش‌آموز از کاربر فعلی"""
        return get_object_or_404(self.request.user.student_profile)
    
    def get_form_kwargs(self):
        """تنظیم تکلیف و دانش‌آموز در فرم"""
        kwargs = super().get_form_kwargs()
        kwargs['assignment'] = self.get_assignment()
        kwargs['student'] = self.get_student()
        return kwargs
    
    def get_success_url(self):
        """URL پس از ارسال موفق تکلیف"""
        return reverse('course:assignment_detail', kwargs={'pk': self.get_assignment().id})
    
    def get_context_data(self, **kwargs):
        """اضافه کردن اطلاعات اضافی"""
        context = super().get_context_data(**kwargs)
        assignment = self.get_assignment()
        
        context['assignment'] = assignment
        context['course'] = assignment.course
        context['student'] = self.get_student()
        
        # بررسی امکان ارسال
        can_submit, message = assignment.can_submit(self.get_student())
        context['can_submit'] = can_submit
        context['message'] = message
        
        return context
    
    def form_valid(self, form):
        """پس از اعتبارسنجی موفق فرم"""
        # بررسی مجدد امکان ارسال
        assignment = self.get_assignment()
        student = self.get_student()
        
        can_submit, message = assignment.can_submit(student)
        if not can_submit:
            messages.error(self.request, message)
            return self.form_invalid(form)
        
        messages.success(self.request, 'تکلیف شما با موفقیت ارسال شد.')
        return super().form_valid(form)


class AssignmentSubmissionGradingView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """نمره‌دهی تکلیف توسط معلم"""
    model = AssignmentSubmission
    form_class = AssignmentGradingForm
    template_name = 'course/assignment_grade.html'
    
    def test_func(self):
        """بررسی اینکه کاربر معلم دوره است"""
        submission = self.get_object()
        return submission.assignment.course.teacher.user == self.request.user
    
    def get_success_url(self):
        """URL پس از نمره‌دهی موفق"""
        return reverse('course:assignment_detail', kwargs={'pk': self.get_object().assignment.id})
    
    def get_context_data(self, **kwargs):
        """اضافه کردن اطلاعات اضافی"""
        context = super().get_context_data(**kwargs)
        submission = self.get_object()
        
        context['assignment'] = submission.assignment
        context['course'] = submission.assignment.course
        context['student'] = submission.student
        
        return context
    
    def form_valid(self, form):
        """پس از اعتبارسنجی موفق فرم"""
        submission = form.save(commit=False)
        submission.graded_by = get_object_or_404(self.request.user.teacher_profile)
        submission.graded_at = timezone.now()
        submission.save()
        
        messages.success(self.request, 'نمره‌دهی تکلیف با موفقیت انجام شد.')
        return super().form_valid(form)


@login_required
def download_assignment_file(request, assignment_id):
    """دانلود فایل دستورالعمل تکلیف"""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # بررسی دسترسی
    if request.user.is_teacher:
        if assignment.course.teacher.user != request.user:
            return HttpResponseForbidden("شما دسترسی لازم ندارید.")
    elif request.user.is_student:
        if not assignment.course.students.filter(user=request.user).exists():
            return HttpResponseForbidden("شما دسترسی لازم ندارید.")
    else:
        return HttpResponseForbidden("شما دسترسی لازم ندارید.")
    
    if not assignment.instruction_file:
        messages.error(request, "فایل دستورالعمل موجود نیست.")
        return redirect('course:assignment_detail', pk=assignment_id)
    
    response = HttpResponse(assignment.instruction_file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{assignment.instruction_file.name}"'
    return response


@login_required
def download_submission_file(request, submission_id):
    """دانلود فایل ارسالی دانش‌آموز"""
    submission = get_object_or_404(AssignmentSubmission, id=submission_id)
    
    # بررسی دسترسی
    if request.user.is_teacher:
        if submission.assignment.course.teacher.user != request.user:
            return HttpResponseForbidden("شما دسترسی لازم ندارید.")
    elif request.user.is_student:
        if submission.student.user != request.user:
            return HttpResponseForbidden("شما دسترسی لازم ندارید.")
    else:
        return HttpResponseForbidden("شما دسترسی لازم ندارید.")
    
    if not submission.submission_file:
        messages.error(request, "فایل ارسالی موجود نیست.")
        return redirect('course:assignment_detail', pk=submission.assignment.id)
    
    response = HttpResponse(submission.submission_file.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{submission.submission_file.name}"'
    return response




# Student Exam Views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from django.views import View

class StudentExamsView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """لیست امتحانات دانشجو"""
    template_name = 'course/student_exams.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'student'
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'teacher':
                messages.error(self.request, 'این صفحه فقط برای زبان‌آموزان است. شما به عنوان معلم وارد شده‌اید.')
            elif self.request.user.is_staff or self.request.user.is_superuser:
                messages.error(self.request, 'این صفحه فقط برای زبان‌آموزان است. شما به عنوان ادمین وارد شده‌اید.')
            else:
                messages.error(self.request, 'شما باید به عنوان دانش‌آموز وارد شوید.')
            return redirect('core:home')
        return super().handle_no_permission()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from account.models import Student
        from enrollment.models import Enrollment
        from course.models import Exam
        from django.utils import timezone
        
        try:
            student = Student.objects.get(user=self.request.user)
        except Student.DoesNotExist:
            return context
        
        # دوره‌های ثبت‌نام شده
        enrollments = Enrollment.objects.filter(student=student, status='confirmed')
        course_ids = enrollments.values_list('course_id', flat=True)
        
        # امتحانات دوره‌ها
        all_exams = Exam.objects.filter(course_id__in=course_ids, is_active=True)
        
        # دسته‌بندی امتحانات
        upcoming_exams = []
        active_exams = []
        past_exams = []
        
        now = timezone.now()
        for exam in all_exams:
            can_see, _ = exam.can_student_see(student)
            if not can_see:
                continue
            
            if exam.is_ended():
                past_exams.append(exam)
            elif exam.is_started():
                # محاسبه دقایق باقی‌مانده
                time_left = exam.scheduled_end - now
                exam.minutes_remaining = int(time_left.total_seconds() / 60) if time_left.total_seconds() > 0 else 0
                active_exams.append(exam)
            else:
                upcoming_exams.append(exam)
        
        context['student'] = student
        context['upcoming_exams'] = upcoming_exams
        context['active_exams'] = active_exams
        context['past_exams'] = past_exams
        
        return context


class StudentTakeExamView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """صفحه شرکت در امتحان"""
    template_name = 'course/student_take_exam.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'student'
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'teacher':
                messages.error(self.request, 'این صفحه فقط برای زبان‌آموزان است. شما به عنوان معلم وارد شده‌اید.')
            elif self.request.user.is_staff or self.request.user.is_superuser:
                messages.error(self.request, 'این صفحه فقط برای زبان‌آموزان است. شما به عنوان ادمین وارد شده‌اید.')
            else:
                messages.error(self.request, 'شما باید به عنوان دانش‌آموز وارد شوید.')
            return redirect('core:home')
        return super().handle_no_permission()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from account.models import Student
        from course.models import Exam, ExamParticipation
        from django.utils import timezone
        
        exam_id = kwargs.get('exam_id')
        
        try:
            student = Student.objects.get(user=self.request.user)
        except Student.DoesNotExist:
            return context
        
        exam = get_object_or_404(Exam, id=exam_id)
        
        # بررسی دسترسی
        can_participate, message = exam.can_student_participate(student)
        
        # پیدا کردن شرکت فعلی یا ایجاد جدید
        participation = ExamParticipation.objects.filter(
            exam=exam,
            student=student
        ).order_by('-attempt_number').first()
        
        # اگر امتحان جدید است یا می‌خواهد دوباره شرکت کند
        is_new_attempt = not participation or participation.status == 'submitted'
        
        context['exam'] = exam
        context['student'] = student
        context['can_participate'] = can_participate
        context['message'] = message
        context['participation'] = participation
        context['is_new_attempt'] = is_new_attempt
        context['time_remaining'] = exam.time_until_end()
        
        return context
    
    def post(self, request, *args, **kwargs):
        from account.models import Student
        from course.models import Exam, ExamParticipation
        from django.utils import timezone
        
        exam_id = kwargs.get('exam_id')
        action = request.POST.get('action')
        
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            messages.error(request, 'شما مجاز به این عملیات نیستید.')
            return redirect('dashboard:student_calendar')
        
        exam = get_object_or_404(Exam, id=exam_id)
        
        if action == 'start':
            # شروع امتحان
            can_participate, message = exam.can_student_participate(student)
            if not can_participate:
                messages.error(request, message)
                return redirect('course:student_exams')
            
            # ایجاد شرکت جدید
            attempt_number = ExamParticipation.objects.filter(exam=exam, student=student).count() + 1
            
            participation = ExamParticipation.objects.create(
                exam=exam,
                student=student,
                attempt_number=attempt_number,
                status='started',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
            
            messages.success(request, 'امتحان شروع شد. موفق باشید!')
            return redirect('course:take_exam', exam_id=exam.id)
        
        elif action == 'submit':
            # ارسال پاسخ
            participation = ExamParticipation.objects.filter(
                exam=exam,
                student=student,
                status='started'
            ).order_by('-attempt_number').first()
            
            if not participation:
                messages.error(request, 'شرکتی یافت نشد.')
                return redirect('course:student_exams')
            
            # ذخیره پاسخ‌ها
            answer_file = request.FILES.get('answer_file')
            answer_text = request.POST.get('answer_text', '')
            
            if answer_file:
                participation.answer_file = answer_file
            if answer_text:
                participation.answer_text = answer_text
            
            participation.status = 'submitted'
            participation.submitted_at = timezone.now()
            participation.save()
            
            messages.success(request, 'پاسخ شما با موفقیت ارسال شد!')
            return redirect('course:exam_result', exam_id=exam.id, participation_id=participation.id)
        
        return redirect('course:take_exam', exam_id=exam.id)


class StudentExamResultView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """نمایش نتیجه امتحان"""
    template_name = 'course/student_exam_result.html'
    
    def test_func(self):
        return hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'student'
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            if hasattr(self.request.user, 'user_type') and self.request.user.user_type == 'teacher':
                messages.error(self.request, 'این صفحه فقط برای زبان‌آموزان است. شما به عنوان معلم وارد شده‌اید.')
            elif self.request.user.is_staff or self.request.user.is_superuser:
                messages.error(self.request, 'این صفحه فقط برای زبان‌آموزان است. شما به عنوان ادمین وارد شده‌اید.')
            else:
                messages.error(self.request, 'شما باید به عنوان دانش‌آموز وارد شوید.')
            return redirect('core:home')
        return super().handle_no_permission()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from account.models import Student
        from course.models import ExamParticipation
        
        participation_id = kwargs.get('participation_id')
        
        try:
            student = Student.objects.get(user=self.request.user)
        except Student.DoesNotExist:
            return context
        
        participation = get_object_or_404(
            ExamParticipation,
            id=participation_id,
            student=student
        )
        
        context['participation'] = participation
        context['exam'] = participation.exam
        context['student'] = student
        
        return context
