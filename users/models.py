from django.contrib.auth.models import AbstractUser
from django.db import models
import re
from django.core.validators import RegexValidator, EmailValidator

# ==================== Industry Model ====================
class Industry(models.Model):
    """
    Industry model for multi-tenant isolation.
    Each industry has its own Industry Admin (Owner) and users.
    """
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    test_phone_number = models.CharField(
        max_length=15, blank=True, null=True,
        help_text="Test phone number for this industry (for testing purposes)"
    )
    test_password = models.CharField(
        max_length=128, blank=True, null=True,
        help_text="Test password for this industry (for testing purposes)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Industry"
        verbose_name_plural = "Industries"
        ordering = ['name']
    
    def __str__(self):
        return self.name


# ==================== Role Model ====================
class Role(models.Model):
    """
    A database-backed Role. You can assign any number of Django Permissions to it.
    """
    name = models.CharField(max_length=50, unique=True)
    display_name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return self.display_name or self.name


# ==================== User Model ====================
class User(AbstractUser):
    # Username for login
    username = models.CharField(
        max_length=150, unique=True,
        help_text="Required. Letters, digits and @/./+/-/_ only."
    )
    
    # Multi-tenant: Role & Industry
    role = models.ForeignKey(
        Role, null=True, blank=True, on_delete=models.SET_NULL, related_name='users', db_column='role'
    )
    industry = models.ForeignKey(
        Industry, null=True, blank=True, on_delete=models.SET_NULL, related_name='users'
    )
    
    created_by = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_users'
    )

    # ==================== Core Fields ====================
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    phone_number = models.CharField(
        max_length=15, unique=True, blank=True, null=True,
        help_text="Phone number (10 digits for India)"
    )
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(
    upload_to='profile_pics/',
    null=True,
    blank=True,
    help_text="Optional user profile picture"
)


    # Hardcoded dropdowns
    STATE_CHOICES = [
        ('Maharashtra', 'Maharashtra'),
        ('Karnataka', 'Karnataka'),
        ('Tamil Nadu', 'Tamil Nadu'),
    ]
    DISTRICT_CHOICES = [
        ('Pune', 'Pune'),
        ('Mumbai', 'Mumbai'),
        ('Bangalore', 'Bangalore'),
    ]
    TALUKA_CHOICES = [
        ('Haveli', 'Haveli'),
        ('Andheri', 'Andheri'),
        ('Whitefield', 'Whitefield'),
    ]
    state = models.CharField(max_length=50, choices=STATE_CHOICES, blank=True)
    district = models.CharField(max_length=50, choices=DISTRICT_CHOICES, blank=True)
    taluka = models.CharField(max_length=50, choices=TALUKA_CHOICES, blank=True)
    village = models.CharField(max_length=255, blank=True, null=True, help_text="Optional: user's village")

    # ==================== Password Reset Fields ====================
    password_reset_token = models.CharField(max_length=100, null=True, blank=True)
    password_reset_token_created_at = models.DateTimeField(null=True, blank=True)

    # ==================== Timestamps ====================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ==================== User Config ====================
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        role = self.role.name if self.role else "NoRole"
        identifier = self.username or self.phone_number or self.email or "Unknown"
        return f"{identifier} ({role})"

    # ==================== Role Helpers ====================
    def has_role(self, role_name: str) -> bool:
        return bool(self.role and self.role.name == role_name)

    def has_any_role(self, role_names: list[str]) -> bool:
        return bool(self.role and self.role.name in role_names)

    # ==================== Phone Helpers ====================
    def get_phone_number_with_country_code(self):
        if self.phone_number:
            return f"+91{self.phone_number}"
        return None
    
    @property
    def phone_number_formatted(self):
        return self.get_phone_number_with_country_code()

    