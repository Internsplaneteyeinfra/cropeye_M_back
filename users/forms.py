from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """User creation form with phone_number as identifier (no username)."""

    class Meta:
        model = User
        fields = (
            'phone_number',
            'email',
            'first_name',
            'last_name',
            'address',
            'profile_picture',
            'state',
            'district',
            'taluka',
            'village',
            'role',
            'industry',
            'created_by',
            'is_active',
            'is_staff',
            'is_superuser',
        )

    def save(self, commit=True):
        user = User.objects.create_user(
            phone_number=self.cleaned_data['phone_number'],
            email=self.cleaned_data.get('email'),
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
            address=self.cleaned_data.get('address', ''),
            state=self.cleaned_data.get('state', ''),
            district=self.cleaned_data.get('district', ''),
            taluka=self.cleaned_data.get('taluka', ''),
            village=self.cleaned_data.get('village', ''),
            role=self.cleaned_data.get('role'),
            industry=self.cleaned_data.get('industry'),
            created_by=self.cleaned_data.get('created_by'),
            is_active=self.cleaned_data.get('is_active', True),
            is_staff=self.cleaned_data.get('is_staff', False),
            is_superuser=self.cleaned_data.get('is_superuser', False),
        )
        if self.cleaned_data.get('profile_picture'):
            user.profile_picture = self.cleaned_data['profile_picture']
            user.save(update_fields=['profile_picture'])
        return user


class CustomUserChangeForm(UserChangeForm):
    """User change form (no username)."""

    class Meta:
        model = User
        fields = (
            'phone_number',
            'email',
            'first_name',
            'last_name',
            'address',
            'profile_picture',
            'state',
            'district',
            'taluka',
            'village',
            'role',
            'industry',
            'created_by',
            'is_active',
            'is_staff',
            'is_superuser',
        )
