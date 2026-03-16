from django.db import migrations, models


CASUAL_LEAVE_NAME = 'Casual Leave'
CASUAL_LEAVE_DAYS_PER_YEAR = 12


def enforce_casual_leave_policy(apps, schema_editor):
    LeaveType = apps.get_model('leave_management', 'LeaveType')
    LeaveBalance = apps.get_model('leave_management', 'LeaveBalance')

    casual_leave, _ = LeaveType.objects.get_or_create(
        name=CASUAL_LEAVE_NAME,
        defaults={
            'max_days_per_year': CASUAL_LEAVE_DAYS_PER_YEAR,
            'is_active': True,
        },
    )

    LeaveType.objects.filter(pk=casual_leave.pk).update(
        max_days_per_year=CASUAL_LEAVE_DAYS_PER_YEAR,
        is_active=True,
    )
    LeaveType.objects.exclude(pk=casual_leave.pk).update(is_active=False)
    LeaveBalance.objects.filter(leave_type_id=casual_leave.pk).update(total_leaves=CASUAL_LEAVE_DAYS_PER_YEAR)


class Migration(migrations.Migration):

    dependencies = [
        ('leave_management', '0003_update_leave_limits_to_five'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leavetype',
            name='max_days_per_year',
            field=models.IntegerField(default=12),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='total_leaves',
            field=models.IntegerField(default=12),
        ),
        migrations.RunPython(enforce_casual_leave_policy, migrations.RunPython.noop),
    ]
