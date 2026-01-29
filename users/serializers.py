from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
import re
from .models import Role, Industry
from farms.models import Plot, Farm

User = get_user_model()

class FarmSummarySerializer(serializers.ModelSerializer):
    """A lean serializer for farm details within a plot."""
    plantation_type = serializers.CharField(source='crop_type.plantation_type', allow_null=True)
    plantation_type_display = serializers.CharField(source='crop_type.get_plantation_type_display', allow_null=True, read_only=True)
    crop_type = serializers.CharField(source='crop_type.crop_type', allow_null=True)

    class Meta:
        model = Farm
        fields = [
            'id',
            'farm_uid',
            'area_size',
            'crop_type',
            'plantation_type',
            'plantation_type_display',
            'plantation_date'
        ]

class PlotDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed plot information within nested responses."""
    location = serializers.SerializerMethodField()
    boundary = serializers.SerializerMethodField()
    fastapi_plot_id = serializers.SerializerMethodField()
    farms = FarmSummarySerializer(many=True, read_only=True)

    class Meta:
        model = Plot
        fields = [
            'id', 'fastapi_plot_id', 'gat_number', 'plot_number', 'village', 'taluka', 'district', 'state', 'location', 'boundary', 'created_at', 'farms'
        ]

    def get_location(self, obj):
        if obj.location:
            return {'type': 'Point', 'coordinates': [obj.location.x, obj.location.y]}
        return None

    def get_boundary(self, obj):
        if obj.boundary:
            return {'type': 'Polygon', 'coordinates': obj.boundary.coords}
        return None

    def get_fastapi_plot_id(self, obj):
        """Generate plot ID in the same format as FastAPI services"""
        if obj.gat_number and obj.plot_number:
            return f"{obj.gat_number}_{obj.plot_number}"
        elif obj.gat_number:
            return obj.gat_number
        else:
            return f"plot_{obj.id}"

class FarmerWithPlotsSerializer(serializers.ModelSerializer):
    """Serializer for a Farmer, including a list of their plots."""
    plots = PlotDetailSerializer(many=True, read_only=True)
    role = serializers.StringRelatedField()

    class Meta:
        model = User 
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'email',
            'village', 'district', 'role', 'plots'
        ]

    def __init__(self, *args, **kwargs):
        # Prefetch related plots for performance
        super().__init__(*args, **kwargs)
        if 'context' in kwargs and 'request' in kwargs['context']:
            self.Meta.model.objects.prefetch_related('plots__farms__crop_type')


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name', 'display_name']


class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = ['id', 'name', 'description']


class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    industry = IndustrySerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'first_name', 'last_name', 
            'address', 'village', 'taluka', 'district', 'state',
            'role', 'industry', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    def get_role(self, obj):
        if obj.role:
            return {
                'id': obj.role.id,
                'name': obj.role.name
            }
        return None

    # Return industry info
    def get_industry(self, obj):
        if obj.industry:
            return {
                'id': obj.industry.id,
                'name': obj.industry.name
            }
        return None

class FarmerDetailSerializer(UserSerializer):
    """Enhanced serializer for farmers with irrigation and plantation details"""
    
    # Basic user info (inherited from UserSerializer)
    # role, created_by, created_at, updated_at are already included
    
    # Farmer-specific agricultural data
    plots = serializers.SerializerMethodField()
    farms = serializers.SerializerMethodField()
    irrigation_details = serializers.SerializerMethodField()
    plantation_details = serializers.SerializerMethodField()
    agricultural_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'first_name', 'last_name', 
            'address', 'village', 'taluka', 'district', 'state',
            'role', 'created_by', 'created_at', 'updated_at',
            'plots', 'farms', 'irrigation_details', 'plantation_details', 'agricultural_summary'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_plots(self, obj):
        """Get all plots owned by the farmer"""
        plots_data = []
        for plot in obj.plots.all():
            plot_info = {
                'id': plot.id,
                'gat_number': plot.gat_number,
                'plot_number': plot.plot_number,
                'village': plot.village,
                'taluka': plot.taluka,
                'district': plot.district,
                'state': plot.state,
                'country': plot.country,
                'pin_code': plot.pin_code,
                'location': {
                    'type': 'Point',
                    'coordinates': [plot.location.x, plot.location.y] if plot.location else None
                } if plot.location else None,
                'boundary': {
                    'type': 'Polygon',
                    'coordinates': plot.boundary.coords[0] if plot.boundary else None
                } if plot.boundary else None,
                'created_at': plot.created_at.isoformat() if plot.created_at else None,
                'updated_at': plot.updated_at.isoformat() if plot.updated_at else None
            }
            plots_data.append(plot_info)
        return plots_data
    
    def get_farms(self, obj):
        """Get all farms owned by the farmer"""
        farms_data = []
        for farm in obj.farms.all():
            farm_info = {
                'id': farm.id,
                'farm_uid': str(farm.farm_uid),
                'address': farm.address,
                'area_size': str(farm.area_size) if farm.area_size else None,
                'area_size_numeric': float(farm.area_size) if farm.area_size else None,
                'spacing_a': float(farm.spacing_a) if farm.spacing_a else None,
                'spacing_b': float(farm.spacing_b) if farm.spacing_b else None,
                'plantation_date': farm.plantation_date.isoformat() if farm.plantation_date else None,
                'plants_in_field': farm.plants_in_field,
                'soil_type': {
                    'id': farm.soil_type.id,
                    'name': farm.soil_type.name
                } if farm.soil_type else None,
                'crop_type': {
                    'id': farm.crop_type.id,
                    'crop_type': farm.crop_type.crop_type,
                    'plantation_type': farm.crop_type.plantation_type,
                    'plantation_type_display': farm.crop_type.get_plantation_type_display() if farm.crop_type.plantation_type else None,
                    'planting_method': farm.crop_type.planting_method,
                    'planting_method_display': farm.crop_type.get_planting_method_display() if farm.crop_type.planting_method else None
                } if farm.crop_type else None,
                'farm_document': {
                    'name': farm.farm_document.name.split('/')[-1] if farm.farm_document else None,
                    'url': farm.farm_document.url if farm.farm_document else None,
                    'size': farm.farm_document.size if farm.farm_document else None
                } if farm.farm_document else None,
                'created_at': farm.created_at.isoformat() if farm.created_at else None,
                'updated_at': farm.updated_at.isoformat() if farm.updated_at else None,
                'created_by': {
                    'id': farm.created_by.id,
                    'phone_number': farm.created_by.phone_number,
                    'full_name': f"{farm.created_by.first_name} {farm.created_by.last_name}".strip() or farm.created_by.phone_number,
                    'email': farm.created_by.email
                } if farm.created_by else None
            }
            farms_data.append(farm_info)
        return farms_data
    
    def get_irrigation_details(self, obj):
        """Get all irrigation details for the farmer's farms"""
        irrigation_data = []
        for farm in obj.farms.all():
            for irrigation in farm.irrigations.all():
                irrigation_info = {
                    'id': irrigation.id,
                    'farm_id': farm.id,
                    'farm_uid': str(farm.farm_uid),
                    'irrigation_type': irrigation.irrigation_type.get_name_display() if irrigation.irrigation_type else None,
                    'irrigation_type_code': irrigation.irrigation_type.name if irrigation.irrigation_type else None,
                    'location': {
                        'type': 'Point',
                        'coordinates': [irrigation.location.x, irrigation.location.y] if irrigation.location else None
                    } if irrigation.location else None,
                    'status': irrigation.status,
                    'status_display': 'Active' if irrigation.status else 'Inactive',
                    'motor_horsepower': irrigation.motor_horsepower,
                    'pipe_width_inches': irrigation.pipe_width_inches,
                    'distance_motor_to_plot_m': irrigation.distance_motor_to_plot_m,
                    'plants_per_acre': irrigation.plants_per_acre,
                    'flow_rate_lph': irrigation.flow_rate_lph,
                    'emitters_count': irrigation.emitters_count
                }
                irrigation_data.append(irrigation_info)
        return irrigation_data
    
    def get_plantation_details(self, obj):
        """Get plantation details from crop types"""
        plantation_data = []
        for farm in obj.farms.all():
            if farm.crop_type:
                plantation_info = {
                    'farm_id': farm.id,
                    'farm_uid': str(farm.farm_uid),
                    'crop_type': farm.crop_type.crop_type,
                    'plantation_type': farm.crop_type.plantation_type,
                    'plantation_type_display': farm.crop_type.get_plantation_type_display() if farm.crop_type.plantation_type else None,
                    'planting_method': farm.crop_type.planting_method,
                    'planting_method_display': farm.crop_type.get_planting_method_display() if farm.crop_type.planting_method else None,
                    'plantation_date': farm.plantation_date.isoformat() if farm.plantation_date else None,
                    'area_size': str(farm.area_size) if farm.area_size else None,
                    'soil_type': farm.soil_type.name if farm.soil_type else None
                }
                plantation_data.append(plantation_info)
        return plantation_data
    
    def get_agricultural_summary(self, obj):
        """Get agricultural summary statistics"""
        total_plots = obj.plots.count()
        total_farms = obj.farms.count()
        total_irrigations = sum(farm.irrigations.count() for farm in obj.farms.all())
        
        # Get unique irrigation types
        irrigation_types = set()
        for farm in obj.farms.all():
            for irrigation in farm.irrigations.all():
                if irrigation.irrigation_type:
                    irrigation_types.add(irrigation.irrigation_type.get_name_display())
        
        # Get unique crop types
        crop_types = set()
        for farm in obj.farms.all():
            if farm.crop_type and farm.crop_type.crop_type:
                crop_types.add(farm.crop_type.crop_type)
        
        # Calculate total area
        total_area = sum(float(farm.area_size) for farm in obj.farms.all() if farm.area_size)
        
        return {
            'total_plots': total_plots,
            'total_farms': total_farms,
            'total_irrigations': total_irrigations,
            'total_area_acres': round(total_area, 2),
            'irrigation_types': list(irrigation_types),
            'crop_types': list(crop_types),
            'plots_with_boundaries': obj.plots.filter(boundary__isnull=False).count(),
            'plots_with_locations': obj.plots.filter(location__isnull=False).count()
        }

