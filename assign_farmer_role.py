#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/machinist/Documents/test/matbw')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Role

User = get_user_model()

def assign_farmer_role():
    """Assign farmer role to test user"""
    
    print("👤 Assigning farmer role to test user...")
    
    try:
        # Get farmer role
        farmer_role, created = Role.objects.get_or_create(
            name='farmer',
            defaults={'description': 'Farmer role for agricultural users'}
        )
        
        if created:
            print("✅ Farmer role created")
        else:
            print("ℹ️ Farmer role already exists")
        
        # Get test farmer
        farmer = User.objects.get(username='testfarmer1')
        
        # Assign role
        farmer.role = farmer_role
        farmer.save()
        
        print(f"✅ Role assigned to {farmer.username}")
        print(f"Role: {farmer.role.name}")
        print(f"Role ID: {farmer.role.id}")
        
    except User.DoesNotExist:
        print("❌ Test farmer not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    assign_farmer_role()
