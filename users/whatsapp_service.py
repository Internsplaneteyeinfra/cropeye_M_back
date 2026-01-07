"""
WhatsApp OTP Service for Farm Management Backend
"""

from twilio.rest import Client
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

class WhatsAppOTPService:
    """WhatsApp OTP sending service using Twilio"""
    
    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        self.whatsapp_number = settings.TWILIO_WHATSAPP_NUMBER
    
    def send_otp(self, phone_number, otp_code, user_name=None):
        """
        Send OTP via WhatsApp
        
        Args:
            phone_number (str): User's phone number (with country code)
            otp_code (str): 6-digit OTP code
            user_name (str): User's name for personalization
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Format phone number for WhatsApp
            if not phone_number.startswith('whatsapp:'):
                phone_number = f'whatsapp:{phone_number}'
            
            # Create personalized message
            name_part = f"Hi {user_name}!" if user_name else "Hi!"
            message_body = f"""{name_part}

Your OTP for Farm Management System login is: *{otp_code}*

This OTP will expire in 10 minutes.

Please do not share this code with anyone.

Thank you for using our services! 🌾"""
            
            # Send WhatsApp message
            message = self.client.messages.create(
                body=message_body,
                from_=self.whatsapp_number,
                to=phone_number
            )
            
            logger.info(f"WhatsApp OTP sent successfully to {phone_number}. Message SID: {message.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp OTP to {phone_number}: {str(e)}")
            return False
    
    def send_otp_with_fallback(self, user, otp_code):
        """
        Send OTP via WhatsApp with email fallback
        
        Args:
            user: Django User object
            otp_code (str): 6-digit OTP code
        
        Returns:
            dict: Result with success status and method used
        """
        result = {
            'success': False,
            'method': None,
            'error': None
        }
        
        # Try WhatsApp first if enabled
        if getattr(settings, 'WHATSAPP_OTP_ENABLED', False) and user.phone_number:
            whatsapp_success = self.send_otp(
                phone_number=user.phone_number,
                otp_code=otp_code,
                user_name=user.first_name or user.username
            )
            
            if whatsapp_success:
                result['success'] = True
                result['method'] = 'whatsapp'
                return result
        
        # Fallback to email if WhatsApp fails or is disabled
        if getattr(settings, 'EMAIL_OTP_FALLBACK', True) and user.email:
            try:
                send_mail(
                    'Your OTP for Farm Management System',
                    f'Your OTP is: {otp_code}. Expires in 10 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
                result['success'] = True
                result['method'] = 'email'
                logger.info(f"Email OTP sent as fallback to {user.email}")
            except Exception as e:
                result['error'] = f"Email fallback failed: {str(e)}"
                logger.error(f"Email OTP fallback failed: {str(e)}")
        
        return result

class GupshupWhatsAppService:
    """Alternative WhatsApp service using Gupshup API"""
    
    def __init__(self):
        self.api_key = settings.GUPSHUP_API_KEY
        self.app_name = settings.GUPSHUP_APP_NAME
        self.base_url = "https://api.gupshup.io/wa/api/v1"
    
    def send_otp(self, phone_number, otp_code, user_name=None):
        """
        Send OTP via Gupshup WhatsApp API
        
        Args:
            phone_number (str): User's phone number (with country code)
            otp_code (str): 6-digit OTP code
            user_name (str): User's name for personalization
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            import requests
            
            # Remove + from phone number for Gupshup
            if phone_number.startswith('+'):
                phone_number = phone_number[1:]
            
            # Create message
            name_part = f"Hi {user_name}!" if user_name else "Hi!"
            message = f"""{name_part}

Your OTP for Farm Management System login is: *{otp_code}*

This OTP will expire in 10 minutes.

Please do not share this code with anyone.

Thank you for using our services! 🌾"""
            
            # Send message via Gupshup
            url = f"{self.base_url}/msg"
            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'channel': 'whatsapp',
                'source': self.app_name,
                'destination': phone_number,
                'message': message,
                'src.name': 'FarmManagement'
            }
            
            response = requests.post(url, headers=headers, data=data)
            
            if response.status_code == 200:
                logger.info(f"Gupshup WhatsApp OTP sent successfully to {phone_number}")
                return True
            else:
                logger.error(f"Gupshup WhatsApp OTP failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Gupshup WhatsApp OTP to {phone_number}: {str(e)}")
            return False
