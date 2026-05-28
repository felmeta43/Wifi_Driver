from django.db import models


class HospitalSettings(models.Model):
    name = models.CharField(max_length=200, default='City General Hospital')
    tagline = models.CharField(max_length=300, blank=True, default='Your Health, Our Priority')
    logo = models.ImageField(upload_to='hospital/', blank=True, null=True)
    address = models.TextField(default='123 Medical Drive, Health City')
    phone = models.CharField(max_length=20, default='+1-800-HOSPITAL')
    email = models.EmailField(default='info@hospital.com')
    website = models.URLField(blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    established_year = models.CharField(max_length=4, blank=True)
    primary_color = models.CharField(max_length=7, default='#0d6efd')
    secondary_color = models.CharField(max_length=7, default='#198754')
    currency_symbol = models.CharField(max_length=5, default='$')
    currency_code = models.CharField(max_length=3, default='USD')
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    working_hours = models.CharField(max_length=100, default='24/7')
    emergency_number = models.CharField(max_length=20, default='911')
    bed_capacity = models.IntegerField(default=100)
    about = models.TextField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Hospital Settings'
        verbose_name_plural = 'Hospital Settings'

    def __str__(self):
        return self.name

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Department(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fa-hospital', help_text='FontAwesome icon class')
    head_doctor = models.ForeignKey(
        'doctors.Doctor', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='headed_departments'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Notification(models.Model):
    TYPES = [
        ('appointment', 'Appointment'),
        ('billing', 'Billing'),
        ('lab', 'Lab Result'),
        ('pharmacy', 'Pharmacy'),
        ('general', 'General'),
    ]
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} -> {self.user.username}"
