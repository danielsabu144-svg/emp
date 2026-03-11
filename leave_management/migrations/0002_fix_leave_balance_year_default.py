from django.db import migrations, models

import leave_management.models


class Migration(migrations.Migration):

    dependencies = [
        ('leave_management', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leavebalance',
            name='year',
            field=models.IntegerField(default=leave_management.models.current_leave_year),
        ),
    ]