class FieldOfficerWithFarmersSerializer(serializers.ModelSerializer):
    """
    Serializer for a Field Officer, including a nested list of their farmers and plots.
    """
    farmers = serializers.SerializerMethodField()
    role = serializers.StringRelatedField()

    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'first_name', 'last_name', 'email',
            'role', 'farmers'
        ]

    def get_farmers(self, obj):
        """
        Get all farmers created by this field officer, serialized with their plots.
        """
        # We query for farmers who have this field officer as their creator.
        farmers = User.objects.filter(
            created_by=obj,
            role__name='farmer'
        ).prefetch_related('plots__farms__crop_type').order_by('first_name')
        
        serializer = FarmerWithPlotsSerializer(farmers, many=True, context=self.context)
        return serializer.data

class FieldOfficerSerializer(FieldOfficerWithFarmersSerializer):
    pass

class FarmerSerializer(UserSerializer):
    role = RoleSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'first_name', 'last_name', 
            'address', 'village', 'taluka', 'district', 'state',
            'role', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class ManagerHierarchySerializer(UserSerializer):
    """Serializer for Manager showing their field officers and farmers"""
    role = RoleSerializer(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    
    # Field officers under this manager
    field_officers = serializers.SerializerMethodField()
    field_officers_count = serializers.SerializerMethodField()
    
    # Farmers under this manager (through field officers)
    total_farmers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'first_name', 'last_name', 
            'address', 'village', 'taluka', 'district', 'state',
            'role', 'created_by', 'created_at', 'updated_at',
            'field_officers', 'field_officers_count', 'total_farmers_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_field_officers(self, obj):
        """Get all field officers created by this manager"""
        field_officers = obj.created_users.filter(role__name='fieldofficer')
        return FieldOfficerSerializer(field_officers, many=True).data
    
    def get_field_officers_count(self, obj):
        """Count of field officers under this manager"""
        return obj.created_users.filter(role__name='fieldofficer').count()
    
    def get_total_farmers_count(self, obj):
        """Count of total farmers under this manager (through field officers)"""
        total = 0
        for field_officer in obj.created_users.filter(role__name='fieldofficer'):
            total += field_officer.created_users.filter(role__name='farmer').count()
        return total

class OwnerHierarchySerializer(serializers.ModelSerializer):
    """Serializer for Owner showing complete hierarchy"""
    role = RoleSerializer(read_only=True)
    
    # All managers in the system
    managers = serializers.SerializerMethodField()
    managers_count = serializers.SerializerMethodField()
    
    # Total counts across all hierarchy
    total_field_officers = serializers.SerializerMethodField()
    total_farmers = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'email', 'first_name', 'last_name', 
            'address', 'village', 'taluka', 'district', 'state',
            'role', 'created_at', 'updated_at',
            'managers', 'managers_count', 'total_field_officers', 'total_farmers'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_managers(self, obj):
        """Get all managers in the system"""
        # Special logic: Owner can monitor all managers, including the one who created them
        managers = User.objects.filter(role__name='manager')
        return ManagerHierarchySerializer(managers, many=True).data
    
    def get_managers_count(self, obj):
        """Count of total managers"""
        return User.objects.filter(role__name='manager').count()
    
    def get_total_field_officers(self, obj):
        """Count of total field officers across all managers"""
        return User.objects.filter(role__name='fieldofficer').count()
    
    def get_total_farmers(self, obj):
        """Count of total farmers across all field officers"""
        return User.objects.filter(role__name='farmer').count()

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # Use CharField to accept both string and integer from frontend, then validate and convert to int
    role_id = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    # Industry is set automatically by the view, but we include it in fields to allow it
    industry = serializers.PrimaryKeyRelatedField(queryset=Industry.objects.all(), required=False, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'phone_number', 'email', 'password', 'first_name', 'last_name',
            'address', 'village', 'taluka', 'district', 'state', 'profile_picture',
            'role_id', 'industry'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number format (10 digits for India) and uniqueness"""
        import re
        if value:
            cleaned_phone = re.sub(r'\D', '', value)
            if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
                cleaned_phone = cleaned_phone[2:]
            if len(cleaned_phone) != 10:
                raise serializers.ValidationError("Phone number must be exactly 10 digits (or 12 digits with +91).")
            if User.objects.filter(phone_number=cleaned_phone).exists():
                raise serializers.ValidationError("A user with this phone number already exists.")
            return cleaned_phone
        raise serializers.ValidationError("Phone number is required.")
    
    def validate_role_id(self, value):
        """Validate that the role exists - accepts both role ID (int/string) and role name (string)"""
        import logging
        logger = logging.getLogger(__name__)
        
        # Handle None, empty string, blank, null values
        if value is None or value == '' or value == 'null' or value == 'undefined':
            return None
        
        # Handle string representations
        if isinstance(value, str):
            value = value.strip()  # Remove whitespace
            if value == '' or value.lower() in ['null', 'undefined', 'none']:
                return None
        
        # Handle 0 as None (for auto-determination)
        if value == 0 or value == '0':
            return None
        
        # NEW: Check if it's a role name instead of role ID
        # Map role names to role IDs
        role_name_mapping = {
            'farmer': 1,
            'fieldofficer': 2,
            'field_officer': 2,
            'field-officer': 2,
            'manager': 3,
            'owner': 4
        }
        
        # If value is a role name (string), convert it to role ID
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in role_name_mapping:
                role_id_int = role_name_mapping[value_lower]
                logger.info(f"Converted role name '{value}' to role ID: {role_id_int}")
                # Continue with validation using the converted ID
                value = role_id_int
            else:
                # Not a role name, try to convert to integer (might be "1", "2", etc.)
                try:
                    value = int(value)
                except (ValueError, TypeError) as e:
                    logger.error(f"Failed to convert role_id to integer. Value: {repr(value)}, Type: {type(value)}, Error: {e}")
                    raise serializers.ValidationError(
                        f"Invalid role ID format. Received: '{value}' (type: {type(value).__name__}). "
                        f"Must be a valid integer (1, 2, 3, or 4) or role name (farmer, fieldofficer, manager, owner)."
                    )
        
        # Convert to int - handle both string and integer inputs
        try:
            role_id_int = int(value)
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert role_id to integer. Value: {repr(value)}, Type: {type(value)}, Error: {e}")
            raise serializers.ValidationError(
                f"Invalid role ID format. Received: '{value}' (type: {type(value).__name__}). "
                f"Must be a valid integer (1, 2, 3, or 4) or role name (farmer, fieldofficer, manager, owner)."
            )
        
        # Validate that the role exists in database
        try:
            role = Role.objects.get(id=role_id_int)
            logger.info(f"Validated role_id: {role_id_int} -> {role.name} ({role.display_name})")
        except Role.DoesNotExist:
            logger.error(f"Role with ID {role_id_int} does not exist in database")
            raise serializers.ValidationError(
                f"Role with ID {role_id_int} does not exist. Valid role IDs: 1 (Farmer), 2 (Field Officer), 3 (Manager), 4 (Owner)."
            )
        
        return role_id_int  # Return as integer
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_industry(self, value):
        """
        Industry is set automatically by the view from the creator's industry.
        Frontend cannot override this - any value sent will be ignored.
        """
        # If value is an Industry instance (set by view or already validated), keep it
        if isinstance(value, Industry):
            return value
        # If value is an integer (industry ID from frontend), ignore it - view will set the correct one
        # Return None to ignore frontend values - view will set it after validation
        # Note: The view sets industry in validated_data AFTER validation, so this will be None during validation
        return None
    
    def create(self, validated_data):
        import logging
        from rest_framework import serializers
        from .models import User, Role

        logger = logging.getLogger(__name__)

        # --- Extract password ---
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirmation', None)  # remove confirmation
        if not password:
            raise serializers.ValidationError({"password": "Password is required."})

        # --- Extract and process role ---
        role_id = validated_data.pop('role', None)
        request = self.context.get('request')
        creator = request.user if request else None

        # Auto-assign role if missing
        if not role_id and creator:
            if hasattr(creator, 'role') and creator.role.name.lower() == 'manager':
                role = Role.objects.get(name__iexact='Field Officer')
            elif hasattr(creator, 'role') and creator.role.name.lower() == 'fieldofficer':
                role = Role.objects.get(name__iexact='Farmer')
            else:
                role = None
        elif role_id:
            # If role is provided as id or name
            if isinstance(role_id, int):
                role = Role.objects.filter(id=role_id).first()
            else:
                role = Role.objects.filter(name__iexact=str(role_id)).first()
        else:
            role = None

        if not role:
            raise serializers.ValidationError({"role": "Valid role is required."})

        # --- Ensure industry is set ---
        if 'industry' not in validated_data or validated_data['industry'] is None:
            if creator and hasattr(creator, 'industry') and creator.industry:
                validated_data['industry'] = creator.industry
            else:
                raise serializers.ValidationError({
                    'industry': 'Industry must be provided or inherited from creator.'
                })

        # --- phone_number is required (unique identifier) ---
        phone_number = validated_data.get('phone_number')
        if not phone_number:
            raise serializers.ValidationError({"phone_number": "Phone number is required."})

        # --- CREATE USER using create_user (phone_number as identifier) ---
        user = User.objects.create_user(
            phone_number=phone_number,
            password=password,
            role=role,
            created_by=creator,
            industry=validated_data.get('industry'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            address=validated_data.get('address', ''),
            village=validated_data.get('village', ''),
            taluka=validated_data.get('taluka', ''),
            district=validated_data.get('district', ''),
            state=validated_data.get('state', ''),
            profile_picture=validated_data.get('profile_picture'),
        )

        logger.info(f"User {user.phone_number} created successfully with role {role.name} and industry {user.industry.name if user.industry else 'None'}")
        return user


    def validate(self, data):
        password = data.get('password')
        password_confirmation = data.get('password_confirmation')
        
        if not password:
            raise serializers.ValidationError({"password": "This field cannot be blank."})
        if password != password_confirmation:
            raise serializers.ValidationError({"password_confirmation": "Passwords must match."})
        
        return data
class UserUpdateSerializer(serializers.ModelSerializer):
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        required=False
    )

    class Meta:
        model = User
        fields = [
            'email','first_name', 'last_name', 'role_id', 'phone_number', 'address',
            'village', 'state', 'district', 'taluka', 'profile_picture',
        ]
        read_only_fields = ['email']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that uses phone_number instead of email/username
    """
    # Override parent fields completely
    username = None
    phone_number = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def __init__(self, *args, **kwargs):
        # Don't call super().__init__ first - we'll handle fields manually
        super(TokenObtainPairSerializer, self).__init__(*args, **kwargs)
        # Remove username field completely
        self.fields.pop('username', None)
        # Ensure our fields are present
        self.fields['phone_number'] = serializers.CharField(required=True, write_only=True)
        self.fields['password'] = serializers.CharField(required=True, write_only=True)
    
    def validate_phone_number(self, value):
        """Field-level validation for phone_number - handles +91 country code"""
        import re
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        
        # Clean phone number (remove non-digit characters)
        cleaned_phone = re.sub(r'\D', '', value)
        
        # If starts with 91 (country code), remove it to get 10 digits
        if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
            cleaned_phone = cleaned_phone[2:]
        
        # Validate it's exactly 10 digits
        if len(cleaned_phone) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits (or 12 digits with +91).")
        
        # Return the cleaned value (this will be used in validate() method)
        return cleaned_phone
    
    def validate(self, attrs):
        # Remove any username that might have been passed
        attrs.pop('username', None)
        
        # phone_number is already cleaned by validate_phone_number() to 10 digits
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        
        if not phone_number:
            raise serializers.ValidationError({
                'phone_number': ['This field is required.']
            })
        
        if not password:
            raise serializers.ValidationError({
                'password': ['This field is required.']
            })
        
        # Authenticate using phone_number (already cleaned to 10 digits)
        user = authenticate(
            request=self.context.get('request'),
            phone_number=phone_number,
            password=password
        )
        
        if not user:
            raise serializers.ValidationError({
                'non_field_errors': ['Invalid phone number or password']
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': ['Account is deactivated']
            })
        
        # Get token using parent class method
        refresh = self.get_token(user)
        
        data = {}
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        
        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New passwords must match.")
        return data


class SimpleUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    
    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'state',
            'district',
            'taluka',
            'password',
            'role',
            'industry',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'role', 'industry', 'created_at', 'updated_at']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'phone_number': {'required': True},
            'state': {'required': False},
            'district': {'required': False},
            'taluka': {'required': False},
        }
    
    def validate_phone_number(self, value):
        """Validate phone number format (10 digits for India) and handle +91 country code"""
        import re
        if value:
            # Remove all non-digit characters
            cleaned_phone = re.sub(r'\D', '', value)
            
            # If starts with 91 (country code), remove it to get 10 digits
            if cleaned_phone.startswith('91') and len(cleaned_phone) == 12:
                cleaned_phone = cleaned_phone[2:]
            
            # Validate it's exactly 10 digits
            if len(cleaned_phone) != 10:
                raise serializers.ValidationError("Phone number must be exactly 10 digits (or 12 digits with +91).")
            
            # Check if phone number already exists
            if User.objects.filter(phone_number=cleaned_phone).exists():
                raise serializers.ValidationError("A user with this phone number already exists.")
            
            return cleaned_phone
        raise serializers.ValidationError("Phone number is required.")
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        """Create a farmer user with automatic role assignment"""
        from .models import Role
        
        password = validated_data.pop('password')
        
        # Get or create farmer role
        try:
            farmer_role = Role.objects.get(name='farmer')
        except Role.DoesNotExist:
            raise serializers.ValidationError({
                'role': 'Farmer role not found in system. Please contact administrator.'
            })
        
        # phone_number is required (unique identifier)
        phone_number = validated_data.get('phone_number')
        if not phone_number:
            raise serializers.ValidationError({"phone_number": "Phone number is required."})

        # Create farmer user (phone_number as identifier)
        user = User.objects.create_user(
            phone_number=phone_number,
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=password,
            role=farmer_role,
            created_by=None,
            state=validated_data.get('state'),
            district=validated_data.get('district'),
            taluka=validated_data.get('taluka'),
        )
        
        return user