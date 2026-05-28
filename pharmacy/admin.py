from django.contrib import admin
from .models import Medicine, Prescription, PrescriptionItem, StockTransaction


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'stock_quantity', 'unit_price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'generic_name']


class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['prescription_id', 'patient', 'doctor', 'status', 'created_at']
    inlines = [PrescriptionItemInline]


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ['medicine', 'transaction_type', 'quantity', 'created_at']
