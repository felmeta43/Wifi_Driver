from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
import json

from .models import Invoice, InvoiceItem, Payment
from patients.models import Patient
from appointments.models import Appointment


def generate_invoice_number():
    last = Invoice.objects.order_by('-id').first()
    num = (last.id + 1) if last else 1
    return f"INV{num:06d}"


@login_required
def invoice_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    invoices = Invoice.objects.select_related('patient').order_by('-created_at')
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )
    if status:
        invoices = invoices.filter(status=status)
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = Invoice.objects.filter(status='pending').aggregate(
        total=Sum('total_amount'))['total'] or 0
    return render(request, 'billing/invoice_list.html', {
        'invoices': invoices, 'query': query, 'status': status,
        'status_choices': Invoice.STATUS_CHOICES,
        'total_revenue': total_revenue, 'pending_amount': pending_amount,
    })


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    payments = invoice.payments.all().order_by('-payment_date')
    return render(request, 'billing/invoice_detail.html', {
        'invoice': invoice, 'items': items, 'payments': payments
    })


@login_required
def invoice_create(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    appointments = Appointment.objects.filter(status='completed').order_by('-appointment_date')[:50]
    if request.method == 'POST':
        data = request.POST
        patient = get_object_or_404(Patient, pk=data.get('patient'))
        apt_id = data.get('appointment')
        apt = Appointment.objects.filter(pk=apt_id).first() if apt_id else None

        from core.models import HospitalSettings
        hospital = HospitalSettings.get_settings()
        tax_pct = float(hospital.tax_percentage)

        descriptions = data.getlist('description')
        categories = data.getlist('category')
        quantities = data.getlist('quantity')
        unit_prices = data.getlist('unit_price')

        subtotal = 0
        discount = float(data.get('discount_amount', 0))
        items_data = []
        for i, desc in enumerate(descriptions):
            if desc:
                qty = float(quantities[i]) if i < len(quantities) else 1
                price = float(unit_prices[i]) if i < len(unit_prices) else 0
                total = qty * price
                subtotal += total
                items_data.append({
                    'description': desc,
                    'category': categories[i] if i < len(categories) else 'other',
                    'quantity': qty, 'unit_price': price, 'total_price': total
                })

        tax_amount = (subtotal - discount) * tax_pct / 100
        total = subtotal - discount + tax_amount

        invoice = Invoice.objects.create(
            invoice_number=generate_invoice_number(),
            patient=patient, appointment=apt,
            created_by=request.user,
            subtotal=subtotal, discount_amount=discount,
            tax_amount=tax_amount, total_amount=total,
            notes=data.get('notes', ''),
            due_date=data.get('due_date') or None,
        )
        for item in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item)
        messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
        return redirect('invoice_detail', pk=invoice.pk)
    return render(request, 'billing/invoice_form.html', {
        'patients': patients, 'appointments': appointments,
        'item_categories': InvoiceItem.CATEGORY_CHOICES,
    })


@login_required
def add_payment(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        method = request.POST.get('method', 'cash')
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')
        Payment.objects.create(
            invoice=invoice, amount=amount, method=method,
            reference=reference, notes=notes, received_by=request.user
        )
        invoice.paid_amount += amount
        if invoice.paid_amount >= invoice.total_amount:
            invoice.status = 'paid'
        elif invoice.paid_amount > 0:
            invoice.status = 'partial'
        invoice.save()
        messages.success(request, f'Payment of {amount} recorded successfully!')
    return redirect('invoice_detail', pk=invoice.pk)


@login_required
def billing_reports(request):
    from datetime import date, timedelta
    from django.db.models.functions import TruncMonth
    today = date.today()
    monthly = Payment.objects.filter(
        payment_date__year=today.year
    ).annotate(month=TruncMonth('payment_date')).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    total_revenue = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_pending = Invoice.objects.filter(status='pending').aggregate(
        total=Sum('total_amount'))['total'] or 0
    payment_methods = Payment.objects.values('method').annotate(total=Sum('amount')).order_by('-total')
    return render(request, 'billing/reports.html', {
        'monthly': monthly, 'total_revenue': total_revenue,
        'total_pending': total_pending, 'payment_methods': payment_methods,
    })
