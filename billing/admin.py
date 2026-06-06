from django.contrib import admin
from .models import Invoice, InvoiceItem, Payment, DailyCollection


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['payment_date']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'patient', 'total_amount', 'paid_amount', 'status']
    list_filter = ['status']
    inlines = [InvoiceItemInline, PaymentInline]


@admin.register(DailyCollection)
class DailyCollectionAdmin(admin.ModelAdmin):
    list_display = ['cashier', 'collection_date', 'total_collected', 'transaction_count', 'status', 'submitted_at']
    list_filter = ['status', 'collection_date']
    readonly_fields = ['submitted_at', 'reviewed_at', 'created_at', 'updated_at']
