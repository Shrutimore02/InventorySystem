from django.db import migrations, models


def seed_first_admin(apps, schema_editor):
    Employee = apps.get_model('accounts', 'Employee')
    if not Employee.objects.filter(role='ADM').exists():
        first_employee = Employee.objects.order_by('id').first()
        if first_employee:
            first_employee.role = 'ADM'
            first_employee.save(update_fields=['role'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='role',
            field=models.CharField(choices=[('EMP', 'Employee'), ('ADM', 'Admin')], default='EMP', max_length=3),
        ),
        migrations.RunPython(seed_first_admin, migrations.RunPython.noop),
    ]
