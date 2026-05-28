from django.db import models
import uuid


class Patient(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    BLOOD_GROUPS = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]
    STATUS_CHOICES = [('active', 'Active'), ('inactive', 'Inactive'), ('deceased', 'Deceased')]

    patient_id = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='patient_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS, blank=True)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    marital_status = models.CharField(max_length=20, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    id_type = models.CharField(max_length=50, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    insurance_provider = models.CharField(max_length=150, blank=True)
    insurance_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def __str__(self):
        return f"{self.get_full_name()} ({self.patient_id})"


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL, null=True)
    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='medical_record')
    visit_date = models.DateTimeField(auto_now_add=True)
    chief_complaint = models.TextField()
    diagnosis = models.TextField()
    treatment = models.TextField()
    prescription = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    vital_signs = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f"Record: {self.patient} - {self.visit_date.date()}"


class Admission(models.Model):
    STATUS_CHOICES = [('admitted', 'Admitted'), ('discharged', 'Discharged'), ('transferred', 'Transferred')]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='admissions')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL, null=True)
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=50, default='General')
    admission_date = models.DateTimeField(auto_now_add=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    diagnosis = models.TextField()
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='admitted')

    def __str__(self):
        return f"{self.patient} - Room {self.room_number}"
