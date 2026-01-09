# Generated manually - Data migration to create default industry

from django.db import migrations


def create_default_industry(apps, schema_editor):
    """
    Create a default industry for existing users.
    """
    Industry = apps.get_model('users', 'Industry')
    User = apps.get_model('users', 'User')
    
    # Check if any industry exists
    if not Industry.objects.exists():
        # Create default industry
        default_industry = Industry.objects.create(
            name='Default Industry',
            description='Default industry for existing users'
        )
        print(f"✅ Created default industry: {default_industry.name} (ID: {default_industry.id})")
        
        # Assign users without industry to default industry
        users_updated = User.objects.filter(industry__isnull=True, is_superuser=False).update(industry=default_industry)
        if users_updated > 0:
            print(f"✅ Assigned {users_updated} users to default industry")
    else:
        print("✅ Industries already exist, skipping default industry creation")


def reverse_create_default_industry(apps, schema_editor):
    """
    Reverse migration - remove default industry if it exists.
    """
    Industry = apps.get_model('users', 'Industry')
    try:
        default_industry = Industry.objects.get(name='Default Industry')
        # Unassign users from default industry
        User = apps.get_model('users', 'User')
        User.objects.filter(industry=default_industry).update(industry=None)
        default_industry.delete()
        print("✅ Removed default industry")
    except Industry.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_add_industry_multi_tenant'),
    ]

    operations = [
        migrations.RunPython(create_default_industry, reverse_create_default_industry),
    ]

