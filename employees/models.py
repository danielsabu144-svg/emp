from django.db import models
from accounts.models import User

class EmployeeProfile(models.Model):
    """Extended employee profile information"""
    
    DEPARTMENT_CHOICES = (
        ('IT', 'Information Technology'),
        ('HR', 'Human Resources'),
        ('FINANCE', 'Finance'),
        ('MARKETING', 'Marketing'),
        ('SALES', 'Sales'),
        ('OPERATIONS', 'Operations'),
    )
    
    DESIGNATION_CHOICES = (
        ('MANAGER', 'Manager'),
        ('SENIOR', 'Senior Employee'),
        ('JUNIOR', 'Junior Employee'),
        ('INTERN', 'Intern'),
    )
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    department = models.CharField(max_length=20, choices=DEPARTMENT_CHOICES)
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['department']),
            models.Index(fields=['is_active']),
        ]
