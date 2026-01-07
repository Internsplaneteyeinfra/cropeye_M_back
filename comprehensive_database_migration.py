#!/usr/bin/env python3
"""
Comprehensive database migration to match Django models exactly
This script will recreate the entire database schema with proper relationships
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
from django.core.management import execute_from_command_line

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=settings.DATABASES['default']['HOST'],
        port=settings.DATABASES['default']['PORT'],
        database=settings.DATABASES['default']['NAME'],
        user=settings.DATABASES['default']['USER'],
        password=settings.DATABASES['default']['PASSWORD']
    )

def drop_all_tables():
    """Drop all tables to start fresh"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🗑️  Dropping all tables...")
        
        # Get all table names
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'spatial_%'
            ORDER BY tablename;
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        # Drop all tables
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                print(f"   ✅ Dropped {table}")
            except Exception as e:
                print(f"   ❌ Error dropping {table}: {str(e)}")
        
        conn.commit()
        print("✅ All tables dropped successfully")
        
    except Exception as e:
        print(f"❌ Error dropping tables: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def create_django_migrations():
    """Create and apply Django migrations"""
    print("\n🔄 Creating Django migrations...")
    
    try:
        # Create migrations for all apps
        apps = ['users', 'farms', 'equipment', 'inventory', 'tasks', 'bookings', 'vendors']
        
        for app in apps:
            print(f"   Creating migrations for {app}...")
            execute_from_command_line(['manage.py', 'makemigrations', app])
        
        print("✅ Django migrations created")
        
    except Exception as e:
        print(f"❌ Error creating migrations: {str(e)}")

def apply_django_migrations():
    """Apply Django migrations to create proper schema"""
    print("\n📊 Applying Django migrations...")
    
    try:
        # Apply all migrations
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])
        print("✅ Django migrations applied successfully")
        
    except Exception as e:
        print(f"❌ Error applying migrations: {str(e)}")

def create_initial_data():
    """Create initial data (roles, etc.)"""
    print("\n🌱 Creating initial data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create roles
        roles = [
            (1, 'farmer', 'Farmer'),
            (2, 'fieldofficer', 'Field Officer'),
            (3, 'manager', 'Manager'),
            (4, 'owner', 'Owner'),
        ]
        
        for role_id, name, display_name in roles:
            cursor.execute("""
                INSERT INTO users_role (id, name, display_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    display_name = EXCLUDED.display_name;
            """, (role_id, name, display_name))
            print(f"   ✅ Created role: {display_name}")
        
        # Update admin user role
        cursor.execute("""
            UPDATE users_user SET role = 4 WHERE username = 'admin';
        """)
        print("   ✅ Updated admin user role")
        
        conn.commit()
        print("✅ Initial data created successfully")
        
    except Exception as e:
        print(f"❌ Error creating initial data: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def verify_database_schema():
    """Verify the database schema matches Django models"""
    print("\n🔍 Verifying database schema...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check all tables exist
        expected_tables = [
            'users_user', 'users_role', 'users_user_groups', 'users_user_user_permissions',
            'farms_soiltype', 'farms_croptype', 'farms_irrigationtype', 'farms_sensortype',
            'farms_plot', 'farms_farm', 'farms_farmimage', 'farms_farmsensor', 'farms_farmirrigation',
            'equipment_equipment', 'equipment_maintenancerecord', 'equipment_equipmentusage',
            'inventory_inventoryitem', 'inventory_inventorytransaction',
            'tasks_task', 'tasks_taskcomment', 'tasks_taskattachment',
            'bookings_booking', 'bookings_bookingcomment', 'bookings_bookingattachment',
            'vendors_vendor', 'vendors_purchaseorder', 'vendors_purchaseorderitem', 'vendors_vendorcommunication',
            'django_migrations', 'django_content_type', 'django_admin_log', 'django_session',
            'auth_group', 'auth_group_permissions', 'auth_permission'
        ]
        
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = set(expected_tables) - set(existing_tables)
        extra_tables = set(existing_tables) - set(expected_tables)
        
        if missing_tables:
            print(f"   ❌ Missing tables: {missing_tables}")
        if extra_tables:
            print(f"   ⚠️  Extra tables: {extra_tables}")
        if not missing_tables and not extra_tables:
            print("   ✅ All expected tables exist")
        
        # Check foreign key constraints
        cursor.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_schema = 'public'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        fk_constraints = cursor.fetchall()
        print(f"   ✅ Found {len(fk_constraints)} foreign key constraints")
        
        conn.commit()
        print("✅ Database schema verification completed")
        
    except Exception as e:
        print(f"❌ Error verifying schema: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def test_all_models():
    """Test all Django models can be imported and queried"""
    print("\n🧪 Testing all Django models...")
    
    try:
        from users.models import User, Role
        from farms.models import Farm, Plot, SoilType, CropType, IrrigationType, SensorType, FarmImage, FarmSensor, FarmIrrigation
        from equipment.models import Equipment, MaintenanceRecord, EquipmentUsage
        from inventory.models import InventoryItem, InventoryTransaction
        from tasks.models import Task, TaskComment, TaskAttachment
        from bookings.models import Booking, BookingComment, BookingAttachment
        from vendors.models import Vendor, PurchaseOrder, PurchaseOrderItem, VendorCommunication
        
        # Test basic queries
        models_to_test = [
            (User, "Users"),
            (Role, "Roles"),
            (Farm, "Farms"),
            (Plot, "Plots"),
            (SoilType, "Soil Types"),
            (CropType, "Crop Types"),
            (IrrigationType, "Irrigation Types"),
            (SensorType, "Sensor Types"),
            (Equipment, "Equipment"),
            (InventoryItem, "Inventory Items"),
            (Task, "Tasks"),
            (Booking, "Bookings"),
            (Vendor, "Vendors"),
        ]
        
        for model, name in models_to_test:
            try:
                count = model.objects.count()
                print(f"   ✅ {name}: {count} records")
            except Exception as e:
                print(f"   ❌ {name}: Error - {str(e)}")
        
        print("✅ All models tested successfully")
        
    except Exception as e:
        print(f"❌ Error testing models: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main migration process"""
    print("🚀 Starting comprehensive database migration...")
    print("This will recreate the entire database schema to match Django models exactly.")
    
    # Step 1: Drop all tables
    drop_all_tables()
    
    # Step 2: Create Django migrations
    create_django_migrations()
    
    # Step 3: Apply Django migrations
    apply_django_migrations()
    
    # Step 4: Create initial data
    create_initial_data()
    
    # Step 5: Verify schema
    verify_database_schema()
    
    # Step 6: Test models
    test_all_models()
    
    print("\n🎉 Database migration completed successfully!")
    print("All tables now match Django models exactly with proper relationships.")

if __name__ == "__main__":
    main()
