from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:invoice_pk>/payment/', views.add_payment, name='add_payment'),
    path('reports/', views.billing_reports, name='billing_reports'),
]
