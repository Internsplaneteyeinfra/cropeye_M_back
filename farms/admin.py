from django.contrib import admin
from django import forms
from leaflet.admin import LeafletGeoAdmin
from users.admin import IndustryFilteredAdmin
from .forms import FarmAdminForm
from .forms import FarmIrrigationAdminForm
from .models import Farm, FarmIrrigation

from .models import (
    SoilType,
    CropType,
    PlantationType,
    PlantingMethod,
    IrrigationType,
    SensorType,
    Plot,
    Farm,
    FarmImage,
    FarmSensor,
    FarmIrrigation,
)


@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


# Inline for PlantingMethod (child of PlantationType)
class PlantingMethodInline(admin.TabularInline):
    model = PlantingMethod
    extra = 0
    fields = ('name', 'code', 'description', 'is_active')
    show_change_link = True


# Inline for PlantationType (child of CropType)
class PlantationTypeInline(admin.TabularInline):
    model = PlantationType
    extra = 0
    fields = ('name', 'code', 'description', 'is_active')
    show_change_link = True


class CropTypeAdminForm(forms.ModelForm):
    """Custom form for CropType admin with JS-controlled dropdowns"""
    class Meta:
        model = CropType
        fields = '__all__'
        widgets = {
            'plantation_type': forms.Select(),
            'planting_method': forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plantation_type'].widget = forms.Select()
        self.fields['plantation_type'].required = False

        self.fields['planting_method'].widget = forms.Select()
        self.fields['planting_method'].required = False


@admin.register(CropType)
class CropTypeAdmin(IndustryFilteredAdmin):
    form = CropTypeAdminForm
    list_display = ('crop_category', 'industry', 'plantation_type_display', 'planting_method_display', 'plantation_date_display')
    list_filter = ('crop_category', 'industry', 'plantation_type', 'planting_method')
    search_fields = ('crop_category',)
    change_form_template = 'admin/farms/croptype/change_form.html'
    inlines = [PlantationTypeInline]

    fieldsets = (
        (None, {
            'fields': ('industry', 'crop_category')
        }),
        ('Plantation Details', {
            'fields': ('plantation_type', 'planting_method'),
        }),
    )

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
            'admin/js/croptype_dynamic_fields.js',  # keep your custom JS
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form

    def plantation_type_display(self, obj):
        if not obj.plantation_type:
            return '-'
        choices = obj.get_plantation_type_choices()
        return dict(choices).get(obj.plantation_type, obj.plantation_type)
    plantation_type_display.short_description = 'Plantation Type'
    plantation_type_display.admin_order_field = 'plantation_type'

    def planting_method_display(self, obj):
        if not obj.planting_method or obj.crop_category != 'sugarcane':
            return '-'
        return dict(CropType.SUGARCANE_PLANTATION_METHOD_CHOICES).get(obj.planting_method, obj.planting_method)
    planting_method_display.short_description = 'Planting Method'
    planting_method_display.admin_order_field = 'planting_method'

    def plantation_date_display(self, obj):
        most_recent_farm = obj.farm_set.filter(plantation_date__isnull=False).order_by('-plantation_date').first()
        if most_recent_farm:
            most_recent = most_recent_farm.plantation_date
            total_farms = obj.farm_set.count()
            if total_farms > 1:
                return f"{most_recent} (most recent of {total_farms} farms)"
            return str(most_recent)
        return '-'
    plantation_date_display.short_description = 'Plantation Date'


@admin.register(PlantationType)
class PlantationTypeAdmin(IndustryFilteredAdmin):
    list_display = ('name', 'crop_type', 'code', 'industry', 'is_active', 'created_at')
    list_filter = ('crop_type', 'industry', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description', 'crop_type__crop_category')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [PlantingMethodInline]
    change_form_template = 'admin/farms/plantationtype/change_form.html'

    fieldsets = (
        (None, {
            'fields': ('crop_type', 'industry', 'name', 'code', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(PlantingMethod)
class PlantingMethodAdmin(IndustryFilteredAdmin):
    list_display = ('name', 'plantation_type', 'code', 'industry', 'is_active', 'created_at')
    list_filter = ('plantation_type', 'industry', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description', 'plantation_type__name')
    readonly_fields = ('created_at', 'updated_at')
    change_form_template = 'admin/farms/plantingmethod/change_form.html'

    fieldsets = (
        (None, {
            'fields': ('plantation_type', 'industry', 'name', 'code', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(IrrigationType)
class IrrigationTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(SensorType)
class SensorTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class FarmImageInline(admin.TabularInline):
    model = FarmImage
    extra = 0
    fields = ('title', 'image', 'capture_date', 'uploaded_by')
    readonly_fields = ('uploaded_by',)


class FarmSensorInline(admin.TabularInline):
    model = FarmSensor
    extra = 0
    fields = ('name', 'sensor_type', 'installation_date', 'status')


class FarmIrrigationInline(admin.TabularInline):
    model = FarmIrrigation
    extra = 0
    fields = ('irrigation_type', 'status')


@admin.register(Farm)
class FarmAdmin(admin.ModelAdmin):
    form = FarmAdminForm  # <-- important

    list_display = (
        'farm_owner',
        'farm_uid',
        'industry',
        'area_size',
        'soil_type',
        'crop_type',
        'plantation_date',
        'get_created_by_email',
        'created_at',
    )
    list_filter = ('industry', 'soil_type', 'crop_type', 'created_at', 'created_by')
    search_fields = ('farm_owner__username', 'farm_uid', 'address', 'created_by__email', 'industry__name', 'crop_variety')
    readonly_fields = ('farm_uid', 'created_at', 'updated_at')

    inlines = [
        FarmIrrigationInline,
        FarmImageInline,
        FarmSensorInline,
    ]

    fieldsets = (
        (None, {
            'fields': (
                'farm_owner',
                'plot',
                'industry',
                'address',
                'area_size',
                'soil_type',
                'crop_type',
                'crop_variety',  # <-- now fully integrated
                'plantation_date',
                'farm_document',
            )
        }),
        ('Plantation Details', {
            'fields': ('spacing_a', 'spacing_b'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('farm_uid', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'industry') and request.user.industry:
            return qs.filter(industry=request.user.industry)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'industry') and not obj.industry:
            if hasattr(request.user, 'industry') and request.user.industry:
                obj.industry = request.user.industry
        super().save_model(request, obj, form, change)

    def get_created_by_email(self, obj):
        if obj.created_by:
            return obj.created_by.email
        return "No creator"
    get_created_by_email.short_description = 'Created By (Email)'
    get_created_by_email.admin_order_field = 'created_by__email'


@admin.register(Plot)
class PlotAdmin(LeafletGeoAdmin):
    list_display = (
        'gat_number',
        'plot_number',
        'industry',
        'village',
        'taluka',
        'district',
        'state',
        'country',
        'get_created_by_email',
    )
    list_filter = ('industry', 'village', 'taluka', 'district', 'state', 'country', 'created_by')
    search_fields = ('gat_number', 'plot_number', 'created_by__email', 'industry__name')

    fieldsets = (
        (None, {
            'fields': (
                'gat_number',
                'plot_number',
                'industry',
                'village',
                'taluka',
                'district',
                'state',
                'country',
                'pin_code',
            )
        }),
        ('Geo Data', {'fields': ('location', 'boundary')}),
        ('Metadata', {'fields': ('created_by',), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'industry') and request.user.industry:
            return qs.filter(industry=request.user.industry)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change and hasattr(obj, 'industry') and not obj.industry:
            if hasattr(request.user, 'industry') and request.user.industry:
                obj.industry = request.user.industry
        super().save_model(request, obj, form, change)

    def get_created_by_email(self, obj):
        if obj.created_by:
            return obj.created_by.email
        return "No creator"
    get_created_by_email.short_description = 'Created By (Email)'
    get_created_by_email.admin_order_field = 'created_by__email'


@admin.register(FarmImage)
class FarmImageAdmin(LeafletGeoAdmin):
    list_display = ('title', 'farm', 'capture_date', 'uploaded_by', 'uploaded_at')
    list_filter = ('farm', 'capture_date', 'uploaded_at')
    search_fields = ('title',)
    readonly_fields = ('uploaded_by', 'uploaded_at')

    fieldsets = (
        (None, {'fields': ('farm', 'title', 'image', 'capture_date', 'notes')}),
        ('Location', {'fields': ('location',)}),
        ('Metadata', {'fields': ('uploaded_by', 'uploaded_at')}),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(FarmSensor)
class FarmSensorAdmin(LeafletGeoAdmin):
    list_display = ('name', 'farm', 'sensor_type', 'installation_date', 'status')
    list_filter = ('farm', 'sensor_type', 'status', 'installation_date')
    search_fields = ('name',)

    fieldsets = (
        (None, {
            'fields': (
                'farm',
                'name',
                'sensor_type',
                'installation_date',
                'last_maintenance',
                'status',
            )
        }),
        ('Location', {'fields': ('location',)}),
    )


@admin.register(FarmIrrigation)
class FarmIrrigationAdmin(LeafletGeoAdmin):
    form = FarmIrrigationAdminForm
    list_display = (
        'farm',
        'irrigation_type',
        'status',
        'plantation_date_display',  # method, not field
        'last_harvesting_date_display',  # method, not field
    )

    list_filter = ('farm', 'irrigation_type', 'status')
    search_fields = ('farm__farm_owner__username',)

    # Make fields editable to show calendar
    fieldsets = (
        ('Irrigation Details', {
            'fields': (
                'farm',
                'irrigation_type',
                'status',
                'motor_horsepower',
                'pipe_width_inches',
                'distance_motor_to_plot_m',
                'plants_per_acre',
                'flow_rate_lph',
                'emitters_count',
            )
        }),
        ('Crop Dates (From Farm)', {
            'fields': (
                'plantation_date',
                'foundation_pruning_date',
                'fruit_pruning_date',
                'last_harvesting_date',
            )
        }),
        ('Geographic', {
            'fields': ('location',)
        }),
    )

    def plantation_date_display(self, obj):
        return obj.farm.plantation_date if obj.farm else None
    plantation_date_display.short_description = "Plantation Date"

    def last_harvesting_date_display(self, obj):
        return obj.farm.last_harvesting_date if obj.farm else None
    last_harvesting_date_display.short_description = "Last Harvesting Date"
