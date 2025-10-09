from django import template
from datetime import datetime, date

# تلاش برای import کردن jdatetime
try:
    import jdatetime
    JDATETIME_AVAILABLE = True
except ImportError:
    JDATETIME_AVAILABLE = False

register = template.Library()


@register.filter(name='persian_numbers')
def persian_numbers(value):
    """
    تبدیل اعداد انگلیسی به فارسی
    """
    if value is None:
        return value
    
    # نقشه تبدیل اعداد
    english_to_persian = {
        '0': '۰',
        '1': '۱',
        '2': '۲',
        '3': '۳',
        '4': '۴',
        '5': '۵',
        '6': '۶',
        '7': '۷',
        '8': '۸',
        '9': '۹',
    }
    
    # تبدیل به رشته
    value_str = str(value)
    
    # جایگزینی هر عدد
    for english, persian in english_to_persian.items():
        value_str = value_str.replace(english, persian)
    
    return value_str


@register.filter(name='persianize')
def persianize(value):
    """
    تبدیل اعداد و کاراکترهای خاص به فارسی
    """
    return persian_numbers(value)


@register.filter(name='jalali_date')
def jalali_date(value, format_string='%Y/%m/%d'):
    """
    تبدیل تاریخ میلادی به شمسی (جلالی)
    
    استفاده:
    {{ date_value|jalali_date }}  -> 1403/07/15
    {{ date_value|jalali_date:"%d %B %Y" }}  -> 15 مهر 1403
    {{ datetime_value|jalali_date:"%Y/%m/%d - %H:%M" }}  -> 1403/07/15 - 14:30
    """
    if value is None:
        return ''
    
    # اگر jdatetime موجود نیست، تاریخ میلادی را با اعداد فارسی برگردان
    if not JDATETIME_AVAILABLE:
        if isinstance(value, (datetime, date)):
            return persian_numbers(value.strftime(format_string.replace('%B', '%m')))
        return persian_numbers(str(value))
    
    try:
        # اگر datetime است
        if isinstance(value, datetime):
            jalali = jdatetime.datetime.fromgregorian(datetime=value)
        # اگر date است
        elif isinstance(value, date):
            jalali = jdatetime.date.fromgregorian(date=value)
        else:
            return persian_numbers(str(value))
        
        # فرمت کردن تاریخ
        formatted = jalali.strftime(format_string)
        
        # تبدیل نام ماه‌ها به فارسی
        month_names = {
            'Farvardin': 'فروردین',
            'Ordibehesht': 'اردیبهشت',
            'Khordad': 'خرداد',
            'Tir': 'تیر',
            'Mordad': 'مرداد',
            'Shahrivar': 'شهریور',
            'Mehr': 'مهر',
            'Aban': 'آبان',
            'Azar': 'آذر',
            'Dey': 'دی',
            'Bahman': 'بهمن',
            'Esfand': 'اسفند',
        }
        
        for eng, per in month_names.items():
            formatted = formatted.replace(eng, per)
        
        # تبدیل اعداد به فارسی
        formatted = persian_numbers(formatted)
        
        return formatted
    except Exception as e:
        # در صورت بروز خطا، تاریخ میلادی را با اعداد فارسی برگردان
        if isinstance(value, (datetime, date)):
            return persian_numbers(value.strftime(format_string.replace('%B', '%m')))
        return persian_numbers(str(value))


@register.filter(name='jalali_datetime')
def jalali_datetime(value, format_string='%Y/%m/%d - %H:%M'):
    """
    تبدیل datetime میلادی به شمسی با ساعت
    
    استفاده:
    {{ datetime_value|jalali_datetime }}  -> 1403/07/15 - 14:30
    {{ datetime_value|jalali_datetime:"%d %B %Y ساعت %H:%M" }}
    """
    return jalali_date(value, format_string)


@register.filter(name='jalali_short')
def jalali_short(value):
    """
    نمایش کوتاه تاریخ شمسی
    
    استفاده:
    {{ date_value|jalali_short }}  -> 1403/07/15
    """
    return jalali_date(value, '%Y/%m/%d')


@register.filter(name='jalali_long')
def jalali_long(value):
    """
    نمایش کامل تاریخ شمسی
    
    استفاده:
    {{ date_value|jalali_long }}  -> 15 مهر 1403
    """
    return jalali_date(value, '%d %B %Y')


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    دریافت مقدار از dictionary با key
    
    استفاده:
    {{ my_dict|get_item:key_variable }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='format_class_time')
def format_class_time(value):
    """
    فرمت کردن زمان کلاس به شکل زیبا
    
    ورودی: دوشنبه-پنج‌شنبه ۱۰:۰۰-۱۱:۳۰ ساعت
    خروجی: دوشنبه و پنج‌شنبه ساعت: ۱۰:۰۰ تا ۱۱:۳۰
    """
    if not value:
        return value
    
    # تبدیل به رشته
    text = str(value).strip()
    
    # جایگزینی - بین روزها با "و"
    # ابتدا زمان را جدا می‌کنیم
    import re
    
    # الگوی زمان: HH:MM-HH:MM یا HH:MM - HH:MM
    time_pattern = r'(\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})'
    time_match = re.search(time_pattern, text)
    
    if time_match:
        start_time = time_match.group(1)
        end_time = time_match.group(2)
        
        # حذف قسمت زمان از متن اصلی
        days_part = text[:time_match.start()].strip()
        
        # جایگزینی - با "و" در قسمت روزها
        days_part = days_part.replace('-', ' و ')
        
        # ساخت فرمت جدید
        formatted = f"{days_part} ساعت: {start_time} تا {end_time}"
        
        # تبدیل اعداد به فارسی
        formatted = persian_numbers(formatted)
        
        return formatted
    
    # اگر الگوی زمان پیدا نشد، فقط - را با "و" جایگزین می‌کنیم
    text = text.replace('-', ' و ')
    text = text.replace('ساعت', 'ساعت:')
    
    return persian_numbers(text)

