"""
Unit tests for account views
"""
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from account.models import Student
from unittest.mock import patch

User = get_user_model()


class TestUserRegistrationView(TestCase):
    """Test cases for user registration"""
    
    def setUp(self):
        self.client = Client()
        self.registration_url = reverse('account:register')
        self.valid_data = {
            'email': 'newuser@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password1': 'complexpassword123',
            'password2': 'complexpassword123',
            'user_type': 'student'
        }
    
    def test_registration_view_get(self):
        """Test GET request to registration view"""
        response = self.client.get(self.registration_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ثبت‌نام')
        self.assertContains(response, 'email')
        self.assertContains(response, 'password1')
        self.assertContains(response, 'password2')
    
    def test_registration_view_post_valid(self):
        """Test POST request with valid data"""
        response = self.client.post(self.registration_url, self.valid_data)
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # User should be created
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())
        user = User.objects.get(email='newuser@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(user.user_type, 'student')
        self.assertFalse(user.is_active)  # Should be inactive until verified
    
    def test_registration_view_post_invalid_passwords(self):
        """Test POST request with mismatched passwords"""
        data = self.valid_data.copy()
        data['password2'] = 'differentpassword'
        
        response = self.client.post(self.registration_url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2', 'Passwords don\'t match.')
        
        # User should not be created
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())
    
    def test_registration_view_post_existing_email(self):
        """Test POST request with existing email"""
        # Create user first
        User.objects.create_user(email='newuser@example.com', password='pass123')
        
        response = self.client.post(self.registration_url, self.valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 'User with this email already exists.')
    
    def test_registration_sends_verification_email(self):
        """Test that registration sends verification email"""
        response = self.client.post(self.registration_url, self.valid_data)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('تأیید ایمیل', mail.outbox[0].subject)
        self.assertIn('newuser@example.com', mail.outbox[0].to)


class TestUserLoginView(TestCase):
    """Test cases for user login"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('account:login')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            is_active=True
        )
    
    def test_login_view_get(self):
        """Test GET request to login view"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ورود')
        self.assertContains(response, 'email')
        self.assertContains(response, 'password')
    
    def test_login_view_post_valid(self):
        """Test POST request with valid credentials"""
        data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        
        # User should be logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_view_post_invalid(self):
        """Test POST request with invalid credentials"""
        data = {
            'email': 'testuser@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ایمیل یا رمز عبور اشتباه است')
        
        # User should not be logged in
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_view_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        data = {
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'حساب کاربری شما فعال نیست')
    
    def test_login_redirect_authenticated_user(self):
        """Test that authenticated users are redirected from login page"""
        self.client.force_login(self.user)
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 302)


