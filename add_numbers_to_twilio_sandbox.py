#!/usr/bin/env python3
"""
Script to help add phone numbers to Twilio WhatsApp sandbox
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def get_indian_phone_numbers():
    """Get all Indian phone numbers from the database"""
    
    print("🇮🇳 Getting Indian Phone Numbers for Twilio Sandbox")
    print("=" * 60)
    
    # Get all users with Indian phone numbers
    indian_users = User.objects.filter(phone_number__startswith='+91')
    
    print(f"📱 Found {indian_users.count()} users with Indian phone numbers")
    print("\n📋 Phone numbers to add to Twilio sandbox:")
    print("-" * 50)
    
    phone_numbers = []
    for user in indian_users:
        phone_numbers.append(user.phone_number)
        print(f"  - {user.phone_number} ({user.username})")
    
    return phone_numbers

def show_twilio_sandbox_instructions():
    """Show instructions for adding numbers to Twilio sandbox"""
    
    print("\n🔧 How to Add Numbers to Twilio Sandbox:")
    print("=" * 50)
    
    instructions = """
1. 📱 Go to Twilio WhatsApp Sandbox:
   https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn

2. 🔍 Find your sandbox number (should be +14155238886)

3. 📝 Add each phone number:
   - Click "Add a phone number"
   - Enter the phone number (e.g., +919146579454)
   - Click "Add"

4. ✅ Verify the number:
   - Twilio will send a verification code
   - Enter the code to approve the number

5. 🧪 Test again:
   - The number will now receive WhatsApp OTPs
   - Still limited to 9 messages per day

📋 Numbers to add:
"""
    
    print(instructions)
    
    # Get phone numbers
    phone_numbers = get_indian_phone_numbers()
    
    print("\n📱 Copy these numbers to add to Twilio sandbox:")
    print("-" * 40)
    for phone in phone_numbers:
        print(f"  {phone}")
    
    print(f"\n📊 Total numbers to add: {len(phone_numbers)}")
    
    return phone_numbers

def create_whatsapp_test_script():
    """Create a script to test WhatsApp OTP for specific numbers"""
    
    script_content = '''#!/usr/bin/env python3
"""
Test WhatsApp OTP for specific users
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farm_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.whatsapp_service import WhatsAppOTPService

User = get_user_model()

def test_whatsapp_otp(username):
    """Test WhatsApp OTP for a specific user"""
    
    try:
        user = User.objects.get(username=username)
        print(f"🧪 Testing WhatsApp OTP for: {user.username}")
        print(f"📱 Phone: {user.phone_number}")
        
        # Test WhatsApp service
        whatsapp_service = WhatsAppOTPService()
        result = whatsapp_service.send_otp_with_fallback(user, '123456')
        
        if result['success']:
            print(f"✅ OTP sent successfully via {result['method']}!")
            if result['method'] == 'whatsapp':
                print("🎉 WhatsApp OTP is working!")
            else:
                print("📧 Email fallback was used.")
        else:
            print(f"❌ OTP sending failed: {result.get('error', 'Unknown error')}")
            
    except User.DoesNotExist:
        print(f"❌ User '{username}' not found")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        username = sys.argv[1]
        test_whatsapp_otp(username)
    else:
        print("Usage: python test_whatsapp_user.py <username>")
        print("Example: python test_whatsapp_user.py Snidha")
'''
    
    with open('test_whatsapp_user.py', 'w') as f:
        f.write(script_content)
    
    print("\n📝 Created test script: test_whatsapp_user.py")
    print("Usage: python test_whatsapp_user.py <username>")

def main():
    """Main function"""
    
    print("🔧 Twilio Sandbox Number Addition Helper")
    print("=" * 50)
    
    # Show instructions
    phone_numbers = show_twilio_sandbox_instructions()
    
    # Create test script
    create_whatsapp_test_script()
    
    print("\n🎯 Next Steps:")
    print("1. Add the numbers above to your Twilio sandbox")
    print("2. Test with: python test_whatsapp_user.py Snidha")
    print("3. Check if WhatsApp OTP works for that user")
    
    print("\n⚠️  Remember:")
    print("- Sandbox is limited to 9 messages per day")
    print("- Only approved numbers will receive WhatsApp OTP")
    print("- Other numbers will get email fallback (which is fine!)")

if __name__ == "__main__":
    main()
