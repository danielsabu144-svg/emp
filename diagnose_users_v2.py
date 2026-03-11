import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_management.settings')
django.setup()

from accounts.models import User

print("START DETAILED DIAGNOSIS")
sys.stdout.flush()
users = list(User.objects.all().order_by('-date_joined'))
print(f"Total Users Found: {len(users)}")
for u in users:
    profile_exists = hasattr(u, 'profile')
    dept = u.profile.department if profile_exists else "No Profile"
    print(f"ID: {u.id} | USER: {u.username} | EMPID: {repr(u.employee_id)} | JOIN: {u.date_joined} | JOIN2: {u.date_of_joining} | ROLE: {u.role} | DEPT: {dept}")
    sys.stdout.flush()
print("END DIAGNOSIS")
