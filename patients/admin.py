from django.contrib import admin
from .models import Patient, MedicalRecord, Admission


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'first_name', 'last_name', 'phone', 'status']
    list_filter = ['status', 'gender', 'blood_group']
    search_fields = ['patient_id', 'first_name', 'last_name', 'phone']


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'visit_date']


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'room_number', 'status', 'admission_date']
