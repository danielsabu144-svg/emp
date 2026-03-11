from datetime import date, time
from decimal import Decimal

from django.core.exceptions import FieldDoesNotExist
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User

from .models import Attendance


@override_settings(
    ATTENDANCE_POLICY={
        'office_start': time(hour=9, minute=0),
        'office_end': time(hour=17, minute=0),
        'full_day_hours': 8,
        'half_day_hours': 4,
        'late_grace_minutes': 0,
    }
)
class AttendanceModelTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username='employee1',
            email='employee1@example.com',
            password='testpass123',
            role='EMPLOYEE',
        )

    def test_attendance_uses_raw_check_times_and_computed_final_status(self):
        attendance = Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 3, 10),
            check_in=time(hour=9, minute=0),
            check_out=time(hour=17, minute=0),
        )

        self.assertEqual(attendance.final_status, 'PRESENT')
        self.assertEqual(attendance.worked_hours, Decimal('8.00'))
        self.assertFalse(attendance.is_late)
        self.assertFalse(attendance.is_early_leave)
        self.assertFalse(attendance.is_half_day)
        self.assertFalse(attendance.is_absent)
        self.assertEqual(attendance.attendance_credit, Decimal('1.0'))

    def test_late_and_early_leave_priority_overrides_plain_late(self):
        attendance = Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 3, 11),
            check_in=time(hour=9, minute=30),
            check_out=time(hour=16, minute=0),
        )

        self.assertEqual(attendance.final_status, 'LATE_EARLY_LEAVE')
        self.assertTrue(attendance.is_late)
        self.assertTrue(attendance.is_early_leave)
        self.assertFalse(attendance.is_half_day)
        self.assertEqual(attendance.detection_labels, ['Late', 'Early Leave'])

    def test_early_leave_status_is_detected_when_hours_are_not_half_day(self):
        attendance = Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 3, 12),
            check_in=time(hour=9, minute=0),
            check_out=time(hour=16, minute=0),
        )

        self.assertEqual(attendance.final_status, 'EARLY_LEAVE')
        self.assertFalse(attendance.is_late)
        self.assertTrue(attendance.is_early_leave)
        self.assertEqual(attendance.detection_labels, ['Early Leave'])

    def test_half_day_clears_early_leave_when_worked_hours_are_below_threshold(self):
        attendance = Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 3, 13),
            check_in=time(hour=12, minute=0),
            check_out=time(hour=15, minute=0),
        )

        self.assertEqual(attendance.final_status, 'HALF_DAY')
        self.assertTrue(attendance.is_late)
        self.assertFalse(attendance.is_early_leave)
        self.assertTrue(attendance.is_half_day)
        self.assertEqual(attendance.detection_labels, ['Late', 'Half Day'])
        self.assertEqual(attendance.attendance_credit, Decimal('0.5'))

    def test_missing_check_in_marks_attendance_absent(self):
        attendance = Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 3, 14),
        )

        self.assertEqual(attendance.final_status, 'ABSENT')
        self.assertTrue(attendance.is_absent)
        self.assertEqual(attendance.worked_hours, Decimal('0.00'))
        self.assertEqual(attendance.get_work_hours()['decimal'], 0.0)

    def test_status_is_not_a_stored_model_field_anymore(self):
        with self.assertRaises(FieldDoesNotExist):
            Attendance._meta.get_field('status')


@override_settings(
    ALLOWED_HOSTS=['testserver', 'localhost'],
    ATTENDANCE_POLICY={
        'office_start': time(hour=9, minute=0),
        'office_end': time(hour=17, minute=0),
        'full_day_hours': 8,
        'half_day_hours': 4,
        'late_grace_minutes': 0,
    }
)
class AttendanceViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.hr = User.objects.create_user(
            username='hr-user',
            email='hr@example.com',
            password='testpass123',
            role='HR',
        )
        self.employee = User.objects.create_user(
            username='emp-user',
            email='emp@example.com',
            password='testpass123',
            role='EMPLOYEE',
        )
        Attendance.objects.create(
            employee=self.employee,
            date=date(2026, 3, 15),
            check_in=time(hour=9, minute=45),
            check_out=time(hour=16, minute=0),
        )

    def test_hr_attendance_screen_renders_final_status_and_flags(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('attendance_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Late + Early Leave')
        self.assertContains(response, 'Early Leave')
        self.assertContains(response, 'Late')

    def test_hr_attendance_status_filter_supports_combined_priority_status(self):
        self.client.force_login(self.hr)

        response = self.client.get(reverse('attendance_list'), {'status': 'LATE_EARLY_LEAVE'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Late + Early Leave')

    def test_employee_attendance_screen_renders_updated_summary_labels(self):
        self.client.force_login(self.employee)

        response = self.client.get(reverse('my_attendance'), {'month': 3, 'year': 2026})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Late Entries')
        self.assertContains(response, 'Early Leaves')
        self.assertContains(response, 'Late + Early Leave')

    def test_employee_dashboard_shows_check_in_button_when_no_attendance_exists(self):
        fresh_employee = User.objects.create_user(
            username='fresh-employee',
            email='fresh@example.com',
            password='testpass123',
            role='EMPLOYEE',
        )
        self.client.force_login(fresh_employee)

        response = self.client.get(reverse('employee_dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Check In Now')
        self.assertNotContains(response, 'Check Out Now')

    def test_check_in_creates_todays_attendance(self):
        fresh_employee = User.objects.create_user(
            username='checkin-employee',
            email='checkin@example.com',
            password='testpass123',
            role='EMPLOYEE',
        )
        self.client.force_login(fresh_employee)

        response = self.client.post(reverse('mark_attendance_checkin'), follow=True)

        self.assertEqual(response.status_code, 200)
        attendance = Attendance.objects.get(employee=fresh_employee, date=timezone.localdate())
        self.assertIsNotNone(attendance.check_in)
        self.assertIsNone(attendance.check_out)
        self.assertFalse(attendance.is_absent)

    def test_check_out_updates_open_attendance(self):
        self.client.force_login(self.employee)
        open_attendance = Attendance.objects.create(
            employee=self.employee,
            date=timezone.localdate(),
            check_in=time(hour=9, minute=0),
        )

        response = self.client.post(reverse('mark_attendance_logout'), follow=True)

        self.assertEqual(response.status_code, 200)
        open_attendance.refresh_from_db()
        self.assertIsNotNone(open_attendance.check_out)
