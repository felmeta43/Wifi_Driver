from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, date

from .models import HospitalSettings, Department, Notification
from patients.models import Patient
from doctors.models import Doctor
from appointments.models import Appointment
from billing.models import Invoice, Payment


@login_required
def dashboard(request):
    today = date.today()
    this_month_start = today.replace(day=1)

    stats = {
        'total_patients': Patient.objects.filter(status='active').count(),
        'total_doctors': Doctor.objects.filter(status='active').count(),
        'today_appointments': Appointment.objects.filter(appointment_date=today).count(),
        'pending_appointments': Appointment.objects.filter(
            appointment_date=today, status__in=['scheduled', 'confirmed']
        ).count(),
        'monthly_revenue': Payment.objects.filter(
            payment_date__date__gte=this_month_start
        ).aggregate(total=Sum('amount'))['total'] or 0,
        'pending_invoices': Invoice.objects.filter(status='pending').count(),
        'completed_today': Appointment.objects.filter(
            appointment_date=today, status='completed'
        ).count(),
    }

    recent_appointments = Appointment.objects.filter(
        appointment_date__gte=today - timedelta(days=7)
    ).select_related('patient', 'doctor__user').order_by('-appointment_date', '-appointment_time')[:10]

    recent_patients = Patient.objects.order_by('-registered_at')[:5]

    monthly_revenue = []
    for i in range(6, -1, -1):
        month_date = today - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year + 1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month + 1, day=1)
        rev = Payment.objects.filter(
            payment_date__date__gte=month_start,
            payment_date__date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_revenue.append({'month': month_date.strftime('%b'), 'revenue': float(rev)})

    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]

    return render(request, 'core/dashboard.html', {
        'stats': stats,
        'recent_appointments': recent_appointments,
        'recent_patients': recent_patients,
        'monthly_revenue': monthly_revenue,
        'notifications': notifications,
    })


@login_required
def hospital_settings_view(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    settings = HospitalSettings.get_settings()
    if request.method == 'POST':
        fields = [
            'name', 'tagline', 'address', 'phone', 'email', 'website',
            'registration_number', 'established_year', 'primary_color',
            'secondary_color', 'currency_symbol', 'currency_code',
            'tax_percentage', 'working_hours', 'emergency_number',
            'bed_capacity', 'about', 'facebook_url', 'twitter_url',
            'instagram_url', 'linkedin_url',
        ]
        for field in fields:
            if field in request.POST:
                setattr(settings, field, request.POST[field])
        if 'logo' in request.FILES:
            settings.logo = request.FILES['logo']
        settings.save()
        messages.success(request, 'Hospital settings updated successfully!')
        return redirect('hospital_settings')
    return render(request, 'core/hospital_settings.html', {'settings': settings})


@login_required
def departments(request):
    dept_list = Department.objects.annotate(doctor_count=Count('doctor')).all()
    return render(request, 'core/departments.html', {'departments': dept_list})


@login_required
def department_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        icon = request.POST.get('icon', 'fa-hospital')
        Department.objects.create(name=name, description=description, icon=icon)
        messages.success(request, 'Department created successfully!')
        return redirect('departments')
    return render(request, 'core/department_form.html', {'action': 'Create'})


@login_required
def department_edit(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        dept.name = request.POST.get('name', dept.name)
        dept.description = request.POST.get('description', dept.description)
        dept.icon = request.POST.get('icon', dept.icon)
        dept.save()
        messages.success(request, 'Department updated successfully!')
        return redirect('departments')
    return render(request, 'core/department_form.html', {'dept': dept, 'action': 'Edit'})


@login_required
def notifications_view(request):
    notifs = Notification.objects.filter(user=request.user)
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifs})
