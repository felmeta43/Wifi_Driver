from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse
import json

from .models import Invoice, InvoiceItem, Payment, DailyCollection
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


def _can_receive_payment(user):
    return user.role in ('admin', 'cashier') or user.is_superuser


@login_required
def add_payment(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)
    if request.method == 'POST':
        if not _can_receive_payment(request.user):
            messages.error(request, 'Only cashiers can record payments. Please direct the patient to the cashier desk.')
            return redirect('invoice_detail', pk=invoice_pk)
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


# ── Daily Collection ──────────────────────────────────────────────────────────

def _build_collection_summary(cashier, date):
    """Calculate payment totals for a cashier on a given date from Payment records."""
    from services.models import InstantService
    from django.db.models import Sum
    from decimal import Decimal

    ZERO = Decimal('0')
    payments = Payment.objects.filter(
        received_by=cashier,
        payment_date__date=date,
    )
    totals = {
        'cash': payments.filter(method='cash').aggregate(t=Sum('amount'))['t'] or ZERO,
        'card': payments.filter(method='card').aggregate(t=Sum('amount'))['t'] or ZERO,
        'insurance': payments.filter(method='insurance').aggregate(t=Sum('amount'))['t'] or ZERO,
        'mobile_money': payments.filter(method='mobile_money').aggregate(t=Sum('amount'))['t'] or ZERO,
        'bank_transfer': payments.filter(method='bank_transfer').aggregate(t=Sum('amount'))['t'] or ZERO,
        'check': payments.filter(method='check').aggregate(t=Sum('amount'))['t'] or ZERO,
    }
    instant = InstantService.objects.filter(
        performed_by=cashier,
        created_at__date=date,
    ).aggregate(t=Sum('total_price'))['t'] or ZERO
    total = sum(totals.values()) + instant
    return totals, instant, total, payments.count()


@login_required
def daily_collection_submit(request):
    from datetime import date as date_type
    if request.user.role not in ('cashier', 'admin') and not request.user.is_superuser:
        messages.error(request, 'Only cashiers can submit daily collections.')
        return redirect('dashboard')

    today = date_type.today()
    collection, _ = DailyCollection.objects.get_or_create(
        cashier=request.user, collection_date=today,
    )

    # Always refresh calculated totals if still draft
    if collection.status == 'draft':
        totals, instant, total, count = _build_collection_summary(request.user, today)
        collection.cash_total = totals['cash']
        collection.card_total = totals['card']
        collection.insurance_total = totals['insurance']
        collection.mobile_money_total = totals['mobile_money']
        collection.bank_transfer_total = totals['bank_transfer']
        collection.check_total = totals['check']
        collection.instant_service_total = instant
        collection.total_collected = total
        collection.transaction_count = count
        collection.save(update_fields=[
            'cash_total', 'card_total', 'insurance_total', 'mobile_money_total',
            'bank_transfer_total', 'check_total', 'instant_service_total',
            'total_collected', 'transaction_count',
        ])

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'submit' and collection.status == 'draft':
            from django.utils import timezone
            collection.notes = request.POST.get('notes', '')
            collection.status = 'submitted'
            collection.submitted_at = timezone.now()
            collection.save()
            messages.success(request, f'Daily collection for {today} submitted for approval.')
            return redirect('daily_collection_submit')

    # Get individual payments for the day to show detail
    today_payments = Payment.objects.filter(
        received_by=request.user, payment_date__date=today
    ).select_related('invoice__patient').order_by('-payment_date')

    # History of past collections
    history = DailyCollection.objects.filter(cashier=request.user).exclude(
        collection_date=today
    ).order_by('-collection_date')[:10]

    return render(request, 'billing/daily_collection.html', {
        'collection': collection,
        'today_payments': today_payments,
        'history': history,
        'today': today,
    })


@login_required
def collection_list(request):
    if request.user.role not in ('finance_head', 'admin') and not request.user.is_superuser:
        messages.error(request, 'Access restricted to Finance Head.')
        return redirect('dashboard')

    status = request.GET.get('status', 'submitted')
    qs = DailyCollection.objects.select_related('cashier', 'reviewed_by').order_by(
        '-collection_date', 'cashier__first_name'
    )
    if status:
        qs = qs.filter(status=status)

    pending_count = DailyCollection.objects.filter(status='submitted').count()
    return render(request, 'billing/collection_list.html', {
        'collections': qs,
        'status': status,
        'status_choices': DailyCollection.STATUS_CHOICES,
        'pending_count': pending_count,
    })


@login_required
def collection_review(request, pk):
    if request.user.role not in ('finance_head', 'admin') and not request.user.is_superuser:
        messages.error(request, 'Access restricted to Finance Head.')
        return redirect('dashboard')

    collection = get_object_or_404(DailyCollection, pk=pk)

    if request.method == 'POST':
        from django.utils import timezone
        action = request.POST.get('action')
        if action == 'approve':
            collection.status = 'approved'
            collection.rejection_reason = ''
            collection.reviewed_by = request.user
            collection.reviewed_at = timezone.now()
            collection.save()
            messages.success(request, f'Collection approved for {collection.cashier.get_full_name()} on {collection.collection_date}.')
        elif action == 'reject':
            collection.status = 'rejected'
            collection.rejection_reason = request.POST.get('rejection_reason', '')
            collection.reviewed_by = request.user
            collection.reviewed_at = timezone.now()
            collection.save()
            messages.warning(request, f'Collection rejected. Cashier will need to resubmit.')
            # Reset to draft so cashier can resubmit
            collection.status = 'draft'
            collection.submitted_at = None
            collection.save()
        return redirect('collection_list')

    # Get individual payments for that day and cashier
    day_payments = Payment.objects.filter(
        received_by=collection.cashier,
        payment_date__date=collection.collection_date,
    ).select_related('invoice__patient').order_by('-payment_date')

    from services.models import InstantService
    day_instant = InstantService.objects.filter(
        performed_by=collection.cashier,
        created_at__date=collection.collection_date,
    ).select_related('patient', 'service').order_by('-created_at')

    return render(request, 'billing/collection_detail.html', {
        'collection': collection,
        'day_payments': day_payments,
        'day_instant': day_instant,
    })
