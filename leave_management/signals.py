from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from .models import LeaveType, ensure_casual_leave_policy, ensure_leave_balances_for_employee, ensure_leave_balances_for_leave_type

@receiver(post_save, sender=User)
def create_leave_balances(sender, instance, created, **kwargs):
    if created and instance.is_employee:
        ensure_leave_balances_for_employee(instance)


@receiver(post_save, sender=LeaveType)
def create_missing_balances_for_new_leave_type(sender, instance, **kwargs):
    ensure_casual_leave_policy()
    ensure_leave_balances_for_leave_type(instance)
