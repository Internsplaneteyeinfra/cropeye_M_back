# Migration for created_by field (already exists in 0001_initial, but keeping for migration chain consistency)

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_create_default_industry'),
    ]

    operations = [
        # created_by field already exists in 0001_initial
        # This migration is kept for consistency with migration dependencies
    ]

