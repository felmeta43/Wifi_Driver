from django.db import models


class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('antibiotic', 'Antibiotic'),
        ('antiviral', 'Antiviral'),
        ('antimalarial', 'Anti-Malarial'),
        ('antifungal', 'Anti-Fungal'),
        ('antiparasitic', 'Anti-Parasitic'),
        ('analgesic', 'Analgesic / Anti-Pain'),
        ('antiinflammatory', 'Anti-Inflammatory'),
        ('steroid', 'Steroid'),
        ('anticonvulsant', 'Anti-Convulsant'),
        ('cardiovascular', 'Cardiovascular Drug'),
        ('antihypertensive', 'Anti-Hypertensive'),
        ('gi', 'Gastrointestinal Drug'),
        ('respiratory', 'Respiratory Drug'),
        ('antidiabetic', 'Anti-Diabetic Drug'),
        ('emergency', 'Emergency Drug'),
        ('fluid', 'IV Fluid'),
        ('cephalosporin', 'Cephalosporin'),
        ('eye_ear', 'Eye / Ear Preparation'),
        ('vitamin', 'Vitamin & Supplement'),
        ('psychiatric', 'Psychiatric Drug'),
        ('hormonal', 'Hormonal Drug'),
        ('dermatological', 'Dermatological'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='antibiotic')
    manufacturer = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=30, default='pieces')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=10)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_low_stock(self):
        return self.stock_quantity <= self.minimum_stock

    def __str__(self):
        return f"{self.name} ({self.category})"


class Prescription(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('dispensed', 'Dispensed'), ('cancelled', 'Cancelled')]

    prescription_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.CASCADE, related_name='prescriptions')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='prescriptions')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    dispensed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Prescription {self.prescription_id} - {self.patient}"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)
    instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.medicine.name} - {self.dosage}"


class StockTransaction(models.Model):
    TYPE_CHOICES = [('in', 'Stock In'), ('out', 'Stock Out'), ('adjustment', 'Adjustment')]

    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=12, choices=TYPE_CHOICES)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.medicine} x{self.quantity}"
