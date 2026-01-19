from django.urls import path, include
from .views import UserViewSet, SimpleUserViewSet, RegisterView  # <-- Add RegisterView here
from rest_framework.routers import DefaultRouter
from .login_view import LoginView, PasswordResetRequestView, PasswordResetConfirmView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'simple-users', SimpleUserViewSet, basename='simple-users')

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # <-- open to all
    path('', include(router.urls)),

    # auth
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
