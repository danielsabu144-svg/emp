from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Custom manager to handle user and superuser creation with roles."""

    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be set")

        email = self.normalize_email(email)
        extra_fields.setdefault("role", "EMPLOYEE")

        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        # Ensure superusers are always created as Superadmin
        extra_fields.setdefault("role", "SUPERADMIN")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with role-based authentication"""
    
    ROLE_CHOICES = (
        ('SUPERADMIN', 'Super Admin'),
        ('HR', 'HR/Admin'),
        ('EMPLOYEE', 'Employee'),
    )
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    objects = UserManager()
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"
    
    @property
    def is_hr(self):
        return self.role == 'HR' or self.is_superuser
    
    @property
    def is_employee(self):
        return self.role == 'EMPLOYEE' and not self.is_superuser
