from django.db import models


class Specialization(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    STATUS_CHOICES = [('active', 'Active'), ('on_leave', 'On Leave'), ('inactive', 'Inactive')]

    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='doctor_profile')
    doctor_id = models.CharField(max_length=20, unique=True)
    specialization = models.ForeignKey(Specialization, on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey('core.Department', on_delete=models.SET_NULL, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M')
    date_of_birth = models.DateField(null=True, blank=True)
    qualification = models.CharField(max_length=300)
    experience_years = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bio = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    joining_date = models.DateField(auto_now_add=True)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"

    def get_full_name(self):
        return f"Dr. {self.user.get_full_name()}"


class DoctorSchedule(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'),
        (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday'),
    ]
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    max_patients = models.IntegerField(default=20)

    class Meta:
        unique_together = ('doctor', 'day_of_week')
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()}"
