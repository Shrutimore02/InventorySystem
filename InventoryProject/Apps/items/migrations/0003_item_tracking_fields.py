import uuid

from django.db import migrations, models
import Apps.items.models


def generate_code():
    return f"ITM-{uuid.uuid4().hex[:8].upper()}"


def seed_item_codes(apps, schema_editor):
    Item = apps.get_model('items', 'Item')
    for item in Item.objects.all():
        if not item.item_code:
            code = generate_code()
            while Item.objects.filter(item_code=code).exclude(pk=item.pk).exists():
                code = generate_code()
            item.item_code = code
        if not item.qr_value:
            item.qr_value = item.item_code
        item.save(update_fields=['item_code', 'qr_value'])


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0002_remove_item_description_alter_item_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='assigned_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='item',
            name='availability',
            field=models.CharField(choices=[('AVAILABLE', 'Available'), ('ASSIGNED', 'Assigned'), ('IN_APPROVAL', 'Awaiting Approval'), ('RETURN_PENDING', 'Return Pending'), ('MAINTENANCE', 'Maintenance')], default='AVAILABLE', max_length=20),
        ),
        migrations.AddField(
            model_name='item',
            name='item_code',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='item',
            name='location_note',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='item',
            name='qr_value',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='item',
            name='total_quantity',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.RunPython(seed_item_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='item',
            name='item_code',
            field=models.CharField(default=Apps.items.models.generate_item_code, max_length=20, unique=True),
        ),
    ]
