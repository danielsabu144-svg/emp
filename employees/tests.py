from django.contrib.messages import get_messages
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from datetime import date, time

from accounts.models import User
from attendance.models import Attendance
from employees.models import EmployeeProfile
from leave_management.models import LeaveBalance, LeaveType, current_leave_year


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class EmployeeAdminDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.superadmin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123',
        )
        self.hr = User.objects.create_user(
            username='hr-admin',
            email='hr-admin@example.com',
            password='testpass123',
            role='HR',
        )
        self.employee = User.objects.create_user(
            username='delete-me',
            email='delete-me@example.com',
            password='testpass123',
            role='EMPLOYEE',
        )
        EmployeeProfile.objects.create(
            user=self.employee,
            department='IT',
            designation='JUNIOR',
            gender='M',
            salary=25000,
        )

    def test_hr_can_delete_employee_profile(self):
        self.client.force_login(self.hr)

        response = self.client.post(reverse('delete_employee', args=[self.employee.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(id=self.employee.id).exists())
        self.assertFalse(EmployeeProfile.objects.filter(user_id=self.employee.id).exists())
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Employee profile for delete-me was deleted successfully.', messages)

    def test_hr_cannot_delete_own_account(self):
        self.client.force_login(self.hr)

        response = self.client.post(reverse('delete_employee', args=[self.hr.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(id=self.hr.id).exists())
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('You cannot delete your own account.', messages)

    def test_hr_cannot_delete_non_employee_account(self):
        other_hr = User.objects.create_user(
            username='other-hr',
            email='other-hr@example.com',
            password='testpass123',
            role='HR',
        )
        self.client.force_login(self.hr)

        response = self.client.post(reverse('delete_employee', args=[other_hr.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(id=other_hr.id).exists())
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Only employee accounts can be deleted from this dashboard.', messages)

    def test_delete_view_rejects_get_requests(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('delete_employee', args=[self.employee.id]))

        self.assertEqual(response.status_code, 405)

    def test_superadmin_can_delete_hr_account(self):
        other_hr = User.objects.create_user(
            username='delete-hr',
            email='delete-hr@example.com',
            password='testpass123',
            role='HR',
        )
        self.client.force_login(self.superadmin)

        response = self.client.post(reverse('delete_employee', args=[other_hr.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(id=other_hr.id).exists())

    def test_superadmin_sees_delete_button_for_hr_rows_but_not_self(self):
        other_hr = User.objects.create_user(
            username='visible-hr',
            email='visible-hr@example.com',
            password='testpass123',
            role='HR',
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse('employee_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('delete_employee', args=[self.employee.id]))
        self.assertContains(response, reverse('delete_employee', args=[other_hr.id]))
        self.assertNotContains(response, reverse('delete_employee', args=[self.superadmin.id]))


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class EmployeeDashboardLeaveBalanceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.leave_type, _ = LeaveType.objects.update_or_create(
            name='Casual Leave',
            defaults={
                'max_days_per_year': 12,
                'is_active': True,
            },
        )
        self.inactive_leave_type = LeaveType.objects.create(
            name='Sick Leave',
            max_days_per_year=10,
            is_active=True,
        )
        self.inactive_leave_type.refresh_from_db()
        self.employee = User.objects.create_user(
            username='dashboard-emp',
            email='dashboard-emp@example.com',
            password='testpass123',
            role='EMPLOYEE',
            first_name='Dash',
            last_name='Board',
        )
        EmployeeProfile.objects.create(
            user=self.employee,
            department='IT',
            designation='JUNIOR',
            gender='M',
            salary=20000,
        )
        LeaveBalance.objects.filter(employee=self.employee, leave_type=self.leave_type).update(used_leaves=3)
        LeaveBalance.objects.create(
            employee=self.employee,
            leave_type=self.inactive_leave_type,
            year=current_leave_year(),
            total_leaves=10,
            used_leaves=2,
        )

    def test_dashboard_uses_total_remaining_leave_balance(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('employee_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_remaining_leaves'], 9.0)
        self.assertContains(response, '9')
        self.assertContains(response, 'Remaining: 9 days')
        self.assertNotContains(response, '{{ balance.remaining_leaves }}')
        self.assertFalse(self.inactive_leave_type.is_active)

    def test_leave_balance_usage_percentage_is_relative_to_total(self):
        balance = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type)
        self.assertEqual(round(balance.usage_percentage, 2), 25.0)


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class EmployeeDetailAttendanceIntelligenceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr = User.objects.create_user(
            username='detail-hr',
            email='detail-hr@example.com',
            password='testpass123',
            role='HR',
        )
        self.employee = User.objects.create_user(
            username='detail-employee',
            email='detail-employee@example.com',
            password='testpass123',
            role='EMPLOYEE',
            first_name='Detail',
            last_name='Employee',
        )
        EmployeeProfile.objects.create(
            user=self.employee,
            department='IT',
            designation='JUNIOR',
            gender='M',
            salary=22000,
        )

    def test_absent_record_does_not_render_active_session_in_attendance_intelligence(self):
        Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 3, 3),
        )
        self.client.force_login(self.hr)

        response = self.client.get(reverse('employee_detail', args=[self.employee.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ABSENT')
        self.assertNotContains(response, 'Active Session')

    def test_open_attendance_session_is_labeled_active_session(self):
        Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 3, 4),
            check_in=time(hour=9, minute=0),
        )
        self.client.force_login(self.hr)

        response = self.client.get(reverse('employee_detail', args=[self.employee.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Active Session')
