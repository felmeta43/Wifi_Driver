from django.db import models


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    invoice_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='invoices')
    appointment = models.ForeignKey('appointments.Appointment', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='invoice')
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def get_balance(self):
        return self.total_amount - self.paid_amount

    def __str__(self):
        return f"Invoice #{self.invoice_number} - {self.patient}"


class InvoiceItem(models.Model):
    CATEGORY_CHOICES = [
        ('consultation', 'Consultation'),
        ('procedure', 'Procedure'),
        ('lab', 'Laboratory'),
        ('pharmacy', 'Pharmacy'),
        ('room', 'Room/Bed'),
        ('surgery', 'Surgery'),
        ('other', 'Other'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=300)
    category = models.CharField(max_length=15, choices=CATEGORY_CHOICES, default='other')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} x{self.quantity}"


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('insurance', 'Insurance'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('check', 'Check'),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice}"


class DailyCollection(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted — Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    cashier = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        related_name='daily_collections', limit_choices_to={'role': 'cashier'}
    )
    collection_date = models.DateField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')

    # Breakdown by payment method (auto-populated from Payment records)
    cash_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    card_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    insurance_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mobile_money_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_transfer_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    check_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    instant_service_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_collected = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_count = models.IntegerField(default=0)

    notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    reviewed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_collections'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cashier', 'collection_date')
        ordering = ['-collection_date', 'cashier']

    def __str__(self):
        return f"{self.cashier.get_full_name()} – {self.collection_date} ({self.get_status_display()})"

    def is_pending(self):
        return self.status in ('draft', 'submitted')
