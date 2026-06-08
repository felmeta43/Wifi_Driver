from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import LabTest, LabOrder, LabResult
from patients.models import Patient
from doctors.models import Doctor


def generate_order_id():
    last = LabOrder.objects.order_by('-id').first()
    num = (last.id + 1) if last else 1
    return f"LAB{num:06d}"


TOP_LAB_SECTIONS = [
    'HEMATOLOGY', 'SEROLOGY', 'CLINICAL CHEMISTRY', 'HORMONE ANALYSIS',
    'MICRO-BIOLOGY', 'PARA-MICRO', 'BODY FLUID ANALYSIS',
]


@login_required
def lab_test_list(request):
    if request.method == 'POST':
        LabTest.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            price=float(request.POST.get('price', 0)),
            normal_range=request.POST.get('normal_range', ''),
            unit=request.POST.get('unit', ''),
            turnaround_time=request.POST.get('turnaround_time', ''),
        )
        messages.success(request, 'Lab test added!')
        return redirect('lab_test_list')

    from collections import defaultdict, OrderedDict
    all_tests = list(LabTest.objects.filter(is_active=True).order_by('name'))

    # Group tests by their stated panel (extracted from description)
    tests_by_panel = defaultdict(list)
    for t in all_tests:
        if t.description.startswith('Panel: '):
            panel = t.description[7:]
        else:
            panel = '__root__'
        tests_by_panel[panel].append(t)

    # Build hierarchical tree: section → [{test, sub_tests}, …]
    tree = OrderedDict()
    for section in TOP_LAB_SECTIONS:
        if section not in tests_by_panel:
            continue
        entries = []
        for panel_test in sorted(tests_by_panel[section], key=lambda x: x.name):
            entries.append({
                'test': panel_test,
                'sub_tests': sorted(tests_by_panel.get(panel_test.name, []), key=lambda x: x.name),
            })
        if entries:
            tree[section] = entries

    # Collect any panels not under a known top-level section.
    # Skip a panel if a panel_test with that name was already placed in the tree.
    already_placed = {e['test'].name for sec_entries in tree.values() for e in sec_entries}
    known = set(TOP_LAB_SECTIONS)
    for panel_name, pts in sorted(tests_by_panel.items()):
        if panel_name in known or panel_name == '__root__':
            continue
        if panel_name in already_placed:
            continue
        tree[panel_name] = [
            {'test': t, 'sub_tests': tests_by_panel.get(t.name, [])}
            for t in sorted(pts, key=lambda x: x.name)
        ]

    # Standalone tests (no panel grouping)
    root_tests = tests_by_panel.get('__root__', [])

    # Convert to list of (section_name, entries, count) for simple template iteration
    tree_list = [
        (sec, entries, sum(1 + len(e['sub_tests']) for e in entries))
        for sec, entries in tree.items()
    ]

    return render(request, 'laboratory/lab_test_list.html', {
        'tree': tree_list,
        'root_tests': root_tests,
        'total_tests': len(all_tests),
    })


@login_required
def lab_order_list(request):
    from django.core.paginator import Paginator
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    orders = LabOrder.objects.select_related('patient', 'doctor__user').order_by('-ordered_at')
    if query:
        orders = orders.filter(
            Q(order_id__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )
    if status:
        orders = orders.filter(status=status)
    paginator = Paginator(orders, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'laboratory/lab_order_list.html', {
        'orders': page_obj, 'page_obj': page_obj,
        'query': query, 'status': status,
        'status_choices': LabOrder.STATUS_CHOICES,
    })


@login_required
def lab_order_detail(request, pk):
    order = get_object_or_404(LabOrder, pk=pk)
    results = order.results.select_related('test').all()
    tests = LabTest.objects.filter(is_active=True)
    return render(request, 'laboratory/lab_order_detail.html', {
        'order': order, 'results': results, 'tests': tests
    })


@login_required
def lab_order_create(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    tests = LabTest.objects.filter(is_active=True)
    pre_patient = request.GET.get('patient')
    pre_doctor = request.GET.get('doctor')
    if request.method == 'POST':
        data = request.POST
        patient = get_object_or_404(Patient, pk=data.get('patient'))
        doctor = get_object_or_404(Doctor, pk=data.get('doctor'))
        from appointments.models import Appointment
        apt_id = data.get('appointment')
        apt = Appointment.objects.filter(pk=apt_id).first() if apt_id else None
        order = LabOrder.objects.create(
            order_id=generate_order_id(),
            patient=patient, doctor=doctor, appointment=apt,
            notes=data.get('notes', ''),
        )
        test_ids = data.getlist('tests')
        for test_id in test_ids:
            test = LabTest.objects.filter(pk=test_id).first()
            if test:
                LabResult.objects.create(order=order, test=test, result_value='Pending')
        messages.success(request, f'Lab order {order.order_id} created!')
        return redirect('lab_order_detail', pk=order.pk)
    return render(request, 'laboratory/lab_order_form.html', {
        'patients': patients, 'doctors': doctors, 'tests': tests,
        'pre_patient': pre_patient, 'pre_doctor': pre_doctor,
    })


@login_required
def add_lab_result(request, order_pk):
    order = get_object_or_404(LabOrder, pk=order_pk)
    if request.method == 'POST':
        test_id = request.POST.get('test')
        test = get_object_or_404(LabTest, pk=test_id)
        result_value = request.POST.get('result_value', '')
        unit = request.POST.get('unit', test.unit)
        normal_range = request.POST.get('normal_range', test.normal_range)
        is_abnormal = 'is_abnormal' in request.POST
        notes = request.POST.get('notes', '')
        existing = LabResult.objects.filter(order=order, test=test).first()
        if existing:
            existing.result_value = result_value
            existing.unit = unit
            existing.normal_range = normal_range
            existing.is_abnormal = is_abnormal
            existing.notes = notes
            existing.save()
        else:
            LabResult.objects.create(
                order=order, test=test, result_value=result_value,
                unit=unit, normal_range=normal_range,
                is_abnormal=is_abnormal, notes=notes,
            )
        all_done = all(r.result_value != 'Pending' for r in order.results.all())
        if all_done:
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.technician = request.user
            order.save()
        messages.success(request, 'Lab result recorded!')
    return redirect('lab_order_detail', pk=order_pk)


@login_required
def update_order_status(request, pk):
    order = get_object_or_404(LabOrder, pk=pk)
    if request.method == 'POST':
        order.status = request.POST.get('status', order.status)
        if order.status == 'completed':
            order.completed_at = timezone.now()
        order.save()
        messages.success(request, 'Order status updated!')
    return redirect('lab_order_detail', pk=pk)
