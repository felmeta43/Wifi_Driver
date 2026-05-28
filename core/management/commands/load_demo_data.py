from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta, time
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Load demo data for testing'

    def handle(self, *args, **options):
        from core.models import Department
        from doctors.models import Doctor, Specialization, DoctorSchedule
        from patients.models import Patient
        from appointments.models import Appointment
        from billing.models import Invoice, InvoiceItem, Payment
        from pharmacy.models import Medicine, Prescription, PrescriptionItem, StockTransaction
        from laboratory.models import LabTest, LabOrder, LabResult

        # Demo doctors
        specs = list(Specialization.objects.all()[:6])
        depts = list(Department.objects.all()[:6])
        doctor_data = [
            ('dr.smith', 'John', 'Smith', 0),
            ('dr.johnson', 'Emily', 'Johnson', 1),
            ('dr.patel', 'Raj', 'Patel', 2),
            ('dr.williams', 'Sarah', 'Williams', 3),
            ('dr.chen', 'Michael', 'Chen', 4),
        ]
        doctors = []
        for i, (uname, first, last, spec_idx) in enumerate(doctor_data):
            if not User.objects.filter(username=uname).exists():
                u = User.objects.create_user(username=uname, password='doctor123',
                    first_name=first, last_name=last, role='doctor',
                    email=f'{uname}@hospital.com')
                spec = specs[spec_idx] if spec_idx < len(specs) else specs[0]
                dept = depts[spec_idx] if spec_idx < len(depts) else depts[0]
                d = Doctor.objects.create(user=u, doctor_id=f'DOC{i+1:04d}',
                    specialization=spec, department=dept,
                    qualification='MBBS, MD', experience_years=random.randint(3, 20),
                    consultation_fee=random.choice([50, 75, 100, 150]),
                    gender=random.choice(['M', 'F']))
                for day in [0, 1, 2, 3, 4]:
                    DoctorSchedule.objects.get_or_create(doctor=d, day_of_week=day,
                        defaults={'start_time': time(9, 0), 'end_time': time(17, 0), 'max_patients': 20})
                doctors.append(d)
                self.stdout.write(f'  Doctor: Dr. {first} {last}')
            else:
                doc = Doctor.objects.filter(user__username=uname).first()
                if doc:
                    doctors.append(doc)

        # Demo patients
        patient_data = [
            ('Alice', 'Johnson', 'F', '1985-03-15', 'A+', '+1-555-0101'),
            ('Bob', 'Williams', 'M', '1972-07-22', 'B+', '+1-555-0102'),
            ('Carol', 'Davis', 'F', '1990-11-08', 'O+', '+1-555-0103'),
            ('David', 'Martinez', 'M', '1965-05-30', 'AB+', '+1-555-0104'),
            ('Emma', 'Wilson', 'F', '1995-09-14', 'A-', '+1-555-0105'),
            ('Frank', 'Taylor', 'M', '1980-01-25', 'B-', '+1-555-0106'),
            ('Grace', 'Anderson', 'F', '2001-12-03', 'O-', '+1-555-0107'),
            ('Henry', 'Brown', 'M', '1958-06-18', 'A+', '+1-555-0108'),
        ]
        patients = []
        for i, (first, last, gender, dob, bg, phone) in enumerate(patient_data):
            pid = f'PAT{i+1:05d}'
            if not Patient.objects.filter(patient_id=pid).exists():
                p = Patient.objects.create(
                    patient_id=pid, first_name=first, last_name=last,
                    gender=gender, date_of_birth=dob, blood_group=bg,
                    phone=phone, email=f'{first.lower()}.{last.lower()}@email.com',
                    address=f'{random.randint(100,999)} Main Street, City',
                    emergency_contact_name='Emergency Contact',
                    emergency_contact_phone='+1-555-9999',
                )
                patients.append(p)
                self.stdout.write(f'  Patient: {first} {last}')
            else:
                patients.append(Patient.objects.get(patient_id=pid))

        # Demo appointments
        apt_count = Appointment.objects.count()
        if apt_count < 10 and doctors and patients:
            today = date.today()
            for i in range(12):
                delta = random.randint(-7, 7)
                apt_date = today + timedelta(days=delta)
                apt_time = time(random.randint(9, 16), random.choice([0, 30]))
                status = 'scheduled' if delta >= 0 else random.choice(['completed', 'completed', 'cancelled'])
                apt_id = f'APT{Appointment.objects.count()+1:06d}'
                apt = Appointment.objects.create(
                    appointment_id=apt_id,
                    patient=random.choice(patients),
                    doctor=random.choice(doctors),
                    appointment_date=apt_date,
                    appointment_time=apt_time,
                    appointment_type=random.choice(['consultation', 'follow_up', 'routine']),
                    status=status,
                    reason=random.choice([
                        'Regular checkup', 'Chest pain evaluation', 'Follow-up visit',
                        'Headache and dizziness', 'Fever and cough', 'Annual physical',
                    ]),
                    created_by=User.objects.filter(role='admin').first(),
                )
            self.stdout.write(f'  Created demo appointments')

        # Demo medicines
        medicine_data = [
            ('Paracetamol 500mg', 'Paracetamol', 'tablet', 0.05, 500),
            ('Amoxicillin 250mg', 'Amoxicillin', 'capsule', 0.20, 200),
            ('Ibuprofen 400mg', 'Ibuprofen', 'tablet', 0.10, 300),
            ('Metformin 500mg', 'Metformin', 'tablet', 0.15, 400),
            ('Lisinopril 10mg', 'Lisinopril', 'tablet', 0.25, 150),
            ('Atorvastatin 20mg', 'Atorvastatin', 'tablet', 0.30, 200),
            ('Salbutamol Inhaler', 'Salbutamol', 'inhaler', 8.50, 50),
            ('Cough Syrup 100ml', 'Dextromethorphan', 'syrup', 3.50, 100),
            ('Normal Saline 0.9%', 'Sodium Chloride', 'injection', 1.20, 80),
            ('Cetirizine 10mg', 'Cetirizine', 'tablet', 0.08, 250),
        ]
        for name, generic, cat, price, stock in medicine_data:
            if not Medicine.objects.filter(name=name).exists():
                Medicine.objects.create(name=name, generic_name=generic, category=cat,
                    unit_price=price, stock_quantity=stock, minimum_stock=20)
                self.stdout.write(f'  Medicine: {name}')

        # Demo lab tests
        lab_test_data = [
            ('Complete Blood Count (CBC)', 10.00, 'See report', 'count', '2 hours'),
            ('Blood Glucose (Fasting)', 5.00, '70-100 mg/dL', 'mg/dL', '1 hour'),
            ('HbA1c', 15.00, '4.0-5.6%', '%', '3 hours'),
            ('Lipid Panel', 20.00, 'See report', 'mg/dL', '4 hours'),
            ('Liver Function Test', 25.00, 'See report', 'U/L', '4 hours'),
            ('Kidney Function Test', 20.00, 'See report', 'mg/dL', '3 hours'),
            ('Thyroid Function Test', 30.00, 'See report', 'mIU/L', '6 hours'),
            ('Urinalysis', 8.00, 'See report', 'N/A', '1 hour'),
            ('ECG', 15.00, 'Normal sinus rhythm', 'N/A', '30 minutes'),
            ('Chest X-Ray', 40.00, 'Normal', 'N/A', '1 hour'),
        ]
        for name, price, normal, unit, tat in lab_test_data:
            if not LabTest.objects.filter(name=name).exists():
                LabTest.objects.create(name=name, price=price, normal_range=normal,
                    unit=unit, turnaround_time=tat)
                self.stdout.write(f'  Lab Test: {name}')

        # Demo invoices
        if Invoice.objects.count() < 3 and patients:
            for i, patient in enumerate(patients[:4]):
                inv_num = f'INV{Invoice.objects.count()+1:06d}'
                inv = Invoice.objects.create(
                    invoice_number=inv_num, patient=patient,
                    created_by=User.objects.filter(role='admin').first(),
                    subtotal=150.00, total_amount=150.00,
                    status=random.choice(['paid', 'pending', 'paid']),
                    paid_amount=150.00 if random.choice([True, False]) else 0,
                )
                InvoiceItem.objects.create(invoice=inv, description='Consultation Fee',
                    category='consultation', quantity=1, unit_price=100.00, total_price=100.00)
                InvoiceItem.objects.create(invoice=inv, description='Lab Tests',
                    category='lab', quantity=1, unit_price=50.00, total_price=50.00)
                if inv.paid_amount > 0:
                    Payment.objects.create(invoice=inv, amount=150.00, method='cash',
                        received_by=User.objects.filter(role='admin').first())
                    inv.status = 'paid'
                    inv.save()
            self.stdout.write('  Created demo invoices')

        # Demo service categories and services
        from services.models import ServiceCategory, Service
        service_cat_data = [
            ('Consultation', 'fa-user-md', 'Doctor consultation services'),
            ('Laboratory', 'fa-flask', 'Lab tests and diagnostics'),
            ('Radiology', 'fa-x-ray', 'Imaging and radiology services'),
            ('Procedures', 'fa-syringe', 'Minor and major procedures'),
            ('Pharmacy', 'fa-pills', 'Medication and pharmacy'),
            ('Room & Board', 'fa-bed', 'Inpatient accommodation'),
            ('Emergency', 'fa-ambulance', 'Emergency services'),
            ('Therapy', 'fa-hands-helping', 'Physiotherapy and rehabilitation'),
        ]
        categories = {}
        for name, icon, desc in service_cat_data:
            cat, created = ServiceCategory.objects.get_or_create(name=name,
                defaults={'icon': icon, 'description': desc})
            categories[name] = cat
            if created:
                self.stdout.write(f'  Category: {name}')

        service_data = [
            ('General Consultation', 'CONS-001', 'opd', 'Consultation', 50.00, 30),
            ('Specialist Consultation', 'CONS-002', 'opd', 'Consultation', 100.00, 30),
            ('Emergency Consultation', 'CONS-003', 'emergency', 'Emergency', 150.00, 30),
            ('CBC Test', 'LAB-001', 'diagnostic', 'Laboratory', 10.00, 60),
            ('Blood Glucose', 'LAB-002', 'diagnostic', 'Laboratory', 5.00, 45),
            ('Liver Function Test', 'LAB-003', 'diagnostic', 'Laboratory', 25.00, 120),
            ('Chest X-Ray', 'RAD-001', 'diagnostic', 'Radiology', 40.00, 30),
            ('Abdominal Ultrasound', 'RAD-002', 'diagnostic', 'Radiology', 80.00, 45),
            ('CT Scan Head', 'RAD-003', 'diagnostic', 'Radiology', 200.00, 60),
            ('IV Cannulation', 'PROC-001', 'procedure', 'Procedures', 15.00, 20),
            ('Wound Dressing', 'PROC-002', 'procedure', 'Procedures', 20.00, 30),
            ('Suturing (per stitch)', 'PROC-003', 'procedure', 'Procedures', 10.00, 30),
            ('General Ward (per day)', 'ROOM-001', 'ipd', 'Room & Board', 80.00, 1440),
            ('Private Room (per day)', 'ROOM-002', 'ipd', 'Room & Board', 200.00, 1440),
            ('ICU (per day)', 'ROOM-003', 'ipd', 'Room & Board', 500.00, 1440),
            ('Physiotherapy Session', 'THER-001', 'therapy', 'Therapy', 60.00, 60),
        ]
        for name, code, stype, cat_name, price, duration in service_data:
            if not Service.objects.filter(code=code).exists():
                Service.objects.create(
                    name=name, code=code, service_type=stype,
                    category=categories.get(cat_name, list(categories.values())[0]),
                    price=price, duration_minutes=duration,
                )
                self.stdout.write(f'  Service: {name}')

        self.stdout.write(self.style.SUCCESS('\nDemo data loaded successfully!'))