class TestUserLogoutView(TestCase):
    """Test cases for user logout"""
    
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('account:logout')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
    
    def test_logout_view(self):
        """Test logout functionality"""
        # Login first
        self.client.force_login(self.user)
        
        # Then logout
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 302)
        
        # Check user is logged out
        response = self.client.get(reverse('account:profile'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login


class TestProfileView(TestCase):
    """Test cases for user profile view"""
    
    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('account:profile')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.student = Student.objects.create(
            user=self.user,
            phone_number='09123456789',
            age=25
        )
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'testuser@example.com')
        self.assertContains(response, '09123456789')
    
    def test_profile_view_unauthenticated(self):
        """Test profile view for unauthenticated user"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'{reverse("account:login")}?next={self.profile_url}')
    
    def test_profile_view_student_specific_content(self):
        """Test profile view shows student-specific content"""
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)
        
        self.assertContains(response, 'دوره‌های من')
        self.assertContains(response, 'وضعیت ثبت‌نام')


class TestProfileUpdateView(TestCase):
    """Test cases for profile update view"""
    
    def setUp(self):
        self.client = Client()
        self.update_url = reverse('account:profile_update')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123'
        )
        self.student = Student.objects.create(
            user=self.user,
            phone_number='09123456789',
            age=25
        )
    
    def test_profile_update_view_get(self):
        """Test GET request to profile update view"""
        self.client.force_login(self.user)
        response = self.client.get(self.update_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ویرایش پروفایل')
        # Check form is pre-populated
        self.assertContains(response, 'testuser@example.com')
        self.assertContains(response, '09123456789')
    
    def test_profile_update_view_post_valid(self):
        """Test POST request with valid data"""
        self.client.force_login(self.user)
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone_number': '09987654321',
            'age': 30,
            'education_level': 'master',
            'learning_goal': 'academic'
        }
        response = self.client.post(self.update_url, data)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        
        # Check data was updated
        self.user.refresh_from_db()
        self.student.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Jane')
        self.assertEqual(self.user.last_name, 'Smith')
        self.assertEqual(self.student.phone_number, '09987654321')
        self.assertEqual(self.student.age, 30)
    
    def test_profile_update_view_unauthenticated(self):
        """Test profile update view for unauthenticated user"""
        response = self.client.get(self.update_url)
        self.assertEqual(response.status_code, 302)


class TestPasswordChangeView(TestCase):
    """Test cases for password change view"""
    
    def setUp(self):
        self.client = Client()
        self.password_change_url = reverse('account:password_change')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='oldpassword123'
        )
    
    def test_password_change_view_get(self):
        """Test GET request to password change view"""
        self.client.force_login(self.user)
        response = self.client.get(self.password_change_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تغییر رمز عبور')
        self.assertContains(response, 'old_password')
        self.assertContains(response, 'new_password1')
        self.assertContains(response, 'new_password2')
    
    def test_password_change_view_post_valid(self):
        """Test POST request with valid data"""
        self.client.force_login(self.user)
        data = {
            'old_password': 'oldpassword123',
            'new_password1': 'newpassword456',
            'new_password2': 'newpassword456'
        }
        response = self.client.post(self.password_change_url, data)
        
        # Should redirect after successful change
        self.assertEqual(response.status_code, 302)
        
        # Check password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword456'))
    
    def test_password_change_view_invalid_old_password(self):
        """Test POST request with invalid old password"""
        self.client.force_login(self.user)
        data = {
            'old_password': 'wrongpassword',
            'new_password1': 'newpassword456',
            'new_password2': 'newpassword456'
        }
        response = self.client.post(self.password_change_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'old_password', 'Your old password was entered incorrectly.')


class TestPasswordResetView(TestCase):
    """Test cases for password reset views"""
    
    def setUp(self):
        self.client = Client()
        self.password_reset_url = reverse('account:password_reset')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            is_active=True
        )
    
    def test_password_reset_view_get(self):
        """Test GET request to password reset view"""
        response = self.client.get(self.password_reset_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'بازیابی رمز عبور')
        self.assertContains(response, 'email')
    
    def test_password_reset_view_post_valid(self):
        """Test POST request with valid email"""
        data = {'email': 'testuser@example.com'}
        response = self.client.post(self.password_reset_url, data)
        
        # Should redirect to done page
        self.assertEqual(response.status_code, 302)
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('بازیابی رمز عبور', mail.outbox[0].subject)
    
    def test_password_reset_view_post_invalid_email(self):
        """Test POST request with invalid email"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.password_reset_url, data)
        
        # Should still redirect (for security)
        self.assertEqual(response.status_code, 302)
        
        # But no email should be sent
        self.assertEqual(len(mail.outbox), 0)


@pytest.mark.django_db
class TestAccountViewsPytest:
    """Pytest-style tests for account views"""
    
    def test_registration_view_with_client(self, client):
        """Test registration view using pytest client"""
        url = reverse('account:register')
        response = client.get(url)
        assert response.status_code == 200
        assert 'ثبت‌نام' in response.content.decode()
    
    def test_login_view_with_fixtures(self, client, student_user):
        """Test login view with user fixture"""
        url = reverse('account:login')
        data = {
            'email': student_user.email,
            'password': 'testpass123'
        }
        response = client.post(url, data)
        assert response.status_code == 302
    
    def test_profile_view_authenticated(self, authenticated_client, student_profile):
        """Test profile view with authenticated client"""
        url = reverse('account:profile')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert student_profile.user.email in response.content.decode()
    
    def test_profile_update_workflow(self, authenticated_client, student_profile):
        """Test complete profile update workflow"""
        url = reverse('account:profile_update')
        
        # GET form
        response = authenticated_client.get(url)
        assert response.status_code == 200
        
        # POST update
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'phone_number': '09111111111',
            'age': 30,
            'education_level': 'master',
            'learning_goal': 'academic'
        }
        response = authenticated_client.post(url, data)
        assert response.status_code == 302
        
        # Verify update
        student_profile.user.refresh_from_db()
        assert student_profile.user.first_name == 'Updated' 