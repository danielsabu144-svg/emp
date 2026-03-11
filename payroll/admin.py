from django.contrib import admin
from .models import Payroll, PayrollComponent

class PayrollComponentInline(admin.TabularInline):
    model = PayrollComponent
    extra = 1


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month_name', 'year', 'basic_salary', 'net_salary', 'is_paid', 'payment_date')
    list_filter = ('is_paid', 'year', 'month')
    search_fields = ('employee__username', 'employee__email')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PayrollComponentInline]
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'month', 'year')
        }),
        ('Salary Details', {
            'fields': ('basic_salary', 'allowances', 'deductions', 'net_salary')
        }),
        ('Attendance', {
            'fields': ('working_days', 'present_days')
        }),
        ('Payment', {
            'fields': ('is_paid', 'payment_date', 'remarks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PayrollComponent)
class PayrollComponentAdmin(admin.ModelAdmin):
    list_display = ('payroll', 'component_type', 'name', 'amount')
    list_filter = ('component_type',)
    search_fields = ('payroll__employee__username', 'name')
