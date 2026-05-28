from django.urls import path
from . import views

urlpatterns = [
    # OPD
    path('opd/', views.opd_list, name='opd_list'),
    path('opd/create/', views.opd_create, name='opd_create'),
    path('opd/<int:pk>/', views.opd_detail, name='opd_detail'),
    path('opd/<int:pk>/status/', views.opd_status_update, name='opd_status_update'),
    # IPD
    path('ipd/', views.ipd_list, name='ipd_list'),
    path('ipd/admit/', views.ipd_admit, name='ipd_admit'),
    path('ipd/<int:pk>/', views.ipd_detail, name='ipd_detail'),
    path('ipd/<int:pk>/discharge/', views.ipd_discharge, name='ipd_discharge'),
    # Clinical Notes
    path('notes/<int:patient_pk>/create/', views.clinical_note_create, name='clinical_note_create'),
    # Operation Notes
    path('operations/', views.operation_note_list, name='operation_note_list'),
    path('operations/create/', views.operation_note_create, name='operation_note_create'),
    path('operations/patient/<int:patient_pk>/create/', views.operation_note_create, name='operation_note_create_patient'),
    path('operations/<int:pk>/', views.operation_note_detail, name='operation_note_detail'),
    # Consultations
    path('consultations/', views.consultation_list, name='consultation_list'),
    path('consultations/create/', views.consultation_create, name='consultation_create'),
    path('consultations/patient/<int:patient_pk>/create/', views.consultation_create, name='consultation_create_patient'),
    path('consultations/<int:pk>/respond/', views.consultation_respond, name='consultation_respond'),
    # Handover
    path('handover/', views.handover_list, name='handover_list'),
    path('handover/create/', views.handover_create, name='handover_create'),
    path('handover/patient/<int:patient_pk>/create/', views.handover_create, name='handover_create_patient'),
    # Medical Files
    path('files/<int:patient_pk>/upload/', views.medical_file_upload, name='medical_file_upload'),
    # Machine Results
    path('lab/<int:order_pk>/cbc/', views.cbc_result_create, name='cbc_result_create'),
    path('lab/<int:order_pk>/chemistry/', views.chemistry_result_create, name='chemistry_result_create'),
    # Radiology
    path('radiology/', views.radiology_order_list, name='radiology_order_list'),
    path('radiology/create/', views.radiology_order_create, name='radiology_order_create'),
    path('radiology/<int:pk>/report/', views.radiology_report, name='radiology_report'),
]
