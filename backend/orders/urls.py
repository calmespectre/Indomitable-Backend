from django.urls import path
from .views import (
    OrderListCreateView, OrderCancelView, OrderClearHistoryView,
    FavoriteListView, FavoriteDeleteView
)

urlpatterns = [
    path('orders/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('orders/clear/', OrderClearHistoryView.as_view(), name='order-clear'),

    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),
    path('favorites/<str:product_id>/',
         FavoriteDeleteView.as_view(), name='favorite-delete'),
]
