from django.contrib import admin
from .models import (OPDVisit, IPDAdmission, DischargeRecord, ClinicalNote,
                     OperationNote, ConsultationRequest, PatientHandover,
                     MedicalFile, CBCResult, ChemistryResult, RadiologyOrder, RadiologyResult)


@admin.register(OPDVisit)
class OPDVisitAdmin(admin.ModelAdmin):
    list_display = ['visit_number', 'patient', 'visit_date', 'triage_level', 'status']


@admin.register(IPDAdmission)
class IPDAdmissionAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'patient', 'room_number', 'status', 'admission_date']


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ['patient', 'note_type', 'title', 'written_by', 'created_at']


@admin.register(OperationNote)
class OperationNoteAdmin(admin.ModelAdmin):
    list_display = ['operation_number', 'patient', 'procedure_name', 'surgeon', 'status']


@admin.register(ConsultationRequest)
class ConsultationRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'patient', 'requesting_doctor', 'consulting_doctor', 'status']


@admin.register(PatientHandover)
class PatientHandoverAdmin(admin.ModelAdmin):
    list_display = ['patient', 'shift', 'handover_from', 'handover_to', 'handover_date']


@admin.register(MedicalFile)
class MedicalFileAdmin(admin.ModelAdmin):
    list_display = ['patient', 'file_type', 'title', 'uploaded_by', 'created_at']


@admin.register(CBCResult)
class CBCResultAdmin(admin.ModelAdmin):
    list_display = ['patient', 'hemoglobin', 'wbc', 'platelets', 'recorded_at']


@admin.register(ChemistryResult)
class ChemistryResultAdmin(admin.ModelAdmin):
    list_display = ['patient', 'panel', 'glucose', 'creatinine', 'recorded_at']


@admin.register(RadiologyOrder)
class RadiologyOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'patient', 'modality', 'body_part', 'status']
