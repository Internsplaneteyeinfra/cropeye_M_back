from django import forms
from .models import Farm, CropType

class FarmAdminForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Determine crop category from the related CropType
        crop_category = None
        if self.instance and self.instance.crop_type:
            crop_category = self.instance.crop_type.crop_category
        else:
            crop_category = 'sugarcane'  # default if none selected

        # Set plantation_type choices dynamically
        if crop_category == 'grapes':
            self.fields['plantation_type'].choices = CropType.GRAPES_PLANTATION_TYPE_CHOICES
            # Hide planting method for grapes
            self.fields['planting_method'].widget = forms.HiddenInput()
        else:
            self.fields['plantation_type'].choices = CropType.SUGARCANE_PLANTATION_TYPE_CHOICES
            self.fields['planting_method'].choices = CropType.SUGARCANE_PLANTATION_METHOD_CHOICES
