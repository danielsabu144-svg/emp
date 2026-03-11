from datetime import datetime, time, timedelta

from django.db import migrations, models


def backfill_attendance_detection(apps, schema_editor):
    Attendance = apps.get_model('attendance', 'Attendance')
    office_start_time = time(hour=9, minute=0)
    office_end_time = time(hour=18, minute=0)
    half_day_min_hours = 4.5

    for attendance in Attendance.objects.all().iterator():
        is_late_entry = False
        is_early_exit = False

        if not attendance.login_time:
            status = 'ABSENT'
        else:
            login_time = attendance.login_time.replace(second=0, microsecond=0)
            is_late_entry = login_time > office_start_time
            status = 'LATE' if is_late_entry else 'PRESENT'

            if attendance.logout_time:
                logout_time = attendance.logout_time.replace(second=0, microsecond=0)
                is_early_exit = logout_time < office_end_time

                login_dt = datetime.combine(attendance.date, attendance.login_time)
                logout_dt = datetime.combine(attendance.date, attendance.logout_time)
                duration = logout_dt - login_dt if logout_dt > login_dt else timedelta()
                worked_hours = duration.total_seconds() / 3600
                if worked_hours < half_day_min_hours:
                    status = 'HALF_DAY'

        attendance.is_late_entry = is_late_entry
        attendance.is_early_exit = is_early_exit
        attendance.status = status
        attendance.save(update_fields=['is_late_entry', 'is_early_exit', 'status'])


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='is_early_exit',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='attendance',
            name='is_late_entry',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(backfill_attendance_detection, migrations.RunPython.noop),
    ]
