<template>
  <div lang="fa" dir="rtl">
    <Navbar />

    <main class="content">
      <router-view />
    </main>

    <Footer />
  </div>
</template>

<script setup>
import Navbar from '@/components/layout/Navbar.vue'
import Footer from '@/components/layout/Footer.vue'
</script>

<style>
@import '@/assets/css/navbar.css';
@import '@/assets/css/main.css';
@import '@/assets/css/slide.css';
@import '@/assets/css/login.css';
@import '@/assets/css/footer.css';
@import '@/assets/css/search.css';
@import '@/assets/css/teacher.css';
@import '@/assets/css/course.css';
@import '@/assets/css/mobile.css';
@import '@/assets/css/fonts.css';

@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');
</style>

<script>
import Darkmode from 'darkmode-js'

export default {
  mounted() {
    const options = {
      bottom: 'unset',
      right: 'unset',
      left: 'unset',
      time: '0.4s',
      label: '',
      autoMatchOsTheme: true,
      saveInCookies: true
    }
    const darkmode = new Darkmode(options)
    window.toggleDarkMode = () => darkmode.toggle()
  }
}
</script>