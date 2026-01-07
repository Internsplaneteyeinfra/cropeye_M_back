#!/usr/bin/env python
"""
Migration reset script for production deployment.
This script handles migration dependency issues that can occur in production.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def reset_migrations():
    """Reset migrations to handle dependency issues."""
    print("🔄 Resetting migrations to handle dependency issues...")
    
    try:
        # First, try to run migrations normally
        print("📊 Attempting normal migration...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        print("✅ Normal migration successful!")
        return True
    except Exception as e:
        print(f"❌ Normal migration failed: {e}")
        
        try:
            # Try with fake initial
            print("🔄 Attempting migration with --fake-initial...")
            execute_from_command_line(['manage.py', 'migrate', '--fake-initial', '--noinput'])
            print("✅ Fake initial migration successful!")
            return True
        except Exception as e2:
            print(f"❌ Fake initial migration failed: {e2}")
            
            try:
                # Last resort: run syncdb
                print("🔄 Attempting syncdb as last resort...")
                execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
                print("✅ Syncdb successful!")
                return True
            except Exception as e3:
                print(f"❌ All migration attempts failed: {e3}")
                return False

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings_production')
    django.setup()
    
    success = reset_migrations()
    if not success:
        print("💥 Migration reset failed!")
        sys.exit(1)
    else:
        print("🎉 Migration reset successful!")
