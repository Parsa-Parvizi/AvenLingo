/**
 * Icon Replacer - جایگزینی خودکار آیکون‌های FontAwesome
 * این اسکریپت تمام آیکون‌های FontAwesome را با آیکون‌های سفارشی جایگزین می‌کند
 */

// نقشه تبدیل آیکون‌های FontAwesome به آیکون‌های سفارشی
const iconMap = {
    'fas fa-user': 'icon-user',
    'fas fa-user-tie': 'icon-user-tie',
    'fas fa-user-plus': 'icon-user-plus',
    'fas fa-user-edit': 'icon-user-edit',
    'fas fa-envelope': 'icon-envelope',
    'fas fa-phone': 'icon-phone',
    'fas fa-mobile-alt': 'icon-mobile',
    'fas fa-book': 'icon-book',
    'fas fa-book-open': 'icon-book-open',
    'fas fa-book-reader': 'icon-book-reader',
    'fas fa-graduation-cap': 'icon-graduation-cap',
    'fas fa-star': 'icon-star',
    'fas fa-clock': 'icon-clock',
    'fas fa-calendar': 'icon-calendar',
    'fas fa-calendar-alt': 'icon-calendar-alt',
    'fas fa-check-circle': 'icon-check-circle',
    'fas fa-times-circle': 'icon-times-circle',
    'fas fa-eye': 'icon-eye',
    'fas fa-edit': 'icon-edit',
    'fas fa-plus': 'icon-plus',
    'fas fa-plus-circle': 'icon-plus-circle',
    'fas fa-arrow-left': 'icon-arrow-left',
    'fas fa-arrow-right': 'icon-arrow-right',
    'fas fa-arrow-up': 'icon-arrow-up',
    'fas fa-home': 'icon-home',
    'fas fa-sign-out-alt': 'icon-sign-out',
    'fas fa-sign-in-alt': 'icon-sign-in',
    'fas fa-chart-line': 'icon-chart-line',
    'fas fa-chart-pie': 'icon-chart-pie',
    'fas fa-money-bill-wave': 'icon-money-bill-wave',
    'fas fa-bell': 'icon-bell',
    'fas fa-bell-slash': 'icon-bell-slash',
    'fas fa-search': 'icon-search',
    'fas fa-paper-plane': 'icon-paper-plane',
    'fas fa-spinner': 'icon-spinner',
    'fas fa-trophy': 'icon-trophy',
    'fas fa-users': 'icon-users',
    'fas fa-handshake': 'icon-handshake',
    'fas fa-lightbulb': 'icon-lightbulb',
    'fas fa-shield-alt': 'icon-shield',
    'fas fa-heart': 'icon-heart',
    'fas fa-comments': 'icon-comments',
    'fas fa-play-circle': 'icon-play-circle',
    'fas fa-certificate': 'icon-certificate',
    'fas fa-bolt': 'icon-bolt',
    'fas fa-list': 'icon-list',
    'fas fa-chevron-left': 'icon-chevron-left',
    'fas fa-chevron-right': 'icon-chevron-right',
    'fas fa-info-circle': 'icon-info-circle',
    'fas fa-exclamation-triangle': 'icon-exclamation-triangle',
    'fas fa-history': 'icon-history',
    'fas fa-chalkboard-teacher': 'icon-chalkboard-teacher',
    'fas fa-door-open': 'icon-door-open',
    'fas fa-save': 'icon-save',
    'fas fa-rocket': 'icon-rocket'
};

// تابع جایگزینی آیکون‌ها
function replaceIcons() {
    // پیدا کردن تمام عناصر i که کلاس‌های FontAwesome دارند
    const iconElements = document.querySelectorAll('i[class*="fas fa-"], i[class*="far fa-"], i[class*="fab fa-"]');
    
    iconElements.forEach(element => {
        const classList = Array.from(element.classList);
        let replaced = false;
        
        // بررسی هر کلاس برای پیدا کردن مطابقت
        for (const [faIcon, customIcon] of Object.entries(iconMap)) {
            const faClasses = faIcon.split(' ');
            const hasAllClasses = faClasses.every(cls => classList.includes(cls));
            
            if (hasAllClasses) {
                // حذف کلاس‌های FontAwesome
                faClasses.forEach(cls => element.classList.remove(cls));
                
                // اضافه کردن کلاس آیکون سفارشی
                element.classList.add(customIcon);
                
                // حفظ کلاس‌های اضافی (مثل رنگ، اندازه)
                const additionalClasses = classList.filter(cls => 
                    !cls.startsWith('fas') && 
                    !cls.startsWith('far') && 
                    !cls.startsWith('fab') && 
                    !cls.startsWith('fa-') &&
                    cls !== 'fa'
                );
                
                replaced = true;
                break;
            }
        }
        
        // اگر آیکون پیدا نشد، حداقل کلاس‌های FontAwesome را حذف کن
        if (!replaced) {
            element.classList.remove('fas', 'far', 'fab', 'fa');
            // اضافه کردن یک آیکون پیش‌فرض
            if (!element.classList.length || element.classList.contains('')) {
                element.classList.add('icon-user');
            }
        }
    });
}

// تابع جایگزینی آیکون‌های spinner در حال بارگذاری
function replaceSpinnerIcons() {
    const spinners = document.querySelectorAll('.fa-spin, .fas.fa-spinner');
    spinners.forEach(spinner => {
        spinner.className = 'icon-spinner';
    });
}

// اجرای جایگزینی پس از بارگذاری DOM
document.addEventListener('DOMContentLoaded', function() {
    replaceIcons();
    replaceSpinnerIcons();
});

// نظارت بر تغییرات DOM برای جایگزینی آیکون‌های جدید
if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver(function(mutations) {
        let shouldReplace = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        const hasIcons = node.querySelector && node.querySelector('i[class*="fas fa-"], i[class*="far fa-"], i[class*="fab fa-"]');
                        if (hasIcons || (node.tagName === 'I' && node.className.includes('fa'))) {
                            shouldReplace = true;
                        }
                    }
                });
            }
        });
        
        if (shouldReplace) {
            setTimeout(replaceIcons, 10); // کمی تاخیر برای اطمینان از رندر شدن
        }
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// تابع عمومی برای جایگزینی دستی
window.replaceIcons = replaceIcons;

// جایگزینی آیکون‌های موجود در محتوای AJAX
document.addEventListener('ajaxComplete', function() {
    replaceIcons();
});

// پشتیبانی از jQuery اگر موجود باشد
if (typeof $ !== 'undefined') {
    $(document).ajaxComplete(function() {
        replaceIcons();
    });
} 