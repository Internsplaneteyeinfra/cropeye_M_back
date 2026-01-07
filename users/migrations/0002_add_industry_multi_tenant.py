# Generated manually for multi-tenant industry support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='industry',
            name='test_phone_number',
            field=models.CharField(blank=True, help_text='Test phone number for this industry (for testing purposes)', max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='industry',
            name='test_password',
            field=models.CharField(blank=True, help_text='Test password for this industry (for testing purposes)', max_length=128, null=True),
        ),
    ]

