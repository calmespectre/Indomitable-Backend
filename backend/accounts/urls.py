from django.urls import path
from .views import (
    RegisterView, LoginView, PasswordResetView,
    GoogleLoginView, AppleLoginView,
    ProfileView, UpdateProfilePictureView, DeleteProfilePictureView,
    DeleteAccountView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),

    # Social Logins
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    path('apple/', AppleLoginView.as_view(), name='apple_login'),

    # JWT Refresh endpoint
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),

    # Account Profile endpoints
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileView.as_view(), name='update_profile'),
    path('profile/update-picture/',
         UpdateProfilePictureView.as_view(), name='update_picture'),
    path('profile/delete-picture/',
         DeleteProfilePictureView.as_view(), name='delete_picture'),
    path('profile/delete/', DeleteAccountView.as_view(), name='delete_account'),
]
