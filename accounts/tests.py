from django.test import TestCase
from django.urls import reverse

from attendance.models import Attendance
from .models import User


class LoginAttendanceFlowTests(TestCase):
    def test_employee_login_does_not_auto_create_attendance(self):
        employee = User.objects.create_user(
            username='login-employee',
            email='login-employee@example.com',
            password='testpass123',
            role='EMPLOYEE',
        )

        response = self.client.post(
            reverse('login'),
            {'username': 'login-employee', 'password': 'testpass123'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Attendance.objects.filter(employee=employee).exists())
        self.assertContains(response, 'Use the Check In button on your dashboard to mark attendance.')
