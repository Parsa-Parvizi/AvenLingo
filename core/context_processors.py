from django.core.cache import cache
from django.conf import settings
from .models import (
    SiteSettings, FooterSection, SocialMedia, ContactInfo, 
    CompanyInfo, HeroSlider, Testimonial
)


def site_data(request):
    """
    Context processor that provides site-wide data for templates
    Caches data for 1 hour to improve performance
    """
    
    # Check cache first
    cache_key = 'site_context_data'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
    context = {}
    
    try:
        # Company/Academy Information (Always available)
        try:
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
        except Exception:
            context['company_info'] = None
        
        # Site Settings (Technical settings)
        try:
            site_settings = SiteSettings.objects.first()
            context['site_settings'] = site_settings
        except Exception:
            context['site_settings'] = None
        
        # Footer Data
        try:
            footer_sections = FooterSection.objects.filter(is_active=True).prefetch_related('links').order_by('order')
            context['footer_sections'] = footer_sections
        except Exception:
            context['footer_sections'] = []
        
        # Social Media Links
        try:
            social_media = SocialMedia.objects.filter(is_active=True).order_by('order')
            context['social_media'] = social_media
        except Exception:
            context['social_media'] = []
        
        # Contact Information
        try:
            contact_info = ContactInfo.objects.filter(is_active=True).order_by('order')
            context['contact_info'] = contact_info
        except Exception:
            context['contact_info'] = []
            
        # Hero Sliders for Home Page
        try:
            hero_sliders = HeroSlider.objects.filter(is_active=True).order_by('order')[:5]
            context['hero_sliders'] = hero_sliders
        except Exception:
            context['hero_sliders'] = []
            
        # Featured Testimonials
        try:
            featured_testimonials = Testimonial.objects.filter(
                is_active=True, 
                is_featured=True
            ).order_by('-created_at')[:3]
            context['featured_testimonials'] = featured_testimonials
        except Exception:
            context['featured_testimonials'] = []
        
        # Cache the data for 1 hour
        cache.set(cache_key, context, 3600)
        
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
    
    cache_key = 'footer_context_data'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
    
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
        
        # Cache for 2 hours
        cache.set(cache_key, context, 7200)
        
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
    Call this in model save methods or admin actions
    """
    cache.delete('site_context_data')
    cache.delete('footer_context_data') 