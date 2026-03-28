from django.contrib.auth.hashers import make_password
from django.db import migrations, models


def seed_existing_credentials(apps, schema_editor):
    Employee = apps.get_model('accounts', 'Employee')
    for employee in Employee.objects.all():
        updated_fields = []
        if not employee.username:
            base_username = (employee.phone or f'user{employee.id}').replace(' ', '')
            username = base_username
            counter = 1
            while Employee.objects.exclude(pk=employee.pk).filter(username=username).exists():
                username = f'{base_username}{counter}'
                counter += 1
            employee.username = username
            updated_fields.append('username')
        if not employee.password:
            initial_password = employee.phone or f'user{employee.id}@123'
            employee.password = make_password(initial_password)
            updated_fields.append('password')
        if updated_fields:
            employee.save(update_fields=updated_fields)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_employee_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='department',
            field=models.CharField(default='General', max_length=100),
        ),
        migrations.AddField(
            model_name='employee',
            name='email',
            field=models.EmailField(blank=True, default='', max_length=254),
        ),
        migrations.AddField(
            model_name='employee',
            name='gender',
            field=models.CharField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], default='O', max_length=1),
        ),
        migrations.AddField(
            model_name='employee',
            name='password',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='employee',
            name='username',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
        migrations.RunPython(seed_existing_credentials, migrations.RunPython.noop),
    ]
