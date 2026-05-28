from django.db import models


class LabTest(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    normal_range = models.CharField(max_length=200, blank=True)
    unit = models.CharField(max_length=50, blank=True)
    turnaround_time = models.CharField(max_length=50, blank=True, help_text='e.g., 2 hours, 1 day')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class LabOrder(models.Model):
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('sample_collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='lab_orders')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='lab_orders')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='lab_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    notes = models.TextField(blank=True)
    ordered_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    technician = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='lab_orders')

    class Meta:
        ordering = ['-ordered_at']

    def __str__(self):
        return f"Lab Order {self.order_id} - {self.patient}"


class LabResult(models.Model):
    order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='results')
    test = models.ForeignKey(LabTest, on_delete=models.CASCADE)
    result_value = models.CharField(max_length=500)
    unit = models.CharField(max_length=50, blank=True)
    normal_range = models.CharField(max_length=200, blank=True)
    is_abnormal = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.test.name}: {self.result_value} {self.unit}"
