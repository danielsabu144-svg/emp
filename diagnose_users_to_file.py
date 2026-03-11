import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_management.settings')
django.setup()

from accounts.models import User

with open("user_diag_report.txt", "w", encoding="utf-8") as f:
    f.write("USER DIAGNOSIS REPORT\n")
    f.write("====================\n")
    users = list(User.objects.all())
    f.write(f"Total Users: {len(users)}\n")
    for u in users:
        f.write(f"ID: {u.id} | Username: {repr(u.username)} | Role: {u.role} | SU: {u.is_superuser} | Active: {u.is_active}\n")
    f.write("====================\n")
