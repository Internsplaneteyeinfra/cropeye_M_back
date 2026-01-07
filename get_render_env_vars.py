#!/usr/bin/env python3
"""
Script to help you get environment variables for Render deployment.
Run this script and it will generate the environment variables you need to set in Render.
"""

import secrets
import string

def generate_secret_key():
    """Generate a secure Django secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(50))

def main():
    print("🔧 Render Environment Variables Generator")
    print("=" * 50)
    print()
    
    print("📋 Copy these environment variables to your Render web service:")
    print()
    
    # Django Configuration
    print("# Django Configuration")
    print(f"DEBUG=False")
    print(f"SECRET_KEY={generate_secret_key()}")
    print(f"DJANGO_SETTINGS_MODULE=farm_management.settings_production")
    print(f"ALLOWED_HOSTS=*.onrender.com,localhost,127.0.0.1")
    print(f"CORS_ALLOWED_ORIGINS=https://*.onrender.com,http://localhost:3000")
    print()
    
    # Database Configuration (you'll need to fill these in)
    print("# Database Configuration (fill in with your actual values)")
    print("DB_NAME=farm_management")
    print("DB_USER=postgres")
    print("DB_PASSWORD=<your-database-password>")
    print("DB_HOST=<your-database-host>")
    print("DB_PORT=<your-database-port>")
    print()
    
    # Redis Configuration (you'll need to fill these in)
    print("# Redis Configuration (fill in with your actual values)")
    print("REDIS_URL=<your-redis-connection-string>")
    print("CELERY_BROKER_URL=<your-redis-connection-string>")
    print("CELERY_RESULT_BACKEND=<your-redis-connection-string>")
    print()
    
    # Email Configuration (optional)
    print("# Email Configuration (optional)")
    print("EMAIL_HOST=smtp.gmail.com")
    print("EMAIL_PORT=587")
    print("EMAIL_USE_TLS=True")
    print("EMAIL_HOST_USER=<your-email>")
    print("EMAIL_HOST_PASSWORD=<your-app-password>")
    print()
    
    # Frontend URL
    print("# Frontend URL (update when you deploy frontend)")
    print("FRONTEND_URL=https://your-frontend-app.onrender.com")
    print()
    
    print("📝 Instructions:")
    print("1. Create PostgreSQL database on Render")
    print("2. Create Redis cache on Render")
    print("3. Create Web Service on Render")
    print("4. Copy the above environment variables to your web service")
    print("5. Replace <your-*> placeholders with actual values from your services")
    print("6. Deploy!")
    print()
    print("🔗 For detailed instructions, see MANUAL_RENDER_DEPLOYMENT.md")

if __name__ == "__main__":
    main()
