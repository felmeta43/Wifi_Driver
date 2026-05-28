from django.urls import path
from . import views

urlpatterns = [
    path('tests/', views.lab_test_list, name='lab_test_list'),
    path('orders/', views.lab_order_list, name='lab_order_list'),
    path('orders/<int:pk>/', views.lab_order_detail, name='lab_order_detail'),
    path('orders/create/', views.lab_order_create, name='lab_order_create'),
    path('orders/<int:order_pk>/results/', views.add_lab_result, name='add_lab_result'),
    path('orders/<int:pk>/status/', views.update_order_status, name='update_order_status'),
]
