<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import CourseCard from '@/components/course/CourseCard.vue'
// import CategoryCard from '@/components/course/CategoryCard.vue'
import CategoryCard from '../course/CategoryCard.vue'
import TeacherCard from '@/components/teacher/TeacherCard.vue'
import FaqItem from '@/components/common/FaqItem.vue'

// Props or mock data
const heroSlider = ref(null)
const featuredCourses = ref([])
const latestCourses = ref([])
const categories = ref([])
const courseGuide = ref(null)
const teachers = ref([])
const faqs = ref([])
</script>

<template>
  <div>
    <!-- Hero Slider -->
    <section class="hero-slider" v-if="heroSlider && heroSlider.slides.length">
      <div class="slides">
        <div
          v-for="(slide, index) in heroSlider.slides"
          :key="index"
          v-if="slide.is_active"
          class="slide"
          :class="{ active: index === 0 }"
        >
          <h1>{{ slide.title }}</h1>
          <p>{{ slide.subtitle }}</p>
          <a
            v-if="slide.button_text && slide.button_url"
            :href="slide.button_url"
            class="btn"
            :class="slide.button_style"
          >
            {{ slide.button_text }}
          </a>
        </div>
      </div>
      <div class="slider-dots">
        <span
          v-for="(slide, index) in heroSlider.slides"
          :key="'dot-' + index"
          v-if="slide.is_active"
          class="dot"
          :class="{ active: index === 0 }"
          :data-slide="index"
        ></span>
      </div>
    </section>

    <!-- Default Hero if none exists -->
    <section class="hero-slider" v-else>
      <div class="slides">
        <div class="slide active">
          <h1>آکادمی زبان Aurora</h1>
          <p>با روش‌های نوین و اساتید حرفه‌ای، زبان انگلیسی را آسان بیاموزید.</p>
          <RouterLink to="/courses" class="btn btn-primary">مشاهده دوره‌ها</RouterLink>
        </div>
        <div class="slide">
          <h1>کلاس‌های آنلاین و حضوری</h1>
          <p>با انعطاف‌پذیری بالا، هرجا هستید آموزش ببینید.</p>
          <RouterLink to="/courses" class="btn btn-secondary">ثبت‌نام رایگان</RouterLink>
        </div>
        <div class="slide">
          <h1>اساتید مجرب بین‌المللی</h1>
          <p>همراه با متد روز دنیا، برای نتیجه‌ی واقعی!</p>
          <RouterLink to="/teachers" class="btn btn-outline">مشاهده اساتید</RouterLink>
        </div>
      </div>
    </section>

    <!-- Featured Courses -->
    <section class="featured-courses">
      <h2>دوره‌های ویژه</h2>
      <div class="course-grid">
        <CourseCard
          v-for="course in featuredCourses"
          :key="course.id"
          :course="course"
          featured
        />
        <p v-if="!featuredCourses.length">هنوز دوره ویژه‌ای ثبت نشده است.</p>
      </div>
    </section>

    <!-- Latest Courses -->
    <section class="latest-courses">
      <h2>جدیدترین دوره‌ها</h2>
      <div class="course-grid">
        <CourseCard
          v-for="course in latestCourses"
          :key="course.id"
          :course="course"
        />
        <p v-if="!latestCourses.length">هنوز دوره‌ای ثبت نشده است.</p>
      </div>
    </section>

    <!-- Categories -->
    <section class="course-categories">
      <h2>دسته‌بندی دوره‌ها</h2>
      <div class="category-grid">
        <CategoryCard
          v-for="category in categories"
          :key="category.id"
          :category="category"
        />
        <p v-if="!categories.length">هنوز دسته‌بندی‌ای ثبت نشده است.</p>
      </div>
    </section>

    <!-- Course Guide -->
    <section class="course-guide" v-if="courseGuide">
      <h2>{{ courseGuide.title }}</h2>
      <p v-if="courseGuide.description">{{ courseGuide.description }}</p>
      <ul>
        <li
          v-for="(item, index) in courseGuide.items"
          :key="index"
          v-if="item.is_active"
        >
          {{ item.text }}
        </li>
      </ul>
    </section>

    <!-- Teachers -->
    <section class="teachers">
      <h2>اساتید ما</h2>
      <div class="teacher-list">
        <TeacherCard
          v-for="teacher in teachers"
          :key="teacher.id"
          :teacher="teacher"
        />
        <p v-if="!teachers.length">فعلاً استادی فعال نیست.</p>
      </div>
    </section>

    <!-- FAQs -->
    <section class="fraq">
      <h2>سوالات متداول</h2>
      <div class="fraq-list">
        <FaqItem
          v-for="faq in faqs"
          :key="faq.id"
          :faq="faq"
        />
        <p v-if="!faqs.length">هیچ سوالی ثبت نشده است.</p>
      </div>
    </section>
  </div>
</template>

