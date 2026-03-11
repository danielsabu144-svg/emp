from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from employees.models import EmployeeProfile
from leave_management.models import LeaveType, LeaveBalance
from chatbot.models import ChatbotResponse
import datetime

class Command(BaseCommand):
    help = 'Seeds the database with sample HR and Employee data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Create Super Admin
        superadmin, created = User.objects.get_or_create(
            username='superadmin',
            defaults={
                'email': 'superadmin@ems.com',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': 'SUPERADMIN',
                'employee_id': 'SA001',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        superadmin_updates = []
        if superadmin.role != 'SUPERADMIN':
            superadmin.role = 'SUPERADMIN'
            superadmin_updates.append('role')
        if not superadmin.is_staff:
            superadmin.is_staff = True
            superadmin_updates.append('is_staff')
        if not superadmin.is_superuser:
            superadmin.is_superuser = True
            superadmin_updates.append('is_superuser')
        if not superadmin.is_active:
            superadmin.is_active = True
            superadmin_updates.append('is_active')
        if superadmin_updates:
            superadmin.save(update_fields=superadmin_updates)
        if created:
            superadmin.set_password('superadmin123')
            superadmin.save(update_fields=['password'])
            self.stdout.write('Created Super Admin: superadmin / superadmin123')

        # 2. Create HR Admin
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ems.com',
                'first_name': 'HR',
                'last_name': 'Manager',
                'role': 'HR',
                'employee_id': 'HR001'
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write('Created HR Admin: admin / admin123')

        # 3. Create Leave Types
        leave_types = [
            {'name': 'Casual Leave', 'max_days': 5},
            {'name': 'Sick Leave', 'max_days': 5},
            {'name': 'Earned Leave', 'max_days': 5},
        ]
        lt_objects = []
        for lt_data in leave_types:
            lt, _ = LeaveType.objects.get_or_create(
                name=lt_data['name'],
                defaults={'max_days_per_year': lt_data['max_days']}
            )
            lt_objects.append(lt)
        self.stdout.write('Created Leave Types.')

        # 4. Create Employees
        employees_data = [
            {'user': 'john_doe', 'fname': 'John', 'lname': 'Doe', 'dept': 'IT', 'desig': 'MANAGER', 'sal': 75000},
            {'user': 'jane_smith', 'fname': 'Jane', 'lname': 'Smith', 'dept': 'HR', 'desig': 'SENIOR', 'sal': 65000},
            {'user': 'mike_ross', 'fname': 'Mike', 'lname': 'Ross', 'dept': 'FINANCE', 'desig': 'JUNIOR', 'sal': 45000},
        ]

        current_year = timezone.now().year

        for emp in employees_data:
            user, created = User.objects.get_or_create(
                username=emp['user'],
                defaults={
                    'email': f"{emp['user']}@company.com",
                    'first_name': emp['fname'],
                    'last_name': emp['lname'],
                    'role': 'EMPLOYEE',
                    'employee_id': f"EMP{emp['user'].upper()[:3]}"
                }
            )
            if created:
                user.set_password('emp123')
                user.save()
                
                # Create Profile
                EmployeeProfile.objects.create(
                    user=user,
                    department=emp['dept'],
                    designation=emp['desig'],
                    salary=emp['sal'],
                    gender='M' if emp['fname'] != 'Jane' else 'F'
                )

                # Initialize Leave Balances
                for lt in lt_objects:
                    LeaveBalance.objects.get_or_create(
                        employee=user,
                        leave_type=lt,
                        year=current_year,
                        defaults={'total_leaves': lt.max_days_per_year}
                    )
                
                self.stdout.write(f"Created Employee: {emp['user']} / emp123")

        # 5. Create Chatbot Responses
        chatbot_data = [
            {'key': 'leave policy', 'res': 'Employees are entitled to Casual, Sick, and Earned leaves. Applications must be submitted 2 days in advance.'},
            {'key': 'office hours', 'res': 'Our office operates from 9:00 AM to 6:00 PM, Monday to Friday.'},
            {'key': 'salary date', 'res': 'Salaries are usually processed on the 1st of every month.'},
        ]
        for cb in chatbot_data:
            ChatbotResponse.objects.get_or_create(
                keyword=cb['key'],
                defaults={'response': cb['res'], 'category': 'General'}
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded all sample data!'))
