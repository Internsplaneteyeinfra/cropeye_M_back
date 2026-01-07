#!/usr/bin/env python3
"""
Comprehensive database schema fix to match Django models
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append('/home/machinist/Documents/test/matbw')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings_production')
django.setup()

import psycopg2
from django.conf import settings

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        database=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD']
    )

def fix_database_schema():
    """Fix database schema to match Django models"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # List of schema fixes needed
        schema_fixes = [
            # Add missing columns to farms_irrigationtype
            "ALTER TABLE farms_irrigationtype ADD COLUMN IF NOT EXISTS description TEXT;",
            
            # Add missing columns to farms_sensortype
            "ALTER TABLE farms_sensortype ADD COLUMN IF NOT EXISTS description TEXT;",
            
            # Add missing columns to farms_farmirrigation
            "ALTER TABLE farms_farmirrigation ADD COLUMN IF NOT EXISTS location GEOMETRY(POINT, 4326);",
            
            # Add missing columns to farms_farmsensor
            "ALTER TABLE farms_farmsensor ADD COLUMN IF NOT EXISTS name VARCHAR(100);",
            "ALTER TABLE farms_farmsensor ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';",
            "ALTER TABLE farms_farmsensor ADD COLUMN IF NOT EXISTS installation_date DATE;",
            "ALTER TABLE farms_farmsensor ADD COLUMN IF NOT EXISTS last_maintenance DATE;",
            "ALTER TABLE farms_farmsensor ADD COLUMN IF NOT EXISTS location GEOMETRY(POINT, 4326);",
            
            # Add missing columns to farms_farmimage
            "ALTER TABLE farms_farmimage ADD COLUMN IF NOT EXISTS title VARCHAR(200);",
            "ALTER TABLE farms_farmimage ADD COLUMN IF NOT EXISTS notes TEXT;",
            "ALTER TABLE farms_farmimage ADD COLUMN IF NOT EXISTS capture_date DATE;",
            "ALTER TABLE farms_farmimage ADD COLUMN IF NOT EXISTS location GEOMETRY(POINT, 4326);",
            
            # Add missing columns to equipment_equipment
            "ALTER TABLE equipment_equipment ADD COLUMN IF NOT EXISTS purchase_price DECIMAL(10,2);",
            "ALTER TABLE equipment_equipment ADD COLUMN IF NOT EXISTS last_maintenance_date DATE;",
            "ALTER TABLE equipment_equipment ADD COLUMN IF NOT EXISTS next_maintenance_date DATE;",
            "ALTER TABLE equipment_equipment ADD COLUMN IF NOT EXISTS location GEOMETRY(POINT, 4326);",
            
            # Add missing columns to equipment_equipmentusage
            "ALTER TABLE equipment_equipmentusage ADD COLUMN IF NOT EXISTS purpose TEXT;",
            "ALTER TABLE equipment_equipmentusage ADD COLUMN IF NOT EXISTS start_date TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE equipment_equipmentusage ADD COLUMN IF NOT EXISTS end_date TIMESTAMP WITH TIME ZONE;",
            
            # Add missing columns to equipment_maintenancerecord
            "ALTER TABLE equipment_maintenancerecord ADD COLUMN IF NOT EXISTS maintenance_type VARCHAR(50);",
            
            # Add missing columns to inventory_inventorytransaction
            "ALTER TABLE inventory_inventorytransaction ADD COLUMN IF NOT EXISTS unit_price DECIMAL(10,2);",
            "ALTER TABLE inventory_inventorytransaction ADD COLUMN IF NOT EXISTS total_price DECIMAL(10,2);",
            
            # Add missing columns to tasks_taskcomment
            "ALTER TABLE tasks_taskcomment ADD COLUMN IF NOT EXISTS content TEXT;",
            
            # Add missing columns to bookings_bookingcomment
            "ALTER TABLE bookings_bookingcomment ADD COLUMN IF NOT EXISTS content TEXT;",
            
            # Add missing columns to vendors_vendor
            "ALTER TABLE vendors_vendor ADD COLUMN IF NOT EXISTS vendor_name VARCHAR(200);",
            "ALTER TABLE vendors_vendor ADD COLUMN IF NOT EXISTS website VARCHAR(200);",
            "ALTER TABLE vendors_vendor ADD COLUMN IF NOT EXISTS rating DECIMAL(3,2);",
            "ALTER TABLE vendors_vendor ADD COLUMN IF NOT EXISTS notes TEXT;",
            
            # Add missing columns to vendors_purchaseorder
            "ALTER TABLE vendors_purchaseorder ADD COLUMN IF NOT EXISTS issue_date DATE;",
            "ALTER TABLE vendors_purchaseorder ADD COLUMN IF NOT EXISTS delivery_date DATE;",
            
            # Add missing columns to vendors_purchaseorderitem
            "ALTER TABLE vendors_purchaseorderitem ADD COLUMN IF NOT EXISTS notes TEXT;",
            "ALTER TABLE vendors_purchaseorderitem ADD COLUMN IF NOT EXISTS item_name VARCHAR(200);",
            
            # Add missing columns to vendors_vendorcommunication
            "ALTER TABLE vendors_vendorcommunication ADD COLUMN IF NOT EXISTS date DATE;",
        ]
        
        for sql in schema_fixes:
            try:
                cursor.execute(sql)
                print(f"✅ Executed: {sql[:50]}...")
            except Exception as e:
                print(f"❌ Error executing {sql[:50]}...: {str(e)}")
        
        conn.commit()
        print("✅ Database schema fixes completed")
        
    except Exception as e:
        print(f"❌ Error fixing database schema: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def test_api_endpoints():
    """Test API endpoints after fixes"""
    print("\n🔍 Testing API endpoints...")
    
    try:
        from farms.models import Farm, SoilType, CropType
        from equipment.models import Equipment
        from inventory.models import InventoryItem
        from tasks.models import Task
        from bookings.models import Booking
        from vendors.models import Vendor
        
        # Test basic queries
        models_to_test = [
            (Farm, "Farms"),
            (SoilType, "Soil Types"),
            (CropType, "Crop Types"),
            (Equipment, "Equipment"),
            (InventoryItem, "Inventory Items"),
            (Task, "Tasks"),
            (Booking, "Bookings"),
            (Vendor, "Vendors"),
        ]
        
        for model, name in models_to_test:
            try:
                count = model.objects.count()
                print(f"✅ {name}: {count} records")
            except Exception as e:
                print(f"❌ {name}: Error - {str(e)}")
        
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")

if __name__ == "__main__":
    print("🔧 Comprehensive database schema fix...")
    fix_database_schema()
    
    print("\n🔍 Testing API endpoints...")
    test_api_endpoints()
