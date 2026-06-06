from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:invoice_pk>/payment/', views.add_payment, name='add_payment'),
    path('reports/', views.billing_reports, name='billing_reports'),
    # Daily Collection
    path('daily-collection/', views.daily_collection_submit, name='daily_collection_submit'),
    path('collections/', views.collection_list, name='collection_list'),
    path('collections/<int:pk>/review/', views.collection_review, name='collection_review'),
]
