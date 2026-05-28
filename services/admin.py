from django.contrib import admin
from .models import ServiceCategory, Service, ServiceOrder, ServiceOrderItem, InstantService


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']


class ServiceOrderItemInline(admin.TabularInline):
    model = ServiceOrderItem
    extra = 1


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'service_type', 'price', 'is_active']
    list_filter = ['service_type', 'category', 'is_active']
    search_fields = ['name', 'code']


@admin.register(ServiceOrder)
class ServiceOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'patient', 'status', 'created_at']
    inlines = [ServiceOrderItemInline]


@admin.register(InstantService)
class InstantServiceAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'patient', 'service', 'total_price', 'created_at']
