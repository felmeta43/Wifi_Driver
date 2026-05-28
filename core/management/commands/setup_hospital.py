from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.models import HospitalSettings, Department
from doctors.models import Specialization

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up initial hospital data (departments, specializations, admin user)'

    def handle(self, *args, **options):
        # Hospital settings
        hospital, created = HospitalSettings.objects.get_or_create(pk=1)
        if created:
            hospital.name = 'City General Hospital'
            hospital.tagline = 'Your Health, Our Priority'
            hospital.address = '123 Medical Drive, Health City, HC 10001'
            hospital.phone = '+1-800-HOSPITAL'
            hospital.email = 'info@citygeneralhospital.com'
            hospital.emergency_number = '911'
            hospital.bed_capacity = 250
            hospital.save()
            self.stdout.write(self.style.SUCCESS('Hospital settings created.'))

        # Departments
        departments = [
            ('Emergency', 'fa-ambulance'),
            ('Cardiology', 'fa-heart'),
            ('Neurology', 'fa-brain'),
            ('Orthopedics', 'fa-bone'),
            ('Pediatrics', 'fa-baby'),
            ('Gynecology', 'fa-venus'),
            ('Oncology', 'fa-ribbon'),
            ('Radiology', 'fa-x-ray'),
            ('Laboratory', 'fa-flask'),
            ('Pharmacy', 'fa-pills'),
            ('General Surgery', 'fa-scalpel'),
            ('Internal Medicine', 'fa-stethoscope'),
            ('Dermatology', 'fa-user-md'),
            ('Ophthalmology', 'fa-eye'),
            ('ENT', 'fa-ear'),
            ('Psychiatry', 'fa-brain'),
            ('Urology', 'fa-procedures'),
            ('Nephrology', 'fa-kidney'),
        ]
        for name, icon in departments:
            obj, created = Department.objects.get_or_create(name=name, defaults={'icon': icon})
            if created:
                self.stdout.write(f'  Department: {name}')

        # Specializations
        specializations = [
            'General Practitioner', 'Cardiologist', 'Neurologist', 'Orthopedic Surgeon',
            'Pediatrician', 'Gynecologist', 'Oncologist', 'Radiologist',
            'General Surgeon', 'Internist', 'Dermatologist', 'Ophthalmologist',
            'ENT Specialist', 'Psychiatrist', 'Urologist', 'Nephrologist',
            'Endocrinologist', 'Pulmonologist', 'Rheumatologist', 'Gastroenterologist',
            'Hematologist', 'Immunologist', 'Anesthesiologist', 'Pathologist',
        ]
        for name in specializations:
            obj, created = Specialization.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f'  Specialization: {name}')

        # Admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                email='admin@hospital.com',
                role='admin',
            )
            self.stdout.write(self.style.SUCCESS('Admin user created: admin / admin123'))
        else:
            self.stdout.write('Admin user already exists.')

        # Demo receptionist
        if not User.objects.filter(username='receptionist').exists():
            User.objects.create_user(
                username='receptionist',
                password='recep123',
                first_name='Jane',
                last_name='Doe',
                email='receptionist@hospital.com',
                role='receptionist',
            )
            self.stdout.write(self.style.SUCCESS('Receptionist user: receptionist / recep123'))

        self.stdout.write(self.style.SUCCESS('\nSetup complete! Login with: admin / admin123'))
