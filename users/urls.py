from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    SimpleUserViewSet,
    RegisterView,  # existing
    
)
from .login_view import LoginView, PasswordResetRequestView, PasswordResetConfirmView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer

# DRF router
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'simple-users', SimpleUserViewSet, basename='simple-users')

# Custom JWT view
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    # Open registration endpoints
    path('register/', RegisterView.as_view(), name='register'),        # existing
   
    # Include router for users
    path('', include(router.urls)),

    # Auth endpoints
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
