from django.db import models
from accounts.models import User
from django.utils import timezone


def current_leave_year():
    return timezone.localdate().year


class LeaveType(models.Model):
    """Different types of leaves available"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    max_days_per_year = models.IntegerField(default=5)
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
    total_leaves = models.IntegerField(default=5)
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


def ensure_leave_balances_for_employee(employee, year=None):
    if not employee or not employee.is_employee:
        return

    balance_year = year or current_leave_year()
    for leave_type in LeaveType.objects.filter(is_active=True).order_by('name'):
        LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            year=balance_year,
            defaults={'total_leaves': leave_type.max_days_per_year},
        )


def ensure_leave_balances_for_leave_type(leave_type, year=None):
    if not leave_type or not leave_type.is_active:
        return

    balance_year = year or current_leave_year()
    employees = User.objects.filter(role='EMPLOYEE')
    for employee in employees.iterator():
        LeaveBalance.objects.get_or_create(
            employee=employee,
            leave_type=leave_type,
            year=balance_year,
            defaults={'total_leaves': leave_type.max_days_per_year},
        )
