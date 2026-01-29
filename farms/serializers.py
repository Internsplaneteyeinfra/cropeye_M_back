from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework_gis.fields import GeometryField
from django.contrib.auth import get_user_model
import json
from django.contrib.gis.geos import Point
from .models import PlotFile



from .models import (
    SoilType,
    CropType,
    PlantationType,
    PlantingMethod,
    Farm,
    Plot,
    FarmImage,
    FarmSensor,
    FarmIrrigation,
    IrrigationType,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class SoilTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilType
        fields = ['id', 'name', 'description', 'properties']


class IrrigationTypeSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)
    
    class Meta:
        model = IrrigationType
        fields = ['id', 'name', 'name_display', 'description']


class PlantationTypeSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    crop_type_id = serializers.PrimaryKeyRelatedField(
        source='crop_type',
        queryset=CropType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = PlantationType
        fields = ['id', 'industry', 'industry_name', 'crop_type', 'crop_type_id', 'name', 'code', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'crop_type']


class PlantingMethodSerializer(serializers.ModelSerializer):
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    plantation_type_id = serializers.PrimaryKeyRelatedField(
        source='plantation_type',
        queryset=PlantationType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = PlantingMethod
        fields = ['id', 'industry', 'industry_name', 'plantation_type', 'plantation_type_id', 'name', 'code', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'plantation_type']


class CropTypeSerializer(serializers.ModelSerializer):
    # Plantation type and planting method are now CharField with choices
    plantation_type_display = serializers.SerializerMethodField()
    planting_method_display = serializers.SerializerMethodField()
    plantation_date = serializers.SerializerMethodField()
    industry_name = serializers.CharField(source='industry.name', read_only=True)
    crop_category = serializers.ChoiceField(choices=CropType.CROP_CATEGORY_CHOICES)
    plantation_type_choices = serializers.SerializerMethodField()
    planting_method_choices = serializers.SerializerMethodField()
    
    class Meta:
        model = CropType
        fields = [
            'id', 'crop_category', 'industry', 'industry_name', 
            'plantation_type', 'plantation_type_display', 'plantation_type_choices',
            'planting_method', 'planting_method_display', 'planting_method_choices',
            'plantation_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_plantation_type_display(self, obj):
        """Get human-readable plantation type based on crop category"""
        if not obj.plantation_type:
            return None
        choices = obj.get_plantation_type_choices()
        choices_dict = dict(choices)
        return choices_dict.get(obj.plantation_type, obj.plantation_type)
    
    def get_planting_method_display(self, obj):
        """Get human-readable planting method"""
        if not obj.planting_method:
            return None
        if obj.crop_category == 'sugarcane':
            choices_dict = dict(CropType.SUGARCANE_PLANTATION_METHOD_CHOICES)
            return choices_dict.get(obj.planting_method, obj.planting_method)
        return None
    
    def get_plantation_type_choices(self, obj):
        """Return available plantation type choices for the crop category"""
        return obj.get_plantation_type_choices() if obj.pk else CropType.get_plantation_type_choices_for_category(
            self.initial_data.get('crop_category', 'sugarcane') if hasattr(self, 'initial_data') else 'sugarcane'
        )
    
    def get_planting_method_choices(self, obj):
        """Return available planting method choices for the crop category"""
        return obj.get_planting_method_choices() if obj.pk else CropType.get_planting_method_choices_for_category(
            self.initial_data.get('crop_category', 'sugarcane') if hasattr(self, 'initial_data') else 'sugarcane'
        )
    
    def get_plantation_date(self, obj):
        # Get plantation_date from the parent Farm instance passed through context
        farm = self.context.get('farm')
        if farm and hasattr(farm, 'plantation_date'):
            return farm.plantation_date.isoformat() if farm.plantation_date else None
        return None
    
    def validate(self, data):
        """Validate plantation_type and planting_method based on crop_category"""
        crop_category = data.get('crop_category', self.instance.crop_category if self.instance else 'sugarcane')
        plantation_type = data.get('plantation_type')
        planting_method = data.get('planting_method')
        
        # Validate plantation_type
        if plantation_type:
            valid_choices = CropType.get_plantation_type_choices_for_category(crop_category)
            valid_values = [choice[0] for choice in valid_choices]
            if plantation_type not in valid_values:
                raise serializers.ValidationError({
                    'plantation_type': f'Invalid plantation type for {crop_category}. Valid choices: {[c[1] for c in valid_choices]}'
                })
        
        # Validate planting_method (only for sugarcane)
        if planting_method:
            if crop_category != 'sugarcane':
                raise serializers.ValidationError({
                    'planting_method': f'Planting method is only applicable for sugarcane crops'
                })
            valid_choices = CropType.get_planting_method_choices_for_category(crop_category)
            valid_values = [choice[0] for choice in valid_choices]
            if planting_method not in valid_values:
                raise serializers.ValidationError({
                    'planting_method': f'Invalid planting method. Valid choices: {[c[1] for c in valid_choices]}'
                })
        
        return data


class PlotSerializer(serializers.ModelSerializer):
    location = GeometryField(
        required=False,
        allow_null=True,
        help_text='Point geometry as GeoJSON: {"type": "Point", "coordinates": [longitude, latitude]}'
    )
    boundary = GeometryField(
        required=False,
        allow_null=True,
        help_text='Polygon geometry as GeoJSON: {"type": "Polygon", "coordinates": [[[lng, lat], ...]]}'
    )

    farmer = serializers.SerializerMethodField(read_only=True)
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Plot
        fields = [
            'id',
            'gat_number',
            'plot_number',
            'village',
            'taluka',
            'district',
            'state',
            'country',
            'pin_code',
            'location',
            'boundary',
            'farmer',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['farmer', 'created_by', 'created_at', 'updated_at']



    # Optional: Show farmer info
    def get_farmer(self, obj):
        return obj.farmer.username if obj.farmer else None

    def get_created_by(self, obj):
        return obj.created_by.username if obj.created_by else None

    # Validate location
    def validate_location(self, value):
        if value is not None:
            try:
                geojson_str = value if hasattr(value, 'geom_type') else value
                geom = GEOSGeometry(geojson_str) if not hasattr(value, 'geom_type') else value
                if geom.geom_type != 'Point':
                    raise serializers.ValidationError(f"Location must be a Point geometry, got {geom.geom_type}")
            except Exception as e:
                raise serializers.ValidationError(f"Invalid location geometry: {str(e)}")
        return value

    # Validate boundary
    def validate_boundary(self, value):
        if value is not None:
            try:
                geojson_str = value if hasattr(value, 'geom_type') else value
                geom = GEOSGeometry(geojson_str) if not hasattr(value, 'geom_type') else value
                if geom.geom_type != 'Polygon':
                    raise serializers.ValidationError(f"Boundary must be a Polygon geometry, got {geom.geom_type}")
            except Exception as e:
                raise serializers.ValidationError(f"Invalid boundary geometry: {str(e)}")
        return value

    # Validate uniqueness of plot
    def validate(self, attrs):
            farmer = self.context['request'].user if self.context['request'] else None

            gat = attrs.get('gat_number')
            plot = attrs.get('plot_number')
            village = attrs.get('village')
            taluka = attrs.get('taluka')
            district = attrs.get('district')

            # 🔹 Global check
            if Plot.objects.filter(
                gat_number=gat,
                plot_number=plot,
                village=village,
                taluka=taluka,
                district=district
            ).exists():
                raise serializers.ValidationError(
                    "This plot already exists globally."
                )

            # 🔹 Farmer-level check
            if farmer and Plot.objects.filter(
                farmer=farmer,
                gat_number=gat,
                plot_number=plot,
                village=village
            ).exists():
                raise serializers.ValidationError(
                    "This farmer already has this plot."
                )

            return attrs


class FarmImageSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = FarmImage
        fields = [
            'id',
            'farm',
            'title',
            'image',
            'capture_date',
            'notes',
            'uploaded_by',
            'uploaded_at',
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']

    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class FarmSensorSerializer(serializers.ModelSerializer):
    location = GeometryField(required=False, allow_null=True)

    class Meta:
        model = FarmSensor
        fields = [
            'id',
            'farm',
            'name',
            'sensor_type',
            'location',
            'installation_date',
            'last_maintenance',
            'status',
        ]


class FarmIrrigationSerializer(serializers.ModelSerializer):
    geographic = serializers.SerializerMethodField()
    location = GeometryField(write_only=True, required=True)

    flow_rate_liter_per_hour = serializers.FloatField(
        required=False,
        allow_null=True,
        source='flow_rate_lph'
    )
    emitters_per_plant = serializers.IntegerField(
        required=False,
        allow_null=True,
        source='emitters_count'
    )

    # Crop dates (write-only)
    plantation_date = serializers.DateTimeField(write_only=True, required=False, allow_null=True)
    foundation_pruning_date = serializers.DateTimeField(write_only=True, required=False, allow_null=True)
    fruit_pruning_date = serializers.DateTimeField(write_only=True, required=False, allow_null=True)
    last_harvesting_date = serializers.DateTimeField(write_only=True, required=False, allow_null=True)

    irrigation_type_name = serializers.CharField(source='irrigation_type.name', read_only=True)
    irrigation_type_display = serializers.CharField(source='irrigation_type.get_name_display', read_only=True)
    farm_uid = serializers.CharField(source='farm.farm_uid', read_only=True)

    class Meta:
        model = FarmIrrigation
        fields = [
            'id',
            'farm',
            'farm_uid',
            'irrigation_type',
            'irrigation_type_name',
            'irrigation_type_display',
            'status',
            'motor_horsepower',
            'pipe_width_inches',
            'distance_motor_to_plot_m',
            'plants_per_acre',

            
            'flow_rate_liter_per_hour',
            'emitters_per_plant',

            'location',
            'geographic',
            'plantation_date',
            'foundation_pruning_date',
            'fruit_pruning_date',
            'last_harvesting_date',
        ]

        read_only_fields = [
            'id',
            'farm_uid',
            'irrigation_type_name',
            'irrigation_type_display',
            'geographic',
        ]

    def get_geographic(self, obj):
        if obj.location:
            return {"type": "Point", "coordinates": [obj.location.x, obj.location.y]}
        return None

    def create(self, validated_data):
    # 1. Extract crop dates
        crop_dates = {}
        for field in [
            'plantation_date',
            'foundation_pruning_date',
            'fruit_pruning_date',
            'last_harvesting_date'
        ]:
            crop_dates[field] = validated_data.pop(field, None)

        # 2. Extract location (THIS IS THE FIX)
        location = validated_data.pop('location', None)

        if location is None:
            raise serializers.ValidationError({
                "location": "Location is required"
            })

        # 3. Create object with location
        instance = FarmIrrigation.objects.create(
            location=location,
            **validated_data
        )

        # 4. Save crop dates
        for field, value in crop_dates.items():
            setattr(instance, field, value)

        instance.save()
        return instance


class FarmWithIrrigationSerializer(serializers.ModelSerializer):
    """Serializer for creating farms with irrigation in a single request"""
    farm_owner = UserSerializer(read_only=True)
    farm_owner_id = serializers.PrimaryKeyRelatedField(
        source='farm_owner',
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    created_by = UserSerializer(read_only=True)

    soil_type = SoilTypeSerializer(read_only=True)
    soil_type_id = serializers.PrimaryKeyRelatedField(
        source='soil_type',
        queryset=SoilType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    crop_type = CropTypeSerializer(read_only=True)
    crop_type_id = serializers.PrimaryKeyRelatedField(
        source='crop_type',
        queryset=CropType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    plot = PlotSerializer(read_only=True)
    plot_id = serializers.PrimaryKeyRelatedField(
        source='plot',
        queryset=Plot.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    
    # Irrigation fields
    irrigation_type = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
    )
    motor_horsepower = serializers.FloatField(write_only=True, required=False, allow_null=True)
    pipe_width_inches = serializers.FloatField(write_only=True, required=False, allow_null=True)
    distance_motor_to_plot_m = serializers.FloatField(write_only=True, required=False, allow_null=True)
    plants_per_acre = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    flow_rate_lph = serializers.FloatField(write_only=True, required=False, allow_null=True)
    emitters_count = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # Location fields
    location_lat = serializers.FloatField(write_only=True, required=False, allow_null=True)
    location_lng = serializers.FloatField(write_only=True, required=False, allow_null=True)
    boundary_geojson = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Spacing fields and calculated plants
    plants_in_field = serializers.ReadOnlyField()

    class Meta:
        model = Farm
        fields = [
            'id',
            'farm_uid',
            'farm_owner',
            'farm_owner_id',
            'created_by',
            'plot',
            'plot_id',
            'address',
            'area_size',
            'soil_type',
            'soil_type_id',
            'crop_type',
            'crop_type_id',
            'farm_document',
            'plantation_date',
            'created_at',
            'updated_at',
            'spacing_a',
            'spacing_b',
            'plants_in_field',
            # Irrigation fields
            'irrigation_type',
            'motor_horsepower',
            'pipe_width_inches',
            'distance_motor_to_plot_m',
            'plants_per_acre',
            'flow_rate_lph',
            'emitters_count',
 
            # Location fields
            'location_lat',
            'location_lng',
            'boundary_geojson',
        ]
        read_only_fields = ['farm_uid', 'farm_owner', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create farm and irrigation in a single transaction"""
        from django.db import transaction
        from django.contrib.gis.geos import Point, GEOSGeometry
        
        # Extract irrigation data
        irrigation_type_id = validated_data.pop('irrigation_type', None)
        irrigation_type = None
        if irrigation_type_id:
            try:
                irrigation_type = IrrigationType.objects.get(id=irrigation_type_id)
            except IrrigationType.DoesNotExist:
                raise serializers.ValidationError(f"Irrigation type with ID {irrigation_type_id} does not exist")
        
        irrigation_data = {
            'irrigation_type': irrigation_type,
            'motor_horsepower': validated_data.pop('motor_horsepower', None),
            'pipe_width_inches': validated_data.pop('pipe_width_inches', None),
            'distance_motor_to_plot_m': validated_data.pop('distance_motor_to_plot_m', None),
            'plants_per_acre': validated_data.pop('plants_per_acre', None),
            'flow_rate_lph': validated_data.pop('flow_rate_lph', None),
            'emitters_count': validated_data.pop('emitters_count', None),
        }
        
        # Extract location data
        location_lat = validated_data.pop('location_lat', None)
        location_lng = validated_data.pop('location_lng', None)
        boundary_geojson = validated_data.pop('boundary_geojson', None)
        
        with transaction.atomic():
            # Create the farm
            farm = super().create(validated_data)
            
            # Create irrigation if irrigation type is provided
            if irrigation_data['irrigation_type']:
                irrigation_location = None
                
                # Set irrigation location
                if location_lat and location_lng:
                    irrigation_location = Point(location_lng, location_lat, srid=4326)
                elif boundary_geojson:
                    try:
                        boundary_data = json.loads(boundary_geojson)
                        irrigation_location = GEOSGeometry(json.dumps(boundary_data))
                    except (json.JSONDecodeError, Exception):
                        irrigation_location = Point(0, 0, srid=4326)
                else:
                    irrigation_location = Point(0, 0, srid=4326)
                
                # Create irrigation
                FarmIrrigation.objects.create(
                    farm=farm,
                    irrigation_type=irrigation_data['irrigation_type'],
                    location=irrigation_location,
                    motor_horsepower=irrigation_data['motor_horsepower'],
                    pipe_width_inches=irrigation_data['pipe_width_inches'],
                    distance_motor_to_plot_m=irrigation_data['distance_motor_to_plot_m'],
                    plants_per_acre=irrigation_data['plants_per_acre'],
                    flow_rate_lph=irrigation_data['flow_rate_lph'],
                    emitters_count=irrigation_data['emitters_count'],
                )
        
        return farm
    
    def to_representation(self, instance):
        # Override to pass farm instance to CropTypeSerializer
        representation = super().to_representation(instance)
        if 'crop_type' in representation and instance.crop_type:
            # Pass farm instance to crop_type serializer context
            crop_type_serializer = CropTypeSerializer(
                instance.crop_type,
                context={'farm': instance, **self.context}
            )
            representation['crop_type'] = crop_type_serializer.data
        return representation

class FarmIrrigationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmIrrigation
        fields = [
            'id',
            'irrigation_type',
            'status',
            'motor_horsepower',
            'pipe_width_inches',
            'flow_rate_lph',
            'emitters_count',
            'distance_motor_to_plot_m',
        ]

class FarmSerializer(serializers.ModelSerializer):
    farm_owner = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)

    soil_type = SoilTypeSerializer(read_only=True)
    soil_type_id = serializers.PrimaryKeyRelatedField(
        source='soil_type',
        queryset=SoilType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    crop_type = CropTypeSerializer(read_only=True)
    crop_type_id = serializers.PrimaryKeyRelatedField(
        source='crop_type',
        queryset=CropType.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    plot = PlotSerializer(read_only=True)
    plot_id = serializers.PrimaryKeyRelatedField(
        source='plot',
        queryset=Plot.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    irrigations = FarmIrrigationSerializer(many=True, required=False)
    plants_in_field = serializers.ReadOnlyField()

    class Meta:
        model = Farm
        fields = [
            'id', 'farm_uid', 'industry', 'farm_owner', 'created_by', 'plot', 'plot_id',
            'address', 'area_size', 'soil_type', 'soil_type_id', 'crop_type', 'crop_type_id',
            'farm_document', 'plantation_date', 'spacing_a', 'spacing_b', 'crop_variety',
            'variety_type', 'variety_subtype', 'variety_timing', 'plant_age',
            'foundation_pruning_date', 'fruit_pruning_date', 'last_harvesting_date',
            'resting_period_days', 'row_spacing', 'plant_spacing',
            'flow_rate_liter_per_hour', 'emitters_per_plant',
            'irrigations', 'plants_in_field', 'created_at', 'updated_at',
        ]
        read_only_fields = ['farm_uid', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        irrigations_data = validated_data.pop('irrigations', [])

        # Determine farm_owner based on role
        if hasattr(user, 'has_role') and user.has_role('farmer'):
            validated_data['farm_owner'] = user
        elif user.is_superuser:
            # Superuser can assign any farm_owner if provided
            farm_owner = validated_data.get('farm_owner')
            validated_data['farm_owner'] = farm_owner or user
        else:
            # Field officers or others: assign themselves as created_by
            validated_data.setdefault('farm_owner', user)

        validated_data.setdefault('created_by', user)
        validated_data.setdefault('industry', getattr(user, 'industry', None))

        farm = Farm.objects.create(**validated_data)

        for irrigation in irrigations_data:
            FarmIrrigation.objects.create(farm=farm, **irrigation)

        return farm

    def update(self, instance, validated_data):
        irrigations_data = validated_data.pop('irrigations', None)
        farm = super().update(instance, validated_data)

        if irrigations_data is not None:
            # Replace all existing irrigations
            instance.irrigations.all().delete()
            for irrigation in irrigations_data:
                FarmIrrigation.objects.create(farm=farm, **irrigation)

        return farm

class FarmDetailSerializer(FarmSerializer):
    images      = FarmImageSerializer(many=True, read_only=True)
    sensors     = FarmSensorSerializer(many=True, read_only=True)
    irrigations = FarmIrrigationSerializer(many=True, read_only=True)

    class Meta(FarmSerializer.Meta):
        fields = FarmSerializer.Meta.fields + [
            'images',
            'sensors',
            'irrigations',
        ]


class PlotGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Plot
        geo_field = 'boundary'
        fields = [
            'id',
            'gat_number',
            'plot_number',
            'village',
            'taluka',
            'district',
            'state',
            'country',
            'pin_code',
            'boundary',
        ]

class FarmGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Farm
        geo_field = 'plot__boundary'
        fields = [
            'id',
            'farm_uid',
            'address',
            'area_size',
            'soil_type',
            'crop_type',
            'created_at',
            'updated_at',
        ]
class PlotFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlotFile
        fields = '__all__'