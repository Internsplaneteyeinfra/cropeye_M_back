#!/usr/bin/env python
"""
Clear all tables and migration records from hosted PostgreSQL database.
This will give us a completely clean slate to work with.
"""

import os
import sys
import django
from dotenv import load_dotenv
from django.db import connection

def clear_hosted_database():
    """Clear all tables and migration records from the hosted database."""
    print("🗑️  Clearing hosted PostgreSQL database...")
    print("⚠️   This will remove ALL data and tables!")
    
    try:
        with connection.cursor() as cursor:
            # Get all table names
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'pg_%' 
                AND tablename NOT LIKE 'sql_%'
                ORDER BY tablename;
            """)
            tables = cursor.fetchall()
            
            if tables:
                print(f"📊 Found {len(tables)} tables to drop:")
                for table in tables:
                    print(f"  - {table[0]}")
                
                # Drop all tables (CASCADE to handle foreign key constraints)
                print("🗑️  Dropping all tables...")
                for table in tables:
                    table_name = table[0]
                    try:
                        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
                        print(f"  ✅ Dropped: {table_name}")
                    except Exception as e:
                        print(f"  ⚠️  Could not drop {table_name}: {e}")
                
                print("✅ All tables dropped successfully!")
            else:
                print("📊 Database is already empty - no tables to drop")
            
            # Also drop any sequences that might be left over
            print("🔄 Cleaning up sequences...")
            cursor.execute("""
                SELECT sequence_name FROM information_schema.sequences 
                WHERE sequence_schema = 'public';
            """)
            sequences = cursor.fetchall()
            
            for seq in sequences:
                try:
                    cursor.execute(f'DROP SEQUENCE IF EXISTS "{seq[0]}" CASCADE;')
                    print(f"  ✅ Dropped sequence: {seq[0]}")
                except Exception as e:
                    print(f"  ⚠️  Could not drop sequence {seq[0]}: {e}")
            
            # Drop any views
            print("🔄 Cleaning up views...")
            cursor.execute("""
                SELECT viewname FROM pg_views 
                WHERE schemaname = 'public';
            """)
            views = cursor.fetchall()
            
            for view in views:
                try:
                    cursor.execute(f'DROP VIEW IF EXISTS "{view[0]}" CASCADE;')
                    print(f"  ✅ Dropped view: {view[0]}")
                except Exception as e:
                    print(f"  ⚠️  Could not drop view {view[0]}: {e}")
            
            print("🎉 Hosted PostgreSQL database completely cleared!")
            print("🔄 Database is now ready for fresh migrations")
            
            return True
            
    except Exception as e:
        print(f"❌ Database clearing failed: {e}")
        return False

if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
    
    # Verify we're connecting to the hosted database
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME', 'unknown')
    
    print(f"🔍 Target Database:")
    print(f"  Host: {db_host}")
    print(f"  Database: {db_name}")
    
    if 'render.com' not in db_host:
        print("⚠️  WARNING: This doesn't appear to be the hosted database!")
        print("   Make sure your .env file has the hosted PostgreSQL credentials")
        sys.exit(1)
    
    print("✅ Confirmed: Targeting hosted PostgreSQL database")
    print("")
    
    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')
    django.setup()
    
    success = clear_hosted_database()
    if not success:
        print("💥 Database clearing failed!")
        sys.exit(1)
    else:
        print("🎉 Database clearing successful!")
