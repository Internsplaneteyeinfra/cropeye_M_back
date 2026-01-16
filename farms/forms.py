from django import forms
from django.contrib.admin.widgets import AdminDateWidget
from .models import Farm, CropType, FarmIrrigation

# ==============================
# FARM ADMIN FORM
# ==============================
class FarmAdminForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = '__all__'
        labels = {
            'crop_variety': 'Variety',
        }
        widgets = {
            'crop_variety': forms.TextInput(attrs={
                'placeholder': 'Enter crop variety (e.g., Co 86032, Co 8371)',
            }),
            # ✅ Admin calendar widgets
            'plantation_date': AdminDateWidget(),
            'foundation_pruning_date': AdminDateWidget(),
            'fruit_pruning_date': AdminDateWidget(),
            'last_harvesting_date': AdminDateWidget(),
        }
class FarmAdminForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = '__all__'
        widgets = {
            'crop_variety': forms.TextInput(attrs={'placeholder': 'Enter crop variety'}),
            'plantation_date': AdminDateWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        crop_category = None
        if self.instance and self.instance.crop_type:
            crop_category = self.instance.crop_type.crop_category
        else:
            crop_category = 'sugarcane'  # default

        # Hide fields that might not be needed by default
        for field in ['plantation_type', 'plantation_method']:
            if field in self.fields:
                self.fields[field].widget = forms.HiddenInput()

        # Crop variety should ALWAYS be visible
        if 'crop_variety' in self.fields:
            self.fields['crop_variety'].widget = forms.TextInput(
                attrs={'placeholder': 'Enter crop variety'}
            )

        if crop_category == 'grapes':
            # Grapes → show plantation_type
            if 'plantation_type' in self.fields:
                self.fields['plantation_type'].widget = forms.Select(
                    choices=CropType.GRAPES_PLANTATION_TYPE_CHOICES
                )
        else:  # sugarcane
            # Sugarcane → show plantation_type + plantation_method
            if 'plantation_type' in self.fields:
                self.fields['plantation_type'].widget = forms.Select(
                    choices=CropType.SUGARCANE_PLANTATION_TYPE_CHOICES
                )
            if 'plantation_method' in self.fields:
                self.fields['plantation_method'].widget = forms.Select(
                    choices=CropType.SUGARCANE_PLANTATION_METHOD_CHOICES
                )



# ==============================
# FARM IRRIGATION ADMIN FORM
# ==============================
class FarmIrrigationAdminForm(forms.ModelForm):
    plantation_date = forms.DateField(
        required=False,
        widget=AdminDateWidget()
    )
    foundation_pruning_date = forms.DateField(
        required=False,
        widget=AdminDateWidget()
    )
    fruit_pruning_date = forms.DateField(
        required=False,
        widget=AdminDateWidget()
    )
    last_harvesting_date = forms.DateField(
        required=False,
        widget=AdminDateWidget()
    )

    class Meta:
        model = FarmIrrigation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, 'farm', None):
            self.fields['plantation_date'].initial = self.instance.farm.plantation_date
            self.fields['foundation_pruning_date'].initial = self.instance.farm.foundation_pruning_date
            self.fields['fruit_pruning_date'].initial = self.instance.farm.fruit_pruning_date
            self.fields['last_harvesting_date'].initial = self.instance.farm.last_harvesting_date

    def save(self, commit=True):
        irrigation = super().save(commit=False)
        if irrigation.farm:
            farm = irrigation.farm
            farm.plantation_date = self.cleaned_data.get('plantation_date')
            farm.foundation_pruning_date = self.cleaned_data.get('foundation_pruning_date')
            farm.fruit_pruning_date = self.cleaned_data.get('fruit_pruning_date')
            farm.last_harvesting_date = self.cleaned_data.get('last_harvesting_date')
            farm.save()
        if commit:
            irrigation.save()
        return irrigation
    class Media:
        css = {
            'all': ('admin/css/widgets.css',)
        }
        js = (
            'admin/js/core.js',
            'admin/js/vendor/jquery/jquery.js',
            'admin/js/jquery.init.js',
            'admin/js/actions.js',
            'admin/js/calendar.js',
            'admin/js/admin/DateTimeShortcuts.js',
        )