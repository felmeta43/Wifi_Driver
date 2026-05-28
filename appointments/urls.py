from django.urls import path
from . import views

urlpatterns = [
    path('', views.appointment_list, name='appointment_list'),
    path('today/', views.today_appointments, name='today_appointments'),
    path('<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('create/', views.appointment_create, name='appointment_create'),
    path('<int:pk>/edit/', views.appointment_edit, name='appointment_edit'),
    path('<int:pk>/status/', views.appointment_status_update, name='appointment_status_update'),
]
