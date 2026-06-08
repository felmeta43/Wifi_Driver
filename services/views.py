from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone

from .models import ServiceCategory, Service, ServiceOrder, ServiceOrderItem, InstantService
from patients.models import Patient
from doctors.models import Doctor


def gen_order_number():
    last = ServiceOrder.objects.order_by('-id').first()
    return f"SVO{(last.id + 1 if last else 1):06d}"

def gen_receipt_number():
    last = InstantService.objects.order_by('-id').first()
    return f"ISV{(last.id + 1 if last else 1):06d}"


# ── Service Catalog ──────────────────────────────────────────────────────────

@login_required
def service_list(request):
    query = request.GET.get('q', '')
    stype = request.GET.get('type', '')
    services = Service.objects.select_related('category', 'department').filter(is_active=True)
    if query:
        services = services.filter(Q(name__icontains=query) | Q(code__icontains=query))
    if stype:
        services = services.filter(service_type=stype)
    categories = ServiceCategory.objects.filter(is_active=True)
    return render(request, 'services/service_list.html', {
        'services': services, 'query': query, 'stype': stype,
        'categories': categories, 'type_choices': Service.TYPE_CHOICES,
    })


@login_required
def service_create(request):
    from core.models import Department
    departments = Department.objects.filter(is_active=True)
    categories = ServiceCategory.objects.filter(is_active=True)
    if request.method == 'POST':
        d = request.POST
        cat_id = d.get('category')
        dept_id = d.get('department')
        Service.objects.create(
            name=d['name'], code=d['code'],
            service_type=d.get('service_type', 'opd'),
            category=ServiceCategory.objects.filter(pk=cat_id).first() if cat_id else None,
            department=Department.objects.filter(pk=dept_id).first() if dept_id else None,
            price=float(d.get('price', 0)),
            duration_minutes=int(d.get('duration_minutes', 30)),
            description=d.get('description', ''),
            requires_doctor='requires_doctor' in d,
        )
        messages.success(request, 'Service created successfully!')
        return redirect('service_list')
    return render(request, 'services/service_form.html', {
        'action': 'Create', 'departments': departments, 'categories': categories,
        'type_choices': Service.TYPE_CHOICES,
    })


@login_required
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    from core.models import Department
    departments = Department.objects.filter(is_active=True)
    categories = ServiceCategory.objects.filter(is_active=True)
    if request.method == 'POST':
        d = request.POST
        service.name = d.get('name', service.name)
        service.price = float(d.get('price', service.price))
        service.service_type = d.get('service_type', service.service_type)
        service.description = d.get('description', service.description)
        service.duration_minutes = int(d.get('duration_minutes', service.duration_minutes))
        service.is_active = 'is_active' in d
        service.save()
        messages.success(request, 'Service updated!')
        return redirect('service_list')
    return render(request, 'services/service_form.html', {
        'action': 'Edit', 'service': service, 'departments': departments,
        'categories': categories, 'type_choices': Service.TYPE_CHOICES,
    })


@login_required
def service_update_price(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        new_price = request.POST.get('price', '').strip()
        if new_price:
            service.price = float(new_price)
            service.save(update_fields=['price'])
            messages.success(request, f'Price updated for {service.name}.')
        else:
            messages.error(request, 'Price cannot be empty.')
    return redirect('service_list')


@login_required
def category_list(request):
    cats = ServiceCategory.objects.all()
    if request.method == 'POST':
        ServiceCategory.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            icon=request.POST.get('icon', 'fa-concierge-bell'),
        )
        messages.success(request, 'Category created!')
        return redirect('service_category_list')
    return render(request, 'services/category_list.html', {'categories': cats})


# ── Service Orders ───────────────────────────────────────────────────────────

@login_required
def service_order_list(request):
    orders = ServiceOrder.objects.select_related('patient', 'doctor__user').order_by('-created_at')
    query = request.GET.get('q', '')
    if query:
        orders = orders.filter(
            Q(order_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )
    return render(request, 'services/order_list.html', {'orders': orders, 'query': query})


@login_required
def service_order_create(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    services = Service.objects.filter(is_active=True).order_by('name')
    pre_patient = request.GET.get('patient')
    pre_doctor = request.GET.get('doctor')
    if request.method == 'POST':
        d = request.POST
        patient = get_object_or_404(Patient, pk=d['patient'])
        doc_id = d.get('doctor')
        doctor = Doctor.objects.filter(pk=doc_id).first() if doc_id else None
        order = ServiceOrder.objects.create(
            order_number=gen_order_number(), patient=patient, doctor=doctor,
            notes=d.get('notes', ''), requested_by=request.user,
        )
        svc_ids = d.getlist('service')
        qtys = d.getlist('quantity')
        for i, sid in enumerate(svc_ids):
            svc = Service.objects.filter(pk=sid).first()
            if svc:
                qty = int(qtys[i]) if i < len(qtys) else 1
                ServiceOrderItem.objects.create(
                    order=order, service=svc, quantity=qty,
                    unit_price=svc.price, total_price=svc.price * qty,
                )
        messages.success(request, f'Service order {order.order_number} created!')
        return redirect('service_order_detail', pk=order.pk)
    return render(request, 'services/order_form.html', {
        'patients': patients, 'doctors': doctors, 'services': services,
        'pre_patient': pre_patient, 'pre_doctor': pre_doctor,
    })


@login_required
def service_order_detail(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    items = order.items.select_related('service', 'performed_by').all()
    return render(request, 'services/order_detail.html', {'order': order, 'items': items})


@login_required
def service_order_complete(request, pk):
    order = get_object_or_404(ServiceOrder, pk=pk)
    if request.method == 'POST':
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        messages.success(request, 'Service order marked complete.')
    return redirect('service_order_detail', pk=pk)


# ── Instant Services ─────────────────────────────────────────────────────────

@login_required
def instant_service(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    services = Service.objects.filter(is_active=True).order_by('name')
    recent = InstantService.objects.select_related('patient', 'service').order_by('-created_at')[:20]
    if request.method == 'POST':
        if request.user.role not in ('admin', 'cashier') and not request.user.is_superuser:
            messages.error(request, 'Only cashiers can process instant service payments.')
            return redirect('instant_service')
        d = request.POST
        patient = get_object_or_404(Patient, pk=d['patient'])
        svc = get_object_or_404(Service, pk=d['service'])
        qty = int(d.get('quantity', 1))
        inst = InstantService.objects.create(
            receipt_number=gen_receipt_number(),
            patient=patient, service=svc,
            quantity=qty, unit_price=svc.price,
            payment_method=d.get('payment_method', 'cash'),
            notes=d.get('notes', ''),
            performed_by=request.user,
        )
        messages.success(request, f'Instant service recorded. Receipt: {inst.receipt_number}')
        return redirect('instant_service')
    return render(request, 'services/instant_service.html', {
        'patients': patients, 'services': services, 'recent': recent,
        'payment_methods': [('cash','Cash'),('card','Card'),('insurance','Insurance'),
                            ('mobile_money','Mobile Money')],
    })
