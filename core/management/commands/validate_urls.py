from django.core.management.base import BaseCommand
from django.conf import settings
from core.utils import url_validator, validate_social_media_url
from account.models import AuthSystemSettings
from contact.models import ContactUs
from core.models import SiteSettings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Validate all URLs in the database for security and accessibility'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix invalid URLs by using defaults from settings',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed validation results',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Starting URL validation...')
        )
        
        fix_urls = options['fix']
        verbose = options['verbose']
        
        # Validate URLs in different models
        self.validate_auth_settings(fix_urls, verbose)
        self.validate_contact_settings(fix_urls, verbose)
        self.validate_site_settings(fix_urls, verbose)
        
        self.stdout.write(
            self.style.SUCCESS('✅ URL validation completed!')
        )
    
    def validate_auth_settings(self, fix_urls, verbose):
        """Validate URLs in authentication settings"""
        self.stdout.write('\n🔐 Validating authentication settings...')
        
        try:
            auth_settings = AuthSystemSettings.objects.first()
            if not auth_settings:
                self.stdout.write(self.style.WARNING('No authentication settings found'))
                return
            
            # Validate Instagram URL
            if auth_settings.instagram_url:
                result = validate_social_media_url(auth_settings.instagram_url, 'instagram')
                if not result['valid']:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Invalid Instagram URL: {auth_settings.instagram_url}')
                    )
                    if fix_urls:
                        auth_settings.instagram_url = ''
                        auth_settings.save()
                        self.stdout.write(self.style.SUCCESS('✅ Fixed Instagram URL'))
                elif verbose:
                    self.stdout.write(f'✅ Instagram URL: {auth_settings.instagram_url}')
            
            # Validate Telegram URL
            if auth_settings.telegram_url:
                result = validate_social_media_url(auth_settings.telegram_url, 'telegram')
                if not result['valid']:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Invalid Telegram URL: {auth_settings.telegram_url}')
                    )
                    if fix_urls:
                        auth_settings.telegram_url = ''
                        auth_settings.save()
                        self.stdout.write(self.style.SUCCESS('✅ Fixed Telegram URL'))
                elif verbose:
                    self.stdout.write(f'✅ Telegram URL: {auth_settings.telegram_url}')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error validating auth settings: {e}')
            )
    
    def validate_contact_settings(self, fix_urls, verbose):
        """Validate URLs in contact settings"""
        self.stdout.write('\n📞 Validating contact settings...')
        
        try:
            contact_settings = ContactUs.objects.first()
            if not contact_settings:
                self.stdout.write(self.style.WARNING('No contact settings found'))
                return
            
            # Validate social media URLs
            social_platforms = [
                ('instagram', 'Instagram'),
                ('telegram', 'Telegram'),
                ('linkedin', 'LinkedIn'),
                ('youtube', 'YouTube'),
            ]
            
            for field_name, display_name in social_platforms:
                url_value = getattr(contact_settings, field_name, None)
                if url_value:
                    result = validate_social_media_url(url_value, field_name)
                    if not result['valid']:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Invalid {display_name} URL: {url_value}')
                        )
                        if fix_urls:
                            setattr(contact_settings, field_name, '')
                            self.stdout.write(self.style.SUCCESS(f'✅ Fixed {display_name} URL'))
                    elif verbose:
                        self.stdout.write(f'✅ {display_name} URL: {url_value}')
            
            if fix_urls:
                contact_settings.save()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error validating contact settings: {e}')
            )
    
    def validate_site_settings(self, fix_urls, verbose):
        """Validate URLs in site settings"""
        self.stdout.write('\n🌐 Validating site settings...')
        
        try:
            site_settings = SiteSettings.objects.first()
            if not site_settings:
                self.stdout.write(self.style.WARNING('No site settings found'))
                return
            
            # Validate developer link
            if site_settings.developer_link:
                result = url_validator.validate_url(site_settings.developer_link)
                if not result['valid']:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Invalid developer link: {site_settings.developer_link}')
                    )
                    if fix_urls:
                        site_settings.developer_link = ''
                        site_settings.save()
                        self.stdout.write(self.style.SUCCESS('✅ Fixed developer link'))
                elif verbose:
                    self.stdout.write(f'✅ Developer link: {site_settings.developer_link}')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error validating site settings: {e}')
            )
    
    def validate_external_urls(self):
        """Validate external URLs from settings"""
        self.stdout.write('\n🔗 Validating external URLs from settings...')
        
        external_urls = getattr(settings, 'EXTERNAL_URLS', {})
        
        for key, url in external_urls.items():
            if url and isinstance(url, str) and url.startswith('http'):
                result = url_validator.validate_url(url)
                if not result['valid']:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Invalid external URL {key}: {url}')
                    )
                else:
                    self.stdout.write(f'✅ External URL {key}: {url}')
    
    def show_validation_summary(self):
        """Show summary of validation results"""
        self.stdout.write('\n📊 Validation Summary:')
        self.stdout.write('=' * 50)
        
        # This would be populated with actual results
        self.stdout.write('Total URLs checked: N/A')
        self.stdout.write('Valid URLs: N/A')
        self.stdout.write('Invalid URLs: N/A')
        self.stdout.write('Fixed URLs: N/A') 