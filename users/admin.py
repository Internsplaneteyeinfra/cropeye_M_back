from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.urls import re_path
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden
from django.utils.html import format_html
from django.urls import reverse
from .models import Role
from .forms import CustomUserCreationForm, CustomUserChangeForm




User = get_user_model()


class IndustryFilteredAdmin(admin.ModelAdmin):
    """
    Base admin class that automatically filters by industry for non-superusers.
    """
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


# ==================== Industry Admin ====================
try:
    from .models import Industry

    @admin.register(Industry)
    class IndustryAdmin(admin.ModelAdmin):
        list_display = ('name', 'test_phone_number', 'description', 'view_all_data_link', 'created_at', 'updated_at')
        search_fields = ('name', 'description', 'test_phone_number')
        list_filter = ('created_at', 'updated_at')
        ordering = ('name',)
        readonly_fields = ('created_at', 'updated_at')

        fieldsets = (
            (None, {
                'fields': ('name', 'description'),
                'description': 'Enter the industry name (e.g., "Industry A", "Industry B") and optional description.'
            }),
            ('Test Credentials', {
                'fields': ('test_phone_number', 'test_password'),
                'description': 'Test phone number and password for this industry. Use these credentials for API testing.'
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',),
            }),
        )

        def view_all_data_link(self, obj):
            if obj:
                url = reverse('admin:users_industry_data_view', args=[obj.pk])
                return format_html(
                    '<a class="button" href="{}" style="background-color: #417690; color: white; padding: 8px 12px; text-decoration: none; border-radius: 4px; display: inline-block;">📊 View All Data</a>',
                    url
                )
            return "-"
        view_all_data_link.short_description = 'View All Data'

        def change_view(self, request, object_id, form_url='', extra_context=None):
            extra_context = extra_context or {}
            if object_id:
                try:
                    industry_id = int(object_id)
                    url = reverse('admin:users_industry_data_view', args=[industry_id])
                    extra_context['view_all_data_url'] = url
                except (ValueError, TypeError):
                    pass
            return super().change_view(request, object_id, form_url, extra_context)

        def get_urls(self):
            urls = super().get_urls()
            custom_urls = [
                re_path(
                    r'^(?P<industry_id>\d+)/view-all-data/$',
                    self.admin_site.admin_view(self.industry_data_view),
                    name='users_industry_data_view',
                ),
                re_path(
                    r'^(?P<industry_id>\d+)/view-all-data$',
                    self.admin_site.admin_view(self.industry_data_view),
                    name='users_industry_data_view_no_slash',
                ),
            ]
            return custom_urls + urls

        def industry_data_view(self, request, industry_id):
            try:
                industry_id = int(industry_id)
            except (ValueError, TypeError):
                return HttpResponseForbidden("Invalid industry ID.")

            if not request.user.is_superuser:
                if not (request.user.role and request.user.role.name == 'owner' and request.user.industry and request.user.industry.id == industry_id):
                    return HttpResponseForbidden("You don't have permission to view this industry's data.")

            industry = get_object_or_404(Industry, id=industry_id)

            # Users by role
            owners = User.objects.filter(industry=industry, role__name='owner').select_related('role', 'industry')
            managers = User.objects.filter(industry=industry, role__name='manager').select_related('role', 'industry')
            field_officers = User.objects.filter(industry=industry, role__name='fieldofficer').select_related('role', 'industry')
            farmers = User.objects.filter(industry=industry, role__name='farmer').select_related('role', 'industry')

            context = {
                'industry': industry,
                'owners': owners,
                'managers': managers,
                'field_officers': field_officers,
                'farmers': farmers,
                'owners_count': owners.count(),
                'managers_count': managers.count(),
                'field_officers_count': field_officers.count(),
                'farmers_count': farmers.count(),
                'total_users_count': owners.count() + managers.count() + field_officers.count() + farmers.count()
            }

            # Additional data
            try:
                from farms.models import Plot, Farm
                context['plots'] = Plot.objects.filter(industry=industry).select_related('farmer', 'created_by', 'industry')
                context['farms'] = Farm.objects.filter(industry=industry).select_related('farm_owner', 'plot', 'crop_type', 'soil_type', 'industry')
                context['plots_count'] = context['plots'].count()
                context['farms_count'] = context['farms'].count()
            except ImportError:
                context['plots'] = []
                context['farms'] = []
                context['plots_count'] = 0
                context['farms_count'] = 0

            try:
                from tasks.models import Task
                context['tasks'] = Task.objects.filter(industry=industry).select_related('assigned_to', 'created_by', 'industry')
                context['tasks_count'] = context['tasks'].count()
            except ImportError:
                context['tasks'] = []
                context['tasks_count'] = 0

            try:
                from bookings.models import Booking
                context['bookings'] = Booking.objects.filter(industry=industry).select_related('created_by', 'approved_by', 'industry')
                context['bookings_count'] = context['bookings'].count()
            except ImportError:
                context['bookings'] = []
                context['bookings_count'] = 0

            try:
                from inventory.models import InventoryItem, Stock
                context['inventory_items'] = InventoryItem.objects.filter(industry=industry).select_related('industry')
                context['inventory_items_count'] = context['inventory_items'].count()
                context['stock_items'] = Stock.objects.filter(industry=industry).select_related('created_by', 'industry')
                context['stock_items_count'] = context['stock_items'].count()
            except ImportError:
                context['inventory_items'] = []
                context['inventory_items_count'] = 0
                context['stock_items'] = []
                context['stock_items_count'] = 0

            try:
                from vendors.models import Vendor, Order
                context['vendors'] = Vendor.objects.filter(created_by__industry=industry).select_related('created_by')
                context['vendors_count'] = context['vendors'].count()
                context['orders'] = Order.objects.filter(created_by__industry=industry).select_related('vendor', 'created_by')
                context['orders_count'] = context['orders'].count()
            except ImportError:
                context['vendors'] = []
                context['vendors_count'] = 0
                context['orders'] = []
                context['orders_count'] = 0

            context.update({
                'opts': self.model._meta,
                'has_view_permission': True,
                'has_add_permission': self.has_add_permission(request),
                'has_change_permission': self.has_change_permission(request, industry),
                'has_delete_permission': self.has_delete_permission(request, industry),
                'site_header': self.admin_site.site_header,
                'site_title': self.admin_site.site_title,
            })

            return render(request, 'admin/users/industry_data_view.html', context)

