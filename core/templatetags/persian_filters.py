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

