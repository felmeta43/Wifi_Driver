from django.urls import path
from . import views

urlpatterns = [
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/create/', views.medicine_create, name='medicine_create'),
    path('medicines/<int:pk>/edit/', views.medicine_edit, name='medicine_edit'),
    path('medicines/<int:pk>/stock-in/', views.stock_in, name='stock_in'),
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('prescriptions/create/', views.prescription_create, name='prescription_create'),
    path('prescriptions/<int:pk>/dispense/', views.dispense_prescription, name='dispense_prescription'),
]
