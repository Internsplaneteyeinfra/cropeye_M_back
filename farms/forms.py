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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        crop_category = None
        if self.instance and self.instance.crop_type:
            crop_category = self.instance.crop_type.crop_category
        else:
            crop_category = 'sugarcane'

        if crop_category == 'grapes':
            self.fields['plantation_type'].choices = CropType.GRAPES_PLANTATION_TYPE_CHOICES
            self.fields['planting_method'].widget = forms.HiddenInput()
            self.fields['crop_variety'].widget = forms.TextInput()
        else:
            self.fields['plantation_type'].choices = CropType.SUGARCANE_PLANTATION_TYPE_CHOICES
            self.fields['planting_method'].choices = CropType.SUGARCANE_PLANTATION_METHOD_CHOICES
            self.fields['crop_variety'].widget = forms.HiddenInput()


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