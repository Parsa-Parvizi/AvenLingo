/**
 * Persian DatePicker Initialization
 * تنظیمات و راه‌اندازی Date Picker شمسی
 */

document.addEventListener('DOMContentLoaded', function() {
    // پیدا کردن همه input های تاریخ
    const dateInputs = document.querySelectorAll('input[type="date"], input.persian-date');
    const dateTimeInputs = document.querySelectorAll('input[type="datetime-local"], input.persian-datetime');
    
    // تنظیمات پایه تقویم شمسی
    const persianConfig = {
        calendar: {
            persian: {
                locale: 'fa',
                showHint: true,
                leapYearMode: 'algorithmic'
            }
        },
        navigator: {
            enabled: true,
            scroll: {
                enabled: true
            },
            text: {
                btnNextText: '>',
                btnPrevText: '<'
            }
        },
        toolbox: {
            enabled: true,
            calendarSwitch: {
                enabled: false
            },
            todayButton: {
                enabled: true,
                text: {
                    fa: 'امروز'
                }
            },
            submitButton: {
                enabled: true,
                text: {
                    fa: 'انتخاب'
                }
            }
        },
        timePicker: {
            enabled: false,
            meridian: {
                enabled: false
            }
        },
        dayPicker: {
            enabled: true,
            titleFormat: 'YYYY MMMM'
        },
        responsive: true
    };
    
    // تبدیل date inputs به Persian DatePicker
    dateInputs.forEach(function(input) {
        // تغییر type به text
        input.setAttribute('type', 'text');
        input.setAttribute('placeholder', 'روز/ماه/سال');
        input.setAttribute('autocomplete', 'off');
        input.classList.add('persian-datepicker-input');
        
        // اگر کتابخانه persian-datepicker لود شده باشد
        if (typeof $.fn.persianDatepicker !== 'undefined') {
            $(input).persianDatepicker(persianConfig);
        }
    });
    
    // تبدیل datetime inputs به Persian DatePicker با ساعت
    dateTimeInputs.forEach(function(input) {
        input.setAttribute('type', 'text');
        input.setAttribute('placeholder', 'روز/ماه/سال ساعت:دقیقه');
        input.setAttribute('autocomplete', 'off');
        input.classList.add('persian-datepicker-input');
        
        if (typeof $.fn.persianDatepicker !== 'undefined') {
            const dateTimeConfig = {
                ...persianConfig,
                timePicker: {
                    enabled: true,
                    meridian: {
                        enabled: false
                    }
                },
                altField: input.getAttribute('data-alt-field') || '',
                altFormat: 'YYYY-MM-DD HH:mm:ss',
                format: 'YYYY/MM/DD HH:mm'
            };
            
            $(input).persianDatepicker(dateTimeConfig);
        }
    });
});
