from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/stats/', views.DashboardStatsView.as_view()),
    path('orders/recent/', views.RecentOrdersView.as_view()),
    path('products/top/', views.TopProductsView.as_view()),
    path('customers/recent/', views.RecentCustomersView.as_view()),
    path('customers/', views.CustomerListView.as_view()),
    path('orders/', views.RecentOrdersView.as_view()),   # or a full list view
    path('orders/<int:pk>/update_status/',
         views.OrderUpdateStatusView.as_view()),
    # Add other routes as needed
]
