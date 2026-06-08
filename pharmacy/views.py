from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import Medicine, Prescription, PrescriptionItem, StockTransaction
from patients.models import Patient
from doctors.models import Doctor
from appointments.models import Appointment


def generate_prescription_id():
    last = Prescription.objects.order_by('-id').first()
    num = (last.id + 1) if last else 1
    return f"RX{num:06d}"


@login_required
def medicine_list(request):
    from django.core.paginator import Paginator
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    medicines = Medicine.objects.filter(is_active=True).order_by('name')
    if query:
        medicines = medicines.filter(Q(name__icontains=query) | Q(generic_name__icontains=query))
    if category:
        medicines = medicines.filter(category=category)
    low_stock = Medicine.objects.filter(is_active=True, stock_quantity__lte=10)
    paginator = Paginator(medicines, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'pharmacy/medicine_list.html', {
        'medicines': page_obj, 'page_obj': page_obj,
        'query': query, 'category': category,
        'categories': Medicine.CATEGORY_CHOICES,
        'low_stock_count': low_stock.count(),
    })


@login_required
def medicine_create(request):
    if request.method == 'POST':
        data = request.POST
        Medicine.objects.create(
            name=data.get('name'), generic_name=data.get('generic_name', ''),
            category=data.get('category', 'tablet'),
            manufacturer=data.get('manufacturer', ''),
            description=data.get('description', ''),
            unit=data.get('unit', 'pieces'),
            unit_price=float(data.get('unit_price', 0)),
            stock_quantity=int(data.get('stock_quantity', 0)),
            minimum_stock=int(data.get('minimum_stock', 10)),
            expiry_date=data.get('expiry_date') or None,
            batch_number=data.get('batch_number', ''),
        )
        messages.success(request, 'Medicine added successfully!')
        return redirect('medicine_list')
    return render(request, 'pharmacy/medicine_form.html', {
        'action': 'Add', 'categories': Medicine.CATEGORY_CHOICES
    })


@login_required
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        data = request.POST
        medicine.name = data.get('name', medicine.name)
        medicine.generic_name = data.get('generic_name', medicine.generic_name)
        medicine.category = data.get('category', medicine.category)
        medicine.manufacturer = data.get('manufacturer', medicine.manufacturer)
        medicine.unit = data.get('unit', medicine.unit)
        medicine.unit_price = float(data.get('unit_price', medicine.unit_price))
        medicine.minimum_stock = int(data.get('minimum_stock', medicine.minimum_stock))
        medicine.expiry_date = data.get('expiry_date') or medicine.expiry_date
        medicine.save()
        messages.success(request, 'Medicine updated!')
        return redirect('medicine_list')
    return render(request, 'pharmacy/medicine_form.html', {
        'action': 'Edit', 'medicine': medicine, 'categories': Medicine.CATEGORY_CHOICES
    })


@login_required
def stock_in(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == 'POST':
        qty = int(request.POST.get('quantity', 0))
        price = float(request.POST.get('unit_price', medicine.unit_price))
        ref = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')
        StockTransaction.objects.create(
            medicine=medicine, transaction_type='in', quantity=qty,
            unit_price=price, reference=ref, notes=notes, performed_by=request.user
        )
        medicine.stock_quantity += qty
        medicine.unit_price = price
        medicine.save()
        messages.success(request, f'Added {qty} units to {medicine.name}')
        return redirect('medicine_list')
    return render(request, 'pharmacy/stock_in_form.html', {'medicine': medicine})


@login_required
def prescription_list(request):
    from django.core.paginator import Paginator
    query = request.GET.get('q', '')
    prescriptions = Prescription.objects.select_related('patient', 'doctor__user').order_by('-created_at')
    if query:
        from django.db.models import Q
        prescriptions = prescriptions.filter(
            Q(prescription_id__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )
    paginator = Paginator(prescriptions, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'pharmacy/prescription_list.html', {
        'prescriptions': page_obj, 'page_obj': page_obj, 'query': query,
    })


@login_required
def prescription_detail(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    items = prescription.items.select_related('medicine').all()
    return render(request, 'pharmacy/prescription_detail.html', {
        'prescription': prescription, 'items': items
    })


@login_required
def prescription_create(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    medicines = Medicine.objects.filter(is_active=True).order_by('name')
    pre_patient = request.GET.get('patient')
    pre_doctor = request.GET.get('doctor')
    if request.method == 'POST':
        data = request.POST
        patient = get_object_or_404(Patient, pk=data.get('patient'))
        doctor = get_object_or_404(Doctor, pk=data.get('doctor'))
        apt_id = data.get('appointment')
        apt = Appointment.objects.filter(pk=apt_id).first() if apt_id else None
        prescription = Prescription.objects.create(
            prescription_id=generate_prescription_id(),
            patient=patient, doctor=doctor, appointment=apt,
            notes=data.get('notes', ''),
        )
        medicine_ids = data.getlist('medicine')
        dosages = data.getlist('dosage')
        frequencies = data.getlist('frequency')
        durations = data.getlist('duration')
        quantities = data.getlist('quantity')
        instructions_list = data.getlist('instructions')
        for i, med_id in enumerate(medicine_ids):
            if med_id:
                med = Medicine.objects.filter(pk=med_id).first()
                if med:
                    PrescriptionItem.objects.create(
                        prescription=prescription, medicine=med,
                        dosage=dosages[i] if i < len(dosages) else '',
                        frequency=frequencies[i] if i < len(frequencies) else '',
                        duration=durations[i] if i < len(durations) else '',
                        quantity=int(quantities[i]) if i < len(quantities) else 1,
                        instructions=instructions_list[i] if i < len(instructions_list) else '',
                    )
        messages.success(request, f'Prescription {prescription.prescription_id} created!')
        return redirect('prescription_detail', pk=prescription.pk)
    return render(request, 'pharmacy/prescription_form.html', {
        'patients': patients, 'doctors': doctors, 'medicines': medicines,
        'pre_patient': pre_patient, 'pre_doctor': pre_doctor,
    })


@login_required
def dispense_prescription(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.method == 'POST':
        for item in prescription.items.all():
            if item.medicine.stock_quantity >= item.quantity:
                item.medicine.stock_quantity -= item.quantity
                item.medicine.save()
                StockTransaction.objects.create(
                    medicine=item.medicine, transaction_type='out',
                    quantity=item.quantity, reference=prescription.prescription_id,
                    performed_by=request.user
                )
            else:
                messages.warning(request, f'Insufficient stock for {item.medicine.name}')
                return redirect('prescription_detail', pk=prescription.pk)
        prescription.status = 'dispensed'
        prescription.dispensed_by = request.user
        prescription.dispensed_at = timezone.now()
        prescription.save()
        messages.success(request, 'Prescription dispensed successfully!')
    return redirect('prescription_detail', pk=prescription.pk)
