from django.db import models
from accounts.models import User
from django.utils import timezone


CASUAL_LEAVE_NAME = 'Casual Leave'
CASUAL_LEAVE_DAYS_PER_YEAR = 12


def current_leave_year():
    return timezone.localdate().year


class LeaveType(models.Model):
    """Different types of leaves available"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    max_days_per_year = models.IntegerField(default=CASUAL_LEAVE_DAYS_PER_YEAR)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Leave(models.Model):
    """Employee leave applications"""
    
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approval_remarks = models.TextField(blank=True, null=True)
    applied_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.name} ({self.from_date} to {self.to_date})"
    
    @property
    def total_days(self):
        """Calculate total leave days"""
        delta = self.to_date - self.from_date
        return delta.days + 1
    
    @property
    def is_pending(self):
        return self.status == 'PENDING'
    
    @property
    def is_approved(self):
        return self.status == 'APPROVED'
    
    class Meta:
        ordering = ['-applied_on']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['status']),
        ]


class LeaveBalance(models.Model):
    """Track leave balance for each employee"""
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.IntegerField(default=current_leave_year)
    total_leaves = models.IntegerField(default=CASUAL_LEAVE_DAYS_PER_YEAR)
    used_leaves = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    
    @property
    def remaining_leaves(self):
        return self.total_leaves - float(self.used_leaves)

    @property
    def usage_percentage(self):
        if self.total_leaves <= 0:
            return 0
        return min((float(self.used_leaves) / float(self.total_leaves)) * 100, 100)
    
    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.name} - {self.year}"
    
    class Meta:
        unique_together = ('employee', 'leave_type', 'year')
        ordering = ['-year', 'employee']


def ensure_casual_leave_policy():
    casual_leave, _ = LeaveType.objects.get_or_create(
        name=CASUAL_LEAVE_NAME,
        defaults={
            'max_days_per_year': CASUAL_LEAVE_DAYS_PER_YEAR,
            'is_active': True,
        },
    )

    updates = {}
    if casual_leave.max_days_per_year != CASUAL_LEAVE_DAYS_PER_YEAR:
        updates['max_days_per_year'] = CASUAL_LEAVE_DAYS_PER_YEAR
    if not casual_leave.is_active:
        updates['is_active'] = True

    if updates:
        LeaveType.objects.filter(pk=casual_leave.pk).update(**updates)
        for field_name, value in updates.items():
            setattr(casual_leave, field_name, value)

    LeaveType.objects.exclude(pk=casual_leave.pk).filter(is_active=True).update(is_active=False)
    return casual_leave


def get_active_leave_types():
    casual_leave = ensure_casual_leave_policy()
    return LeaveType.objects.filter(pk=casual_leave.pk, is_active=True)


def ensure_leave_balances_for_employee(employee, year=None):
    if not employee or not employee.is_employee:
        return

    balance_year = year or current_leave_year()
    leave_type = ensure_casual_leave_policy()
    leave_balance, _ = LeaveBalance.objects.get_or_create(
        employee=employee,
        leave_type=leave_type,
        year=balance_year,
        defaults={'total_leaves': leave_type.max_days_per_year},
    )

    if leave_balance.total_leaves != leave_type.max_days_per_year:
        LeaveBalance.objects.filter(pk=leave_balance.pk).update(total_leaves=leave_type.max_days_per_year)


def ensure_leave_balances_for_leave_type(leave_type, year=None):
    casual_leave = ensure_casual_leave_policy()
    if not leave_type or leave_type.pk != casual_leave.pk:
        return

    balance_year = year or current_leave_year()
    employees = User.objects.filter(role='EMPLOYEE')
    for employee in employees.iterator():
        leave_balance, _ = LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=casual_leave,
            year=balance_year,
            defaults={'total_leaves': casual_leave.max_days_per_year},
        )
        if leave_balance.total_leaves != casual_leave.max_days_per_year:
            LeaveBalance.objects.filter(pk=leave_balance.pk).update(total_leaves=casual_leave.max_days_per_year)
