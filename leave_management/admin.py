from django.contrib import admin
from .models import LeaveType, Leave, LeaveBalance

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'max_days_per_year', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'from_date', 'to_date', 'total_days', 'status', 'applied_on')
    list_filter = ('status', 'leave_type', 'applied_on')
    search_fields = ('employee__username', 'employee__email')
    date_hierarchy = 'applied_on'
    readonly_fields = ('applied_on', 'updated_on')
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'leave_type')
        }),
        ('Leave Details', {
            'fields': ('from_date', 'to_date', 'reason')
        }),
        ('Approval', {
            'fields': ('status', 'approved_by', 'approval_remarks')
        }),
        ('Timestamps', {
            'fields': ('applied_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'year', 'total_leaves', 'used_leaves', 'remaining_leaves')
    list_filter = ('year', 'leave_type')
    search_fields = ('employee__username', 'employee__email')
