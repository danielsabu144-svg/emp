from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payroll',
            name='present_days',
            field=models.DecimalField(decimal_places=1, default=0, max_digits=5),
        ),
    ]
