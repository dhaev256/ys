from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from scheduler.models import Profile

class TeacherManagementTests(TestCase):
    def setUp(self):
        # Create an admin user
        self.admin_user = User.objects.create_user(username='admin_user', password='password123')
        Profile.objects.filter(user=self.admin_user).update(role='admin')
        
        # Create a teacher user
        self.teacher_user = User.objects.create_user(username='teacher_user', password='password123')
        Profile.objects.filter(user=self.teacher_user).update(role='teacher')

    def test_teacher_list_view_as_admin(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.get(reverse('teacher_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'scheduler/teacher_list.html')
        self.assertContains(response, 'teacher_user')

    def test_teacher_list_view_as_teacher_denied(self):
        self.client.login(username='teacher_user', password='password123')
        response = self.client.get(reverse('teacher_list'))
        # user_passes_test redirects to login_url='home' with next query param
        self.assertRedirects(response, reverse('home') + '?next=%2Fteachers%2F', target_status_code=302)

    def test_teacher_create_as_admin(self):
        self.client.login(username='admin_user', password='password123')
        response = self.client.post(reverse('teacher_create'), {
            'username': 'new_teacher',
            'first_name': 'New',
            'last_name': 'Teacher',
            'email': 'new@school.com',
            'role': 'teacher',
        })
        # Should redirect to the success view
        self.assertRedirects(response, reverse('teacher_creation_success'))
        
        # Verify user creation in DB
        new_user = User.objects.get(username='new_teacher')
        self.assertEqual(new_user.email, 'new@school.com')
        self.assertEqual(new_user.profile.role, 'teacher')

    def test_teacher_creation_success_view_clears_session(self):
        self.client.login(username='admin_user', password='password123')
        # Manually set the session data
        session = self.client.session
        session['created_teacher'] = {
            'username': 'test_temp',
            'password': 'TempPassword123',
            'role': 'Teacher',
            'name': 'Test Temp'
        }
        session.save()

        response = self.client.get(reverse('teacher_creation_success'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_temp')
        self.assertContains(response, 'TempPassword123')

        # Subsequent requests should redirect back to teacher list
        response_again = self.client.get(reverse('teacher_creation_success'))
        self.assertRedirects(response_again, reverse('teacher_list'))

    def test_teacher_delete_as_admin(self):
        self.client.login(username='admin_user', password='password123')
        target_user = User.objects.create_user(username='delete_me', password='password123')
        
        # Access confirm delete page
        response = self.client.get(reverse('teacher_delete', kwargs={'pk': target_user.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Perform deletion
        response_delete = self.client.post(reverse('teacher_delete', kwargs={'pk': target_user.pk}))
        self.assertRedirects(response_delete, reverse('teacher_list'))
        
        # Check database
        self.assertFalse(User.objects.filter(username='delete_me').exists())

    def test_change_password(self):
        self.client.login(username='teacher_user', password='password123')
        
        # Access change password page
        response = self.client.get(reverse('change_password'))
        self.assertEqual(response.status_code, 200)
        
        # Change the password
        response_change = self.client.post(reverse('change_password'), {
            'old_password': 'password123',
            'new_password1': 'newsecurepass123',
            'new_password2': 'newsecurepass123',
        })
        self.assertRedirects(response_change, reverse('home'), target_status_code=302)
        
        # Verify the new password works
        self.client.logout()
        login_success = self.client.login(username='teacher_user', password='newsecurepass123')
        self.assertTrue(login_success)
