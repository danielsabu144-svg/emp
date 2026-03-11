from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        'employee',
        'date',
        'check_in',
        'check_out',
        'worked_hours',
        'is_late',
        'is_early_leave',
        'is_half_day',
        'is_absent',
        'final_status_display',
        'created_at',
    )
    list_filter = ('is_absent', 'is_half_day', 'is_late', 'is_early_leave', 'date')
    search_fields = ('employee__username', 'employee__email')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'worked_hours', 'is_late', 'is_early_leave', 'is_half_day', 'is_absent')
    
    fieldsets = (
        ('Employee Information', {
            'fields': ('employee', 'date')
        }),
        ('Attendance Details', {
            'fields': (
                'check_in',
                'check_out',
                'worked_hours',
                'is_late',
                'is_early_leave',
                'is_half_day',
                'is_absent',
                'remarks',
            )
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Final Status')
    def final_status_display(self, obj):
        return obj.final_status_label
