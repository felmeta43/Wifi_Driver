from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('<int:pk>/', views.doctor_detail, name='doctor_detail'),
    path('create/', views.doctor_create, name='doctor_create'),
    path('<int:pk>/edit/', views.doctor_edit, name='doctor_edit'),
    path('<int:doctor_pk>/schedule/', views.schedule_manage, name='schedule_manage'),
    path('specializations/', views.specialization_list, name='specialization_list'),
]
