from django.urls import path
from .views import (
    RegisterView, LoginView, PasswordResetView,
    GoogleLoginView, AppleLoginView,
    ProfileView, UpdateProfilePictureView, DeleteProfilePictureView,
    DeleteAccountView,
    PastOrdersView, CreateOrderView, CancelOrderView, ClearOrderHistoryView,
    FavoriteListView, FavoriteRemoveView, FavoriteToggleView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('password-reset/', PasswordResetView.as_view(), name='password_reset'),
    path('google/', GoogleLoginView.as_view(), name='google_login'),
    path('apple/', AppleLoginView.as_view(), name='apple_login'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', ProfileView.as_view(), name='update_profile'),
    path('profile/update-picture/',
         UpdateProfilePictureView.as_view(), name='update_picture'),
    path('profile/delete-picture/',
         DeleteProfilePictureView.as_view(), name='delete_picture'),
    path('profile/delete/', DeleteAccountView.as_view(), name='delete_account'),

    # Orders
    path('orders/', PastOrdersView.as_view(), name='past_orders'),
    path('orders/create/', CreateOrderView.as_view(), name='create_order'),
    path('orders/clear/', ClearOrderHistoryView.as_view(), name='clear_orders'),
    path('orders/<int:order_id>/cancel/',
         CancelOrderView.as_view(), name='cancel_order'),

    # Favorites
    path('favorites/', FavoriteListView.as_view(), name='favorites'),
    path('favorites/toggle/', FavoriteToggleView.as_view(), name='favorite_toggle'),
    path('favorites/<int:product_id>/',
         FavoriteRemoveView.as_view(), name='favorite_remove'),
]
