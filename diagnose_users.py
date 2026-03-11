import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_management.settings')
django.setup()

from accounts.models import User

print("START DIAGNOSIS")
sys.stdout.flush()
users = list(User.objects.all())
print(f"Total Users Found: {len(users)}")
for u in users:
    print(f"ID: {u.id} | NAME: {repr(u.username)} | ROLE: {u.role}")
    sys.stdout.flush()
print("END DIAGNOSIS")
