from django.urls import path
from . import views

urlpatterns = [
    path('stk-push/', views.stk_push, name='stk_push'),
    path('stk-push-status/<str:checkout_request_id>/',
         views.stk_push_status, name='stk_push_status'),
    path('callback/', views.stk_callback, name='stk_callback'),
]
