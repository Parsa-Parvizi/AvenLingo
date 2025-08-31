from django.conf import settings
from .models import (
    SiteSettings, FooterSection, SocialMedia, ContactInfo, 
    CompanyInfo, HeroSlider, Testimonial
)


def site_data(request):
    """
    Ultra-optimized context processor with minimal database queries
    """
    context = {}
    
    try:
        # Company/Academy Information - Basic query
        company_info = CompanyInfo.objects.first()
        
        if company_info:
            context['company_info'] = company_info
        else:
            # Fallback if no CompanyInfo exists
            context['company_info'] = {
                'company_name': 'آکادمی زبان انگلیسی',
                'slogan': 'بهترین آموزش زبان انگلیسی',
                'main_phone': '021-12345678',
                'main_email': 'info@academy.com',
                'address': 'تهران، ایران',
                'about_summary': 'آکادمی زبان انگلیسی با سال‌ها تجربه در خدمت شماست',
                'copyright_text': 'تمامی حقوق محفوظ است'
            }
        
        # Site Settings - Single query
        site_settings = SiteSettings.objects.first()
        context['site_settings'] = site_settings
        
        # Footer Data - Basic query
        footer_sections = list(FooterSection.objects.filter(is_active=True)
            .prefetch_related('links')
            .order_by('order'))
        context['footer_sections'] = footer_sections
        
        # Social Media Links - Basic query
        social_media = list(SocialMedia.objects.filter(is_active=True)
            .order_by('order'))
        context['social_media'] = social_media
        
        # Contact Information - Basic query
        contact_info = list(ContactInfo.objects.filter(is_active=True)
            .order_by('order'))
        context['contact_info'] = contact_info
            
        # Hero Sliders for Home Page - Basic query
        hero_sliders = list(HeroSlider.objects.filter(is_active=True)
            .order_by('order')[:5])
        context['hero_sliders'] = hero_sliders
            
        # Featured Testimonials - Basic query
        featured_testimonials = list(Testimonial.objects.filter(
            is_active=True, 
            is_featured=True
        ).order_by('-created_at')[:3])
        context['featured_testimonials'] = featured_testimonials
        
    except Exception as e:
        # Log error but don't break the site
        if settings.DEBUG:
            print(f"Context processor error: {e}")
        context = {
            'company_info': None,
            'site_settings': None,
            'footer_sections': [],
            'social_media': [],
            'contact_info': [],
            'hero_sliders': [],
            'featured_testimonials': []
        }
    
    return context


def footer_data(request):
    """
    Specific context processor for footer data
    Maintained for backward compatibility
    """
    
    context = {}
    
    try:
        # Footer sections with their links
        footer_sections = FooterSection.objects.filter(is_active=True).prefetch_related(
            'links__is_active'
        ).order_by('order')
        
        # Organize sections by type for easier template access
        footer_data = {}
        for section in footer_sections:
            active_links = section.links.filter(is_active=True).order_by('order')
            footer_data[section.section_type] = {
                'title': section.title,
                'links': active_links
            }
        
        context['footer_data'] = footer_data
        
        # Social media links
        social_links = SocialMedia.objects.filter(is_active=True).order_by('order')
        context['social_links'] = social_links
        
        # Contact information
        contact_items = ContactInfo.objects.filter(is_active=True).order_by('order')
        contact_data = {}
        for item in contact_items:
            contact_data[item.contact_type] = {
                'title': item.title,
                'value': item.value,
                'icon': item.icon
            }
        context['contact_data'] = contact_data
        
    except Exception as e:
        if settings.DEBUG:
            print(f"Footer context processor error: {e}")
        context = {
            'footer_data': {},
            'social_links': [],
            'contact_data': {}
        }
    
    return context


def clear_site_cache():
    """
    Utility function to clear site cache when admin makes changes
    Call this in model save methods or admin admin actions
    (Note: No caching is used anymore, this function is kept for compatibility)
    """
    pass

def external_urls(request):
    """Context processor to provide external URLs to templates"""
    return {
        'EXTERNAL_URLS': getattr(settings, 'EXTERNAL_URLS', {}),
        'CDN_URLS': {
            'FONT_AWESOME': getattr(settings, 'EXTERNAL_URLS', {}).get('FONT_AWESOME_CDN', ''),
            'DARKMODE_JS': getattr(settings, 'EXTERNAL_URLS', {}).get('DARKMODE_JS_CDN', ''),
        }
    }

def url_security_settings(request):
    """Context processor to provide URL security settings to templates"""
    return {
        'URL_SECURITY': getattr(settings, 'URL_SECURITY', {}),
        'URL_VALIDATION': getattr(settings, 'URL_VALIDATION', {}),
    } 