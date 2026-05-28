from django.contrib import admin
from .models import LabTest, LabOrder, LabResult


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'turnaround_time', 'is_active']


class LabResultInline(admin.TabularInline):
    model = LabResult
    extra = 0


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'patient', 'doctor', 'status', 'ordered_at']
    inlines = [LabResultInline]
