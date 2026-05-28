from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Doctor, DoctorSchedule, Specialization
from accounts.models import User
from core.models import Department


def generate_doctor_id():
    last = Doctor.objects.order_by('-id').first()
    num = (last.id + 1) if last else 1
    return f"DOC{num:04d}"


@login_required
def doctor_list(request):
    query = request.GET.get('q', '')
    dept_id = request.GET.get('department', '')
    doctors = Doctor.objects.select_related('user', 'specialization', 'department').all()
    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query) |
            Q(doctor_id__icontains=query) | Q(specialization__name__icontains=query)
        )
    if dept_id:
        doctors = doctors.filter(department_id=dept_id)
    departments = Department.objects.filter(is_active=True)
    return render(request, 'doctors/doctor_list.html', {
        'doctors': doctors, 'query': query, 'departments': departments, 'selected_dept': dept_id
    })


@login_required
def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    schedules = doctor.schedules.all().order_by('day_of_week')
    appointments = doctor.appointments.select_related('patient').order_by('-appointment_date')[:10]
    return render(request, 'doctors/doctor_detail.html', {
        'doctor': doctor, 'schedules': schedules, 'appointments': appointments
    })


@login_required
def doctor_create(request):
    if not (request.user.role in ['admin', 'receptionist'] or request.user.is_superuser):
        messages.error(request, 'Access denied.')
        return redirect('doctor_list')
    specializations = Specialization.objects.all()
    departments = Department.objects.filter(is_active=True)
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'doctors/doctor_form.html', {
                'action': 'Add', 'specializations': specializations, 'departments': departments
            })
        user = User.objects.create_user(
            username=username, password=data.get('password'),
            first_name=data.get('first_name'), last_name=data.get('last_name'),
            email=data.get('email', ''), role='doctor', phone=data.get('phone', '')
        )
        spec_id = data.get('specialization')
        spec = get_object_or_404(Specialization, pk=spec_id) if spec_id else None
        dept_id = data.get('department')
        dept = Department.objects.filter(pk=dept_id).first() if dept_id else None
        Doctor.objects.create(
            user=user, doctor_id=generate_doctor_id(), specialization=spec, department=dept,
            gender=data.get('gender', 'M'),
            date_of_birth=data.get('date_of_birth') or None,
            qualification=data.get('qualification', ''),
            experience_years=int(data.get('experience_years', 0)),
            consultation_fee=float(data.get('consultation_fee', 0)),
            bio=data.get('bio', ''), address=data.get('address', ''),
            blood_group=data.get('blood_group', ''),
        )
        messages.success(request, f'Doctor {user.get_full_name()} added successfully!')
        return redirect('doctor_list')
    return render(request, 'doctors/doctor_form.html', {
        'action': 'Add', 'specializations': specializations, 'departments': departments,
        'genders': Doctor.GENDER_CHOICES,
    })


@login_required
def doctor_edit(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    specializations = Specialization.objects.all()
    departments = Department.objects.filter(is_active=True)
    if request.method == 'POST':
        data = request.POST
        user = doctor.user
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.email = data.get('email', user.email)
        user.phone = data.get('phone', user.phone)
        user.save()
        spec_id = data.get('specialization')
        doctor.specialization = get_object_or_404(Specialization, pk=spec_id) if spec_id else doctor.specialization
        dept_id = data.get('department')
        doctor.department = Department.objects.filter(pk=dept_id).first() if dept_id else doctor.department
        doctor.gender = data.get('gender', doctor.gender)
        doctor.qualification = data.get('qualification', doctor.qualification)
        doctor.experience_years = int(data.get('experience_years', doctor.experience_years))
        doctor.consultation_fee = float(data.get('consultation_fee', doctor.consultation_fee))
        doctor.bio = data.get('bio', doctor.bio)
        doctor.status = data.get('status', doctor.status)
        doctor.save()
        messages.success(request, 'Doctor updated successfully!')
        return redirect('doctor_detail', pk=doctor.pk)
    return render(request, 'doctors/doctor_form.html', {
        'action': 'Edit', 'doctor': doctor,
        'specializations': specializations, 'departments': departments,
        'genders': Doctor.GENDER_CHOICES,
    })


@login_required
def schedule_manage(request, doctor_pk):
    doctor = get_object_or_404(Doctor, pk=doctor_pk)
    if request.method == 'POST':
        DoctorSchedule.objects.filter(doctor=doctor).delete()
        days = request.POST.getlist('day_of_week')
        starts = request.POST.getlist('start_time')
        ends = request.POST.getlist('end_time')
        maxes = request.POST.getlist('max_patients')
        for i, day in enumerate(days):
            DoctorSchedule.objects.create(
                doctor=doctor, day_of_week=int(day),
                start_time=starts[i], end_time=ends[i],
                max_patients=int(maxes[i]) if i < len(maxes) else 20,
            )
        messages.success(request, 'Schedule updated successfully!')
        return redirect('doctor_detail', pk=doctor.pk)
    schedules = {s.day_of_week: s for s in doctor.schedules.all()}
    return render(request, 'doctors/schedule_form.html', {
        'doctor': doctor, 'schedules': schedules,
        'days': DoctorSchedule.DAY_CHOICES,
    })


@login_required
def specialization_list(request):
    specs = Specialization.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        desc = request.POST.get('description', '')
        Specialization.objects.create(name=name, description=desc)
        messages.success(request, 'Specialization added!')
        return redirect('specialization_list')
    return render(request, 'doctors/specialization_list.html', {'specializations': specs})
