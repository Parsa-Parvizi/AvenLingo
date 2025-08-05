import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/core/HomeView.vue'
import AboutUsView from '@/views/core/AboutUsView.vue'
import ContactUsView from '@/views/core/ContactUsView.vue'

import LoginView from '../views/Auth/HomeView.vue'
import RegisterView from '../views/Auth/RegisterView.vue'

import StudentDashboardView from '..StudentDashboardView.vue'
import TeacherDashboard from '../views/TeacherDetailView.vue'

import AllCoursesView from '@/views/course/AllCoursesView.vue'
import AllTeachersView from '@/views/AllTeachersView.vue'

import TeacherDetailView from '@/views/TeacherDetailView.vue'

import FeaturedCoursesView from '@/views/FeaturedCoursesView.vue'
import LatestCoursesView from '@/views/LatestCoursesView.vue'
import CategoryCoursesView from '@/views/CategoryCoursesView.vue'
import CourseDetailView from '@/views/course/CourseDetailView.vue'

import NotFoundView from '@/views/NotFoundView.vue'

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/aboutus', name: 'aboutus', component: AboutUsView },
  { path: '/contactus', name: 'contactus', component: ContactUsView },

  { path: '/auth/login', name: 'login', component: LoginView },
  { path: '/auth/register', name: 'register', component: RegisterView },
  
  { path: '/teachers/allteacher', name: 'allteacher', component: AllTeachersView },
  { path: '/teachers/detail/:teacher_id', name: 'teacherdetail', component: TeacherDetailView, props: true },

  { path: '/auth/student/dashboard', name: 'studentdashboard', component: StudentDashboardView },
  { path: '/teacher/dashboard', name: 'teacherdashboard', component: TeacherDashboard},

  { path: '/course', name: 'allcourse', component: AllCoursesView },
  { path: '/course/featured', name: 'featured', component: FeaturedCoursesView },
  { path: '/course/latest', name: 'latest', component: LatestCoursesView },
  { path: '/course/category/:category_slug', name: 'category', component: CategoryCoursesView, props: true },
  { path: '/course/detail/:course_slug', name: 'coursedetail', component: CourseDetailView, props: true },

  { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFoundView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
