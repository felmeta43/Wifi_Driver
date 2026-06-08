from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from datetime import date

from .models import Appointment
from patients.models import Patient
from doctors.models import Doctor


def generate_appointment_id():
    last = Appointment.objects.order_by('-id').first()
    num = (last.id + 1) if last else 1
    return f"APT{num:06d}"


@login_required
def appointment_list(request):
    from django.core.paginator import Paginator
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    appointments = Appointment.objects.select_related('patient', 'doctor__user').order_by('-appointment_date', '-appointment_time')
    if query:
        appointments = appointments.filter(
            Q(appointment_id__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query) |
            Q(doctor__user__first_name__icontains=query)
        )
    if status:
        appointments = appointments.filter(status=status)
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)
    paginator = Paginator(appointments, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'appointments/appointment_list.html', {
        'appointments': page_obj, 'page_obj': page_obj,
        'query': query, 'status': status,
        'date_filter': date_filter, 'status_choices': Appointment.STATUS_CHOICES,
    })


@login_required
def appointment_detail(request, pk):
    apt = get_object_or_404(Appointment, pk=pk)
    return render(request, 'appointments/appointment_detail.html', {'appointment': apt})


@login_required
def appointment_create(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user', 'specialization')
    if request.method == 'POST':
        data = request.POST
        patient = get_object_or_404(Patient, pk=data.get('patient'))
        doctor = get_object_or_404(Doctor, pk=data.get('doctor'))
        Appointment.objects.create(
            appointment_id=generate_appointment_id(),
            patient=patient, doctor=doctor,
            appointment_date=data.get('appointment_date'),
            appointment_time=data.get('appointment_time'),
            appointment_type=data.get('appointment_type', 'consultation'),
            reason=data.get('reason'),
            notes=data.get('notes', ''),
            created_by=request.user,
        )
        messages.success(request, 'Appointment scheduled successfully!')
        return redirect('appointment_list')
    return render(request, 'appointments/appointment_form.html', {
        'patients': patients, 'doctors': doctors,
        'type_choices': Appointment.TYPE_CHOICES,
        'today': date.today().isoformat(),
    })


@login_required
def appointment_edit(request, pk):
    apt = get_object_or_404(Appointment, pk=pk)
    patients = Patient.objects.filter(status='active')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    if request.method == 'POST':
        data = request.POST
        apt.patient = get_object_or_404(Patient, pk=data.get('patient'))
        apt.doctor = get_object_or_404(Doctor, pk=data.get('doctor'))
        apt.appointment_date = data.get('appointment_date')
        apt.appointment_time = data.get('appointment_time')
        apt.appointment_type = data.get('appointment_type', apt.appointment_type)
        apt.status = data.get('status', apt.status)
        apt.reason = data.get('reason', apt.reason)
        apt.notes = data.get('notes', apt.notes)
        apt.save()
        messages.success(request, 'Appointment updated successfully!')
        return redirect('appointment_detail', pk=apt.pk)
    return render(request, 'appointments/appointment_form.html', {
        'appointment': apt, 'patients': patients, 'doctors': doctors,
        'type_choices': Appointment.TYPE_CHOICES,
        'status_choices': Appointment.STATUS_CHOICES,
    })


@login_required
def appointment_status_update(request, pk):
    apt = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        apt.status = request.POST.get('status', apt.status)
        apt.save()
        messages.success(request, f'Appointment status updated to {apt.get_status_display()}.')
    return redirect('appointment_detail', pk=apt.pk)


@login_required
def today_appointments(request):
    today = date.today()
    appointments = Appointment.objects.filter(appointment_date=today).select_related(
        'patient', 'doctor__user'
    ).order_by('appointment_time')
    return render(request, 'appointments/today_appointments.html', {
        'appointments': appointments, 'today': today
    })
