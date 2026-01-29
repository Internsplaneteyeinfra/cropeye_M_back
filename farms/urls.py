from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SoilTypeViewSet,
    CropTypeViewSet,
    PlantationTypeViewSet,
    PlantingMethodViewSet,
    FarmViewSet,
    PlotViewSet,
    PlotFileViewSet,
    FarmImageViewSet,
    FarmSensorViewSet,
    FarmIrrigationViewSet,
    IrrigationTypeViewSet,
    get_crop_fields_config,
    get_crop_type_choices,
    CompleteFarmerRegistrationAPIView,
)

# DRF router
router = DefaultRouter()

# Register all your ViewSets
router.register('soil-types', SoilTypeViewSet, basename='soiltype')
router.register('crop-types', CropTypeViewSet, basename='croptype')
router.register('plantation-types', PlantationTypeViewSet, basename='plantationtype')
router.register('planting-methods', PlantingMethodViewSet, basename='plantingmethod')
router.register('irrigation-types', IrrigationTypeViewSet, basename='irrigationtype')

router.register(r'farms', FarmViewSet, basename='farm')

router.register('plots', PlotViewSet, basename='plot')

# ✅ Plot files CRUD
router.register('plot-files', PlotFileViewSet, basename='plotfile')

router.register('farm-images', FarmImageViewSet, basename='farmimage')
router.register('farm-sensors', FarmSensorViewSet, basename='farmsensor')
router.register('farm-irrigations', FarmIrrigationViewSet, basename='farmirrigation')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),  # All router endpoints
    path('crop-fields-config/', get_crop_fields_config, name='crop-fields-config'),
    path('crop-type-choices/', get_crop_type_choices, name='crop-type-choices'),
    path('register/farmer/', CompleteFarmerRegistrationAPIView.as_view(), name='farmer-register'),
   
]
