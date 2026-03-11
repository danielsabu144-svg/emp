from django.db import migrations, models


def set_leave_limits_to_five(apps, schema_editor):
    LeaveType = apps.get_model('leave_management', 'LeaveType')
    LeaveBalance = apps.get_model('leave_management', 'LeaveBalance')

    LeaveType.objects.all().update(max_days_per_year=5)
    LeaveBalance.objects.all().update(total_leaves=5)


class Migration(migrations.Migration):

    dependencies = [
        ('leave_management', '0002_fix_leave_balance_year_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leavetype',
            name='max_days_per_year',
            field=models.IntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='leavebalance',
            name='total_leaves',
            field=models.IntegerField(default=5),
        ),
        migrations.RunPython(set_leave_limits_to_five, migrations.RunPython.noop),
    ]
