from django.urls import path
from . import views

urlpatterns = [
    path('', views.service_list, name='service_list'),
    path('create/', views.service_create, name='service_create'),
    path('<int:pk>/edit/', views.service_edit, name='service_edit'),
    path('categories/', views.category_list, name='service_category_list'),
    path('orders/', views.service_order_list, name='service_order_list'),
    path('orders/create/', views.service_order_create, name='service_order_create'),
    path('orders/<int:pk>/', views.service_order_detail, name='service_order_detail'),
    path('orders/<int:pk>/complete/', views.service_order_complete, name='service_order_complete'),
    path('instant/', views.instant_service, name='instant_service'),
]
