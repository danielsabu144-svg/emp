import calendar
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from accounts.models import User


TWOPLACES = Decimal('0.01')
ZERO = Decimal('0.00')


def money(value):
    if isinstance(value, Decimal):
        decimal_value = value
    else:
        decimal_value = Decimal(str(value or 0))
    return decimal_value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

class Payroll(models.Model):
    """Monthly payroll records for employees"""

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payrolls')
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    working_days = models.IntegerField(default=0)
    present_days = models.DecimalField(max_digits=5, decimal_places=1, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.employee.username} - {self.month}/{self.year}"
    
    @property
    def earned_basic_salary(self):
        """Attendance-adjusted basic pay for the payroll period."""
        if self.working_days > 0:
            per_day_salary = Decimal(self.basic_salary) / Decimal(self.working_days)
            return money(per_day_salary * Decimal(self.present_days))
        return money(self.basic_salary)

    @property
    def gross_salary(self):
        """Actual gross earnings payable for this payroll period."""
        return money(self.earned_basic_salary + Decimal(self.allowances))

    @property
    def attendance_deduction(self):
        """Salary reduced because of unpaid or partial attendance."""
        return money(max(Decimal(self.basic_salary) - self.earned_basic_salary, ZERO))

    @property
    def tds(self):
        """Tax deducted at source on actual payable gross salary."""
        gross = self.gross_salary
        if gross > Decimal('30000.00'):
            return money(gross * Decimal('0.05'))
        return ZERO

    @property
    def professional_tax(self):
        """Simplified professional tax"""
        gross = self.gross_salary
        if gross > Decimal('20000.00'):
            return Decimal('200.00')
        return ZERO

    @property
    def total_deductions(self):
        """Aggregate of manual deductions and standard taxes"""
        return money(Decimal(self.deductions) + self.tds + self.professional_tax)

    def calculate_net_salary(self):
        """Calculate net salary based on attendance and total deductions"""
        self.net_salary = money(max(self.gross_salary - self.total_deductions, ZERO))
        return self.net_salary
    
    @property
    def month_name(self):
        """Get month name"""
        if 1 <= self.month <= 12:
            return calendar.month_name[self.month]
        return f"Month {self.month}"

    @property
    def unpaid_days(self):
        return max(Decimal(str(self.working_days)) - Decimal(str(self.present_days)), Decimal('0.0'))
    
    class Meta:
        unique_together = ('employee', 'month', 'year')
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['employee', 'year', 'month']),
            models.Index(fields=['is_paid']),
        ]
        verbose_name_plural = 'Payrolls'


class PayrollComponent(models.Model):
    """Additional payroll components like bonuses, overtime, etc."""
    
    COMPONENT_TYPE_CHOICES = (
        ('ALLOWANCE', 'Allowance'),
        ('DEDUCTION', 'Deduction'),
        ('BONUS', 'Bonus'),
        ('OVERTIME', 'Overtime'),
    )
    
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='components')
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.payroll.employee.username} - {self.name} - {self.amount}"
    
    class Meta:
        ordering = ['component_type', 'name']
