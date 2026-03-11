from datetime import timedelta

from django.contrib.messages import get_messages
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Leave, LeaveBalance, LeaveType, current_leave_year


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class LeaveManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr = User.objects.create_user(
            username='leave-hr',
            email='leave-hr@example.com',
            password='testpass123',
            role='HR',
            first_name='Hari',
            last_name='Manager',
        )
        self.employee = User.objects.create_user(
            username='leave-emp',
            email='leave-emp@example.com',
            password='testpass123',
            role='EMPLOYEE',
            first_name='Esha',
            last_name='Employee',
        )
        self.leave_type = LeaveType.objects.create(
            name='Casual Leave',
            max_days_per_year=5,
            is_active=True,
        )
        self.leave = Leave.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            from_date=timezone.localdate() + timedelta(days=1),
            to_date=timezone.localdate() + timedelta(days=2),
            reason='Family work',
        )

    def test_hr_leave_requests_renders_leave_type_column(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('leave_requests'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Casual Leave')

    def test_employee_leave_history_renders_leave_type_column(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('my_leaves'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Casual Leave')

    def test_new_leave_type_creates_balances_for_existing_employees(self):
        existing_balance_count = LeaveBalance.objects.filter(employee=self.employee).count()

        new_leave_type = LeaveType.objects.create(
            name='Sick Leave',
            max_days_per_year=5,
            is_active=True,
        )

        self.assertEqual(
            LeaveBalance.objects.filter(
                employee=self.employee,
                leave_type=new_leave_type,
                year=current_leave_year(),
            ).count(),
            1,
        )
        self.assertGreater(
            LeaveBalance.objects.filter(employee=self.employee).count(),
            existing_balance_count,
        )

    def test_apply_leave_requires_leave_type_selection(self):
        self.client.force_login(self.employee)

        response = self.client.post(
            reverse('apply_leave'),
            {
                'leave_type': '',
                'from_date': timezone.localdate() + timedelta(days=1),
                'to_date': timezone.localdate() + timedelta(days=1),
                'reason': 'Need leave',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Please select a leave type.', messages)

    def test_apply_leave_page_shows_five_day_max_limit(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('apply_leave'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Casual Leave (Max: 5 days)')