except Exception:
    pass


# ==================== Role Admin ====================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name')
    search_fields = ('name', 'display_name')


# ==================== User Admin ====================]

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    # Fields displayed in the user edit page (Change view)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal info', {'fields': (
            'first_name', 'last_name', 'email', 'address', 'profile_picture'
        )}),
        ('Location', {'fields': ('state', 'district', 'taluka', 'village')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Industry & Hierarchy', {'fields': ('industry', 'created_by')}),
        ('Security', {'fields': ('password_reset_token', 'password_reset_token_created_at')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    # Show all fields in Add User view
    def get_fieldsets(self, request, obj=None):
        if not obj:  # Add User view
            return (
                (None, {
                    'classes': ('wide',),
                    'fields': (
                        'phone_number', 'email', 'first_name', 'last_name',
                        'address', 'profile_picture',
                        'state', 'district', 'taluka', 'village',
                        'role', 'industry', 'created_by',
                        'password1', 'password2',
                        'is_active', 'is_staff', 'is_superuser',
                        'groups', 'user_permissions',
                    ),
                }),
            )
        return self.fieldsets  # Change User view

    # Columns in the user list page
    list_display = (
        'phone_number', 'email', 'first_name', 'last_name', 'role', 'industry', 'get_created_by_email',
        'state', 'district', 'taluka',
        'is_active', 'is_staff', 'is_superuser', 'date_joined'
    )

    # Filters on the list page
    list_filter = (
        'role', 'industry', 'state', 'district', 'taluka',
        'is_active', 'is_staff', 'is_superuser', 'created_by'
    )

    # Searchable fields
    search_fields = (
        'phone_number', 'email', 'first_name', 'last_name',
        'created_by__phone_number', 'created_by__email', 'industry__name'
    )

    # Default ordering
    ordering = ('-date_joined',)

    # Horizontal filters for many-to-many fields
    filter_horizontal = ('groups', 'user_permissions',)

    # Helper to display the email of the user who created this account
    def get_created_by_email(self, obj):
        return obj.created_by.email if obj.created_by else "No creator"
    get_created_by_email.short_description = 'Created By (Email)'
    get_created_by_email.admin_order_field = 'created_by__email'

    # Limit queryset for non-superusers
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        from .multi_tenant_utils import get_accessible_users
        return get_accessible_users(request.user)

    def save_model(self, request, obj, form, change):
        if not change:  # Only on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
