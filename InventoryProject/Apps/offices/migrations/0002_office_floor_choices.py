from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offices', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='office',
            name='floor_choices',
            field=models.TextField(blank=True, default=''),
        ),
    ]
