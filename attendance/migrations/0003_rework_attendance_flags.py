from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db import migrations, models


def backfill_raw_attendance_fields(apps, schema_editor):
    Attendance = apps.get_model('attendance', 'Attendance')
    office_start = time(hour=9, minute=0)
    office_end = time(hour=17, minute=0)
    half_day_hours = Decimal('4.00')

    for attendance in Attendance.objects.all().iterator():
        check_in = attendance.check_in.replace(second=0, microsecond=0) if attendance.check_in else None
        check_out = attendance.check_out.replace(second=0, microsecond=0) if attendance.check_out else None

        attendance.check_in = check_in
        attendance.check_out = check_out
        attendance.is_late = False
        attendance.is_early_leave = False
        attendance.is_half_day = False
        attendance.is_absent = not bool(check_in)
        attendance.worked_hours = Decimal('0.00')

        if check_in:
            attendance.is_late = check_in > office_start

            if check_out:
                check_in_dt = datetime.combine(attendance.date, check_in)
                check_out_dt = datetime.combine(attendance.date, check_out)
                duration = check_out_dt - check_in_dt if check_out_dt > check_in_dt else timedelta()
                total_seconds = Decimal(str(int(duration.total_seconds())))
                attendance.worked_hours = (total_seconds / Decimal('3600')).quantize(
                    Decimal('0.01'),
                    rounding=ROUND_HALF_UP,
                )

                if attendance.worked_hours < half_day_hours:
                    attendance.is_half_day = True
                else:
                    attendance.is_early_leave = check_out < office_end

        attendance.save(
            update_fields=[
                'check_in',
                'check_out',
                'worked_hours',
                'is_late',
                'is_early_leave',
                'is_half_day',
                'is_absent',
            ]
        )


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_attendance_detection_flags'),
    ]

    operations = [
        migrations.RenameField(
            model_name='attendance',
            old_name='login_time',
            new_name='check_in',
        ),
        migrations.RenameField(
            model_name='attendance',
            old_name='logout_time',
            new_name='check_out',
        ),
        migrations.RenameField(
            model_name='attendance',
            old_name='is_late_entry',
            new_name='is_late',
        ),
        migrations.RenameField(
            model_name='attendance',
            old_name='is_early_exit',
            new_name='is_early_leave',
        ),
        migrations.AddField(
            model_name='attendance',
            name='worked_hours',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=5),
        ),
        migrations.AddField(
            model_name='attendance',
            name='is_half_day',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='attendance',
            name='is_absent',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(backfill_raw_attendance_fields, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='attendance',
            name='status',
        ),
    ]
