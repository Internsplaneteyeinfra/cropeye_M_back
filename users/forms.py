from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(required=False, empty_value='')

    class Meta:
        model = User
        fields = (
            'phone_number',
            'email',
            'first_name',
            'last_name',
            'username',
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

    def clean_username(self):
        # ALWAYS return a string
        return self.cleaned_data.get('username') or ''


class CustomUserChangeForm(UserChangeForm):
    username = forms.CharField(required=False, empty_value='')

    class Meta:
        model = User
        fields = (
            'phone_number',
            'email',
            'first_name',
            'last_name',
            'username',
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

    def clean_username(self):
        return self.cleaned_data.get('username') or ''
