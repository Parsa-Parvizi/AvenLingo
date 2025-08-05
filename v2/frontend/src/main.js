// استایل کلی پروژه
import './assets/css/main.css'

// ✔ اگر فایل‌های دیگه داری (navbar.css, fonts.css و غیره)، جدا جدا ایمپورت کن
import './assets/css/navbar.css'
import './assets/css/footer.css'
import './assets/css/fonts.css'
import './assets/css/teacher.css'
import './assets/css/course.css'
import './assets/css/mobile.css'
import './assets/css/search.css'
import './assets/css/slide.css'
import './assets/css/login.css'

// Vue core
import { createApp } from 'vue'
import { createPinia } from 'pinia'

// App.vue (همون معادل base.html)
import App from './App.vue'

// Vue Router برای مدیریت route ها
import router from './router'

// Darkmode.js اگر ازش استفاده می‌کنی
import Darkmode from 'darkmode-js'

const app = createApp(App)

// استفاده از Pinia (state management)
app.use(createPinia())

// استفاده از Router
app.use(router)

// فعال‌سازی darkmode
const darkmode = new Darkmode({
  bottom: 'unset',
  right: 'unset',
  left: 'unset',
  time: '0.4s',
  label: '',
  autoMatchOsTheme: true,
  saveInCookies: true
})
darkmode.showWidget() // می‌تونی این رو حذف کنی اگر خودت دکمه ساختی

// Mount app
app.mount('#app')
