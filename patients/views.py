from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
import uuid

from .models import Patient, MedicalRecord, Admission


def generate_patient_id():
    last = Patient.objects.order_by('-id').first()
    num = (last.id + 1) if last else 1
    return f"PAT{num:05d}"


@login_required
def patient_list(request):
    from django.core.paginator import Paginator
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    patients = Patient.objects.all().order_by('-registered_at')
    if query:
        patients = patients.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) |
            Q(patient_id__icontains=query) | Q(phone__icontains=query)
        )
    if status:
        patients = patients.filter(status=status)
    paginator = Paginator(patients, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'patients/patient_list.html', {
        'patients': page_obj, 'page_obj': page_obj,
        'query': query, 'status': status,
    })


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    medical_records = patient.medical_records.select_related('doctor__user').order_by('-visit_date')[:10]
    appointments = patient.appointments.select_related('doctor__user').order_by('-appointment_date')[:10]
    invoices = patient.invoices.order_by('-created_at')[:5]
    lab_orders = patient.lab_orders.order_by('-ordered_at')[:5]
    prescriptions = patient.prescriptions.order_by('-created_at')[:5]
    return render(request, 'patients/patient_detail.html', {
        'patient': patient, 'medical_records': medical_records,
        'appointments': appointments, 'invoices': invoices,
        'lab_orders': lab_orders, 'prescriptions': prescriptions,
    })


@login_required
def patient_create(request):
    if request.method == 'POST':
        data = request.POST
        patient = Patient(
            patient_id=generate_patient_id(),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            gender=data.get('gender'),
            date_of_birth=data.get('date_of_birth'),
            blood_group=data.get('blood_group', ''),
            phone=data.get('phone'),
            email=data.get('email', ''),
            address=data.get('address'),
            emergency_contact_name=data.get('emergency_contact_name', ''),
            emergency_contact_phone=data.get('emergency_contact_phone', ''),
            emergency_contact_relation=data.get('emergency_contact_relation', ''),
            marital_status=data.get('marital_status', ''),
            occupation=data.get('occupation', ''),
            nationality=data.get('nationality', ''),
            allergies=data.get('allergies', ''),
            chronic_conditions=data.get('chronic_conditions', ''),
            current_medications=data.get('current_medications', ''),
            insurance_provider=data.get('insurance_provider', ''),
            insurance_number=data.get('insurance_number', ''),
        )
        patient.save()
        messages.success(request, f'Patient {patient.get_full_name()} registered successfully! ID: {patient.patient_id}')
        return redirect('patient_detail', pk=patient.pk)
    return render(request, 'patients/patient_form.html', {
        'action': 'Register', 'blood_groups': Patient.BLOOD_GROUPS,
        'genders': Patient.GENDER_CHOICES,
    })


@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == 'POST':
        data = request.POST
        patient.first_name = data.get('first_name', patient.first_name)
        patient.last_name = data.get('last_name', patient.last_name)
        patient.gender = data.get('gender', patient.gender)
        patient.date_of_birth = data.get('date_of_birth', patient.date_of_birth)
        patient.blood_group = data.get('blood_group', patient.blood_group)
        patient.phone = data.get('phone', patient.phone)
        patient.email = data.get('email', patient.email)
        patient.address = data.get('address', patient.address)
        patient.emergency_contact_name = data.get('emergency_contact_name', patient.emergency_contact_name)
        patient.emergency_contact_phone = data.get('emergency_contact_phone', patient.emergency_contact_phone)
        patient.emergency_contact_relation = data.get('emergency_contact_relation', patient.emergency_contact_relation)
        patient.marital_status = data.get('marital_status', patient.marital_status)
        patient.occupation = data.get('occupation', patient.occupation)
        patient.nationality = data.get('nationality', patient.nationality)
        patient.allergies = data.get('allergies', patient.allergies)
        patient.chronic_conditions = data.get('chronic_conditions', patient.chronic_conditions)
        patient.current_medications = data.get('current_medications', patient.current_medications)
        patient.insurance_provider = data.get('insurance_provider', patient.insurance_provider)
        patient.insurance_number = data.get('insurance_number', patient.insurance_number)
        patient.status = data.get('status', patient.status)
        patient.save()
        messages.success(request, 'Patient updated successfully!')
        return redirect('patient_detail', pk=patient.pk)
    return render(request, 'patients/patient_form.html', {
        'action': 'Edit', 'patient': patient,
        'blood_groups': Patient.BLOOD_GROUPS, 'genders': Patient.GENDER_CHOICES,
    })


@login_required
def medical_record_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    from doctors.models import Doctor
    doctors = Doctor.objects.filter(status='active').select_related('user')
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        vitals = {
            'blood_pressure': request.POST.get('blood_pressure', ''),
            'temperature': request.POST.get('temperature', ''),
            'pulse': request.POST.get('pulse', ''),
            'weight': request.POST.get('weight', ''),
            'height': request.POST.get('height', ''),
            'oxygen_saturation': request.POST.get('oxygen_saturation', ''),
        }
        MedicalRecord.objects.create(
            patient=patient, doctor=doctor,
            chief_complaint=request.POST.get('chief_complaint'),
            diagnosis=request.POST.get('diagnosis'),
            treatment=request.POST.get('treatment'),
            prescription=request.POST.get('prescription', ''),
            notes=request.POST.get('notes', ''),
            follow_up_date=request.POST.get('follow_up_date') or None,
            vital_signs=vitals,
        )
        messages.success(request, 'Medical record added successfully!')
        return redirect('patient_detail', pk=patient.pk)
    return render(request, 'patients/medical_record_form.html', {
        'patient': patient, 'doctors': doctors
    })


@login_required
def admission_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    from doctors.models import Doctor
    doctors = Doctor.objects.filter(status='active').select_related('user')
    if request.method == 'POST':
        doctor = get_object_or_404(Doctor, pk=request.POST.get('doctor'))
        Admission.objects.create(
            patient=patient, doctor=doctor,
            room_number=request.POST.get('room_number'),
            room_type=request.POST.get('room_type', 'General'),
            diagnosis=request.POST.get('diagnosis'),
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Patient admitted successfully!')
        return redirect('patient_detail', pk=patient.pk)
    return render(request, 'patients/admission_form.html', {
        'patient': patient, 'doctors': doctors
    })
