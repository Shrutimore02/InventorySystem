import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_employee_department_employee_email_employee_gender_and_more'),
        ('transfers', '0007_alter_transfer_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='transfer',
            name='admin_comment',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='transfer',
            name='rejected_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transfer',
            name='rejected_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='rejected_transfers', to='accounts.employee'),
        ),
        migrations.AddField(
            model_name='transfer',
            name='rejection_reason',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='transfer',
            name='return_condition',
            field=models.CharField(choices=[('GOOD', 'Good'), ('DAMAGED', 'Damaged'), ('INCOMPLETE', 'Incomplete')], default='GOOD', max_length=20),
        ),
        migrations.AddField(
            model_name='transfer',
            name='return_note',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='status',
            field=models.CharField(choices=[('AWAITING_APPROVAL', 'Awaiting Approval'), ('APPROVED', 'Approved'), ('RECEIVED', 'Received'), ('RETURN_REQUESTED', 'Return Requested'), ('RETURNED', 'Returned'), ('CANCELLED', 'Cancelled'), ('REJECTED', 'Rejected')], default='AWAITING_APPROVAL', max_length=30),
        ),
        migrations.CreateModel(
            name='TransferAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=80)),
                ('note', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.employee')),
                ('transfer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='transfers.transfer')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
