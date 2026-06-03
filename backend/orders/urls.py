from django.urls import path
from .views import (
    OrderListCreateView, OrderDetailView, OrderCancelView, OrderClearHistoryView,
    FavoriteListView, FavoriteDeleteView,
    NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView, NotificationDeleteView
)

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('orders/clear/', OrderClearHistoryView.as_view(), name='order-clear'),

    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/<str:product_id>/',
         FavoriteDeleteView.as_view(), name='favorite-delete'),

    path('notifications/', NotificationListView.as_view(),
         name='notification-list'),
    path('notifications/<int:pk>/read/',
         NotificationMarkReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', NotificationMarkAllReadView.as_view(),
         name='notification-read-all'),
    path('notifications/<int:pk>/', NotificationDeleteView.as_view(),
         name='notification-delete'),
]
