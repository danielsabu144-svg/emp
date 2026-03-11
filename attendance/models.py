from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from accounts.models import User


class Attendance(models.Model):
    """Employee attendance tracking using raw punches plus computed flags."""

    FINAL_STATUS_CHOICES = (
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
        ('LATE_EARLY_LEAVE', 'Late + Early Leave'),
        ('LATE', 'Late'),
        ('EARLY_LEAVE', 'Early Leave'),
        ('PRESENT', 'Present'),
    )
    STATUS_LABELS = dict(FINAL_STATUS_CHOICES)
    FULL_DAY_STATUSES = ('PRESENT', 'LATE', 'EARLY_LEAVE', 'LATE_EARLY_LEAVE')
    PAYABLE_STATUSES = FULL_DAY_STATUSES + ('HALF_DAY',)

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    worked_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_late = models.BooleanField(default=False)
    is_early_leave = models.BooleanField(default=False)
    is_half_day = models.BooleanField(default=False)
    is_absent = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date']),
        ]
        verbose_name_plural = 'Attendances'

    def __str__(self):
        return f"{self.employee.username} - {self.date} - {self.final_status_label}"

    @staticmethod
    def _coerce_time(value, fallback):
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            for fmt in ('%H:%M:%S', '%H:%M'):
                try:
                    return datetime.strptime(value, fmt).time()
                except ValueError:
                    continue
        return fallback

    @classmethod
    def get_policy(cls):
        policy = getattr(settings, 'ATTENDANCE_POLICY', {})
        return {
            'office_start': cls._coerce_time(
                policy.get('office_start') or policy.get('office_start_time'),
                time(hour=9, minute=0),
            ),
            'office_end': cls._coerce_time(
                policy.get('office_end') or policy.get('office_end_time'),
                time(hour=17, minute=0),
            ),
            'full_day_hours': Decimal(str(policy.get('full_day_hours', 8))),
            'half_day_hours': Decimal(
                str(policy.get('half_day_hours', policy.get('half_day_min_hours', 4)))
            ),
            'late_grace_minutes': int(policy.get('late_grace_minutes', 0)),
        }

    @staticmethod
    def normalize_time(value):
        if not value:
            return None
        return value.replace(second=0, microsecond=0)

    @classmethod
    def status_query(cls, status_code):
        queries = {
            'ABSENT': Q(is_absent=True),
            'HALF_DAY': Q(is_absent=False, is_half_day=True),
            'LATE_EARLY_LEAVE': Q(
                is_absent=False,
                is_half_day=False,
                is_late=True,
                is_early_leave=True,
            ),
            'LATE': Q(
                is_absent=False,
                is_half_day=False,
                is_late=True,
                is_early_leave=False,
            ),
            'EARLY_LEAVE': Q(
                is_absent=False,
                is_half_day=False,
                is_late=False,
                is_early_leave=True,
            ),
            'PRESENT': Q(
                is_absent=False,
                is_half_day=False,
                is_late=False,
                is_early_leave=False,
            ),
        }
        return queries.get(status_code, Q())

    @classmethod
    def payable_query(cls):
        return Q(is_absent=False)

    @classmethod
    def full_day_query(cls):
        return Q(is_absent=False, is_half_day=False)

    def get_work_duration(self):
        if not self.check_in or not self.check_out:
            return timedelta()

        check_in_dt = datetime.combine(self.date, self.check_in)
        check_out_dt = datetime.combine(self.date, self.check_out)
        if check_out_dt <= check_in_dt:
            return timedelta()
        return check_out_dt - check_in_dt

    def calculate_worked_hours(self):
        duration = self.get_work_duration()
        total_seconds = Decimal(str(int(duration.total_seconds())))
        hours = (total_seconds / Decimal('3600')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP,
        )
        return max(hours, Decimal('0.00'))

    def evaluate_attendance(self):
        policy = self.get_policy()

        self.check_in = self.normalize_time(self.check_in)
        self.check_out = self.normalize_time(self.check_out)
        self.worked_hours = self.calculate_worked_hours()

        self.is_late = False
        self.is_early_leave = False
        self.is_half_day = False
        self.is_absent = not bool(self.check_in)

        if self.is_absent:
            self.worked_hours = Decimal('0.00')
            return self.final_status

        start_dt = datetime.combine(self.date, policy['office_start'])
        late_cutoff = (start_dt + timedelta(minutes=policy['late_grace_minutes'])).time()
        self.is_late = self.check_in > late_cutoff

        if self.check_out:
            if self.worked_hours < policy['half_day_hours']:
                self.is_half_day = True
                self.is_early_leave = False
            else:
                self.is_early_leave = self.check_out < policy['office_end']

        return self.final_status

    @property
    def final_status(self):
        if self.is_absent:
            return 'ABSENT'
        if self.is_half_day:
            return 'HALF_DAY'
        if self.is_late and self.is_early_leave:
            return 'LATE_EARLY_LEAVE'
        if self.is_late:
            return 'LATE'
        if self.is_early_leave:
            return 'EARLY_LEAVE'
        return 'PRESENT'

    @property
    def final_status_label(self):
        return self.STATUS_LABELS[self.final_status]

    @property
    def status(self):
        return self.final_status

    def get_status_display(self):
        return self.final_status_label

    @property
    def attendance_credit(self):
        if self.final_status == 'HALF_DAY':
            return Decimal('0.5')
        if self.final_status in self.FULL_DAY_STATUSES:
            return Decimal('1.0')
        return Decimal('0.0')

    @property
    def detection_labels(self):
        labels = []
        if self.is_late:
            labels.append('Late')
        if self.is_early_leave:
            labels.append('Early Leave')
        if self.is_half_day:
            labels.append('Half Day')
        return labels

    @property
    def login_time(self):
        return self.check_in

    @login_time.setter
    def login_time(self, value):
        self.check_in = value

    @property
    def logout_time(self):
        return self.check_out

    @logout_time.setter
    def logout_time(self, value):
        self.check_out = value

    @property
    def is_late_entry(self):
        return self.is_late

    @is_late_entry.setter
    def is_late_entry(self, value):
        self.is_late = value

    @property
    def is_early_exit(self):
        return self.is_early_leave

    @is_early_exit.setter
    def is_early_exit(self, value):
        self.is_early_leave = value

    def save(self, *args, **kwargs):
        self.evaluate_attendance()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            update_fields = set(update_fields)
            update_fields.update(
                {
                    'worked_hours',
                    'is_late',
                    'is_early_leave',
                    'is_half_day',
                    'is_absent',
                }
            )
            kwargs['update_fields'] = list(update_fields)
        super().save(*args, **kwargs)

    def get_work_hours(self):
        """Return worked hours as decimal and a friendly formatted string."""
        duration = self.get_work_duration()
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        return {
            'decimal': float(self.worked_hours),
            'formatted': f"{hours}h {minutes}m",
        }
