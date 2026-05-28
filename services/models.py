from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-concierge-bell')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Service Categories'

    def __str__(self):
        return self.name


class Service(models.Model):
    TYPE_CHOICES = [
        ('opd', 'OPD'),
        ('ipd', 'IPD'),
        ('procedure', 'Procedure'),
        ('diagnostic', 'Diagnostic'),
        ('therapy', 'Therapy'),
        ('surgery', 'Surgery'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ]
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='services')
    name = models.CharField(max_length=250)
    code = models.CharField(max_length=30, unique=True)
    service_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='opd')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    duration_minutes = models.IntegerField(default=30, help_text='Estimated duration')
    requires_doctor = models.BooleanField(default=True)
    department = models.ForeignKey('core.Department', on_delete=models.SET_NULL,
                                   null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} – {self.name}"


class ServiceOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    order_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='service_orders')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL,
                               null=True, blank=True)
    admission = models.ForeignKey('clinical.IPDAdmission', on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='service_orders')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    requested_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                     null=True, related_name='service_orders_requested')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def get_total(self):
        return sum(i.total_price for i in self.items.all())

    def __str__(self):
        return f"{self.order_number} – {self.patient}"


class ServiceOrderItem(models.Model):
    order = models.ForeignKey(ServiceOrder, on_delete=models.CASCADE, related_name='items')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                     null=True, blank=True)
    performed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.service.name} x{self.quantity}"


class InstantService(models.Model):
    """Quick counter service — walk-in or emergency billing."""
    receipt_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='instant_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, default='cash')
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_number} – {self.patient} – {self.service.name}"
