from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transfers', '0008_transfer_admin_comment_transfer_rejected_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='transfer',
            name='from_floor',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='transfer',
            name='to_floor',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
