function toggleMenu() {
    const menu = document.getElementById('navbarMenu');
    const hamburger = document.querySelector('.hamburger');
    menu.classList.toggle('active');
    hamburger.classList.toggle('active');
}

function toggleSearch() {
    const searchDropdown = document.getElementById('searchDropdown');
    const searchBtn = document.querySelector('.search-btn');
    
    searchDropdown.classList.toggle('active');
    
    if (searchDropdown.classList.contains('active')) {
        document.querySelector('.search-input').focus();
        document.addEventListener('click', closeSearchOnClickOutside);
    } else {
        document.removeEventListener('click', closeSearchOnClickOutside);
    }
}


function closeSearchOnClickOutside(event) {
    const searchContainer = document.querySelector('.search-container');
    const searchDropdown = document.getElementById('searchDropdown');
    
    if (!searchContainer.contains(event.target)) {
        searchDropdown.classList.remove('active');
        document.removeEventListener('click', closeSearchOnClickOutside);
    }
}

function toggleAnswer(btn) {
  const faqItem = btn.parentElement;
  const answer = btn.nextElementSibling;
  const isActive = faqItem.classList.contains('active');
  
  // Close all other FAQ items
  document.querySelectorAll('.faq-item').forEach(item => {
    if (item !== faqItem) {
      item.classList.remove('active');
      const otherAnswer = item.querySelector('.faq-answer');
      const otherBtn = item.querySelector('.faq-question');
      otherAnswer.classList.remove('active');
      otherBtn.classList.remove('active');
    }
  });
  
  // Toggle current FAQ item
  if (isActive) {
    faqItem.classList.remove('active');
    answer.classList.remove('active');
    btn.classList.remove('active');
  } else {
    faqItem.classList.add('active');
    answer.classList.add('active');
    btn.classList.add('active');
  }
}

// Slider functionality
function initSlider() {
  const slides = document.querySelectorAll(".slide");
  const dots = document.querySelectorAll(".dot");
  
  if (slides.length === 0) {
    console.log("No slides found");
    return;
  }
  
  let index = 0;
  
  // Show first slide
  slides[0].classList.add("active");
  if (dots.length > 0) {
    dots[0].classList.add("active");
  }
  
  function showSlide(newIndex) {
    // Remove active from current slide and dot
    slides[index].classList.remove("active");
    if (dots[index]) {
      dots[index].classList.remove("active");
    }
    
    // Update index
    index = newIndex;
    
    // Add active to new slide and dot
    slides[index].classList.add("active");
    if (dots[index]) {
      dots[index].classList.add("active");
    }
  }
  
  // Auto slide every 5 seconds
  setInterval(() => {
    showSlide((index + 1) % slides.length);
  }, 5000);
  
  // Add manual navigation
  const prevBtn = document.querySelector(".slider-prev");
  const nextBtn = document.querySelector(".slider-next");
  
  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      showSlide((index - 1 + slides.length) % slides.length);
    });
  }
  
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      showSlide((index + 1) % slides.length);
    });
  }
  
  // Add dot navigation
  dots.forEach((dot, dotIndex) => {
    dot.addEventListener("click", () => {
      showSlide(dotIndex);
    });
  });
}

// Search functionality
function initSearch() {
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const searchInput = this.querySelector('.search-input');
            const searchCourses = this.querySelector('input[name="search_courses"]').checked;
            const searchTeachers = this.querySelector('input[name="search_teachers"]').checked;
            
            if (!searchCourses && !searchTeachers) {
                alert('لطفاً حداقل یک گزینه جستجو را انتخاب کنید');
                return;
            }
            
            if (!searchInput.value.trim()) {
                alert('لطفاً عبارت جستجو را وارد کنید');
                return;
            }
            
            // Build search URL
            let searchUrl = '/search/?q=' + encodeURIComponent(searchInput.value.trim());
            if (searchCourses) searchUrl += '&search_courses=1';
            if (searchTeachers) searchUrl += '&search_teachers=1';
            
            window.location.href = searchUrl;
        });
    }
}

// Newsletter subscription
function initNewsletter() {
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = this.querySelector('input[type="email"]').value;
            if (!email) {
                alert('لطفاً ایمیل خود را وارد کنید');
                return;
            }
            
            // Here you would typically send the email to your backend
            alert('ثبت‌نام در خبرنامه با موفقیت انجام شد!');
            this.reset();
        });
    }
}

// FAQ functionality
function initFAQ() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        if (question) {
            // Add keyboard support
            question.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleAnswer(this);
                }
            });
        }
    });
}

// Initialize all functionality when DOM is loaded
document.addEventListener("DOMContentLoaded", function() {
  initSlider();
  initSearch();
  initNewsletter();
  initFAQ();
  
  // Close mobile menu when clicking on a link
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      const menu = document.getElementById('navbarMenu');
      const hamburger = document.querySelector('.hamburger');
      menu.classList.remove('active');
      hamburger.classList.remove('active');
    });
  });
  
  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
});

