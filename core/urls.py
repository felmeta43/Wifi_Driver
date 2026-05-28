from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('settings/', views.hospital_settings_view, name='hospital_settings'),
    path('departments/', views.departments, name='departments'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('notifications/', views.notifications_view, name='notifications'),
]
