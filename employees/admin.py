from django.contrib import admin
from .models import EmployeeProfile

@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'designation', 'salary', 'is_active', 'created_at')
    list_filter = ('department', 'designation', 'is_active')
    search_fields = ('user__username', 'user__email', 'user__employee_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Details', {
            'fields': ('department', 'designation', 'salary', 'is_active')
        }),
        ('Personal Details', {
            'fields': ('gender', 'address', 'blood_group')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
