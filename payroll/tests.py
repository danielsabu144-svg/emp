from datetime import date
from decimal import Decimal

from django.contrib.messages import get_messages
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from employees.models import EmployeeProfile

from .models import Payroll


class PayrollModelTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username='payroll-user',
            email='payroll@example.com',
            password='testpass123',
            role='EMPLOYEE',
        )

    def test_calculate_net_salary_uses_attendance_adjusted_gross(self):
        payroll = Payroll(
            employee=self.employee,
            month=3,
            year=2026,
            basic_salary=Decimal('30000.00'),
            allowances=Decimal('2000.00'),
            deductions=Decimal('1000.00'),
            working_days=30,
            present_days=Decimal('15.5'),
            net_salary=Decimal('0.00'),
        )

        payroll.calculate_net_salary()

        self.assertEqual(payroll.earned_basic_salary, Decimal('15500.00'))
        self.assertEqual(payroll.gross_salary, Decimal('17500.00'))
        self.assertEqual(payroll.attendance_deduction, Decimal('14500.00'))
        self.assertEqual(payroll.total_deductions, Decimal('1000.00'))
        self.assertEqual(payroll.net_salary, Decimal('16500.00'))
        self.assertEqual(payroll.unpaid_days, Decimal('14.5'))

    def test_month_name_handles_invalid_months_safely(self):
        payroll = Payroll(
            employee=self.employee,
            month=13,
            year=2026,
            basic_salary=Decimal('10000.00'),
            allowances=Decimal('0.00'),
            deductions=Decimal('0.00'),
            working_days=30,
            present_days=Decimal('30.0'),
            net_salary=Decimal('0.00'),
        )

        self.assertEqual(payroll.month_name, 'Month 13')

    def test_calculate_net_salary_never_returns_negative_value(self):
        payroll = Payroll(
            employee=self.employee,
            month=3,
            year=2026,
            basic_salary=Decimal('10000.00'),
            allowances=Decimal('0.00'),
            deductions=Decimal('15000.00'),
            working_days=30,
            present_days=Decimal('30.0'),
            net_salary=Decimal('0.00'),
        )

        payroll.calculate_net_salary()

        self.assertEqual(payroll.net_salary, Decimal('0.00'))


@override_settings(ALLOWED_HOSTS=['testserver', 'localhost'])
class PayrollViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr = User.objects.create_user(
            username='payroll-hr',
            email='payroll-hr@example.com',
            password='testpass123',
            role='HR',
        )
        self.employee = User.objects.create_user(
            username='payroll-employee',
            email='payroll-employee@example.com',
            password='testpass123',
            role='EMPLOYEE',
            employee_id='EMP900',
            first_name='Pay',
            last_name='Roll',
        )
        EmployeeProfile.objects.create(
            user=self.employee,
            department='IT',
            designation='JUNIOR',
            gender='M',
            salary=30000,
        )
        self.payroll = Payroll.objects.create(
            employee=self.employee,
            month=3,
            year=2026,
            basic_salary=Decimal('30000.00'),
            allowances=Decimal('2000.00'),
            deductions=Decimal('1000.00'),
            working_days=30,
            present_days=Decimal('15.5'),
            net_salary=Decimal('16500.00'),
        )

    def test_payroll_detail_renders_month_name_without_template_error(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('payroll_detail', args=[self.payroll.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'March 2026')
        self.assertContains(response, 'Payable Basic after Attendance')

    def test_employee_payroll_history_uses_month_name_property(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('my_payroll'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'March 2026')

    def test_mark_as_paid_rejects_get_requests(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('mark_as_paid', args=[self.payroll.id]))

        self.assertEqual(response.status_code, 405)

    def test_mark_as_paid_post_updates_record(self):
        self.client.force_login(self.hr)

        response = self.client.post(reverse('mark_as_paid', args=[self.payroll.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.payroll.refresh_from_db()
        self.assertTrue(self.payroll.is_paid)

    def test_mark_as_paid_preserves_existing_payment_date(self):
        self.payroll.is_paid = True
        self.payroll.payment_date = date(2026, 3, 31)
        self.payroll.save(update_fields=['is_paid', 'payment_date'])
        self.client.force_login(self.hr)

        response = self.client.post(reverse('mark_as_paid', args=[self.payroll.id]), follow=True)

        self.assertEqual(response.status_code, 200)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.payment_date, date(2026, 3, 31))

    def test_update_payroll_rejects_negative_adjustments(self):
        self.client.force_login(self.hr)

        response = self.client.post(
            reverse('update_payroll', args=[self.payroll.id]),
            {
                'allowances': '-1.00',
                'deductions': '-5.00',
                'remarks': 'Invalid negative values',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.payroll.refresh_from_db()
        self.assertEqual(self.payroll.allowances, Decimal('2000.00'))
        self.assertEqual(self.payroll.deductions, Decimal('1000.00'))
        self.assertIn('allowances', response.context['form'].errors)
        self.assertIn('deductions', response.context['form'].errors)

    def test_generate_payroll_rejects_invalid_period_input(self):
        self.client.force_login(self.hr)

        response = self.client.post(
            reverse('generate_payroll'),
            {'month': '13', 'year': 'invalid'},
            follow=True,
        )

        self.assertEqual(response.status_code, 400)
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Please select a valid payroll month and year.', messages)

    def test_payroll_list_falls_back_on_invalid_period_filter(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('payroll_list'), {'month': '99', 'year': 'abc'}, follow=True)

        self.assertEqual(response.status_code, 200)
        messages = [message.message for message in get_messages(response.wsgi_request)]
        self.assertIn('Invalid payroll period selected. Showing the current month instead.', messages)
