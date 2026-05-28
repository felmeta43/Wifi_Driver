from django.urls import path
from . import views

urlpatterns = [
    path('', views.patient_list, name='patient_list'),
    path('<int:pk>/', views.patient_detail, name='patient_detail'),
    path('create/', views.patient_create, name='patient_create'),
    path('<int:pk>/edit/', views.patient_edit, name='patient_edit'),
    path('<int:patient_pk>/medical-record/add/', views.medical_record_create, name='medical_record_create'),
    path('<int:patient_pk>/admit/', views.admission_create, name='admission_create'),
]
