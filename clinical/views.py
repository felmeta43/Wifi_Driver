from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from .models import (
    OPDVisit, IPDAdmission, DischargeRecord,
    ClinicalNote, OperationNote,
    ConsultationRequest, PatientHandover,
    MedicalFile, CBCResult, ChemistryResult,
    RadiologyOrder, RadiologyResult, RadiologyImage,
)
from patients.models import Patient
from doctors.models import Doctor
from accounts.models import User


def _next(prefix, model):
    last = model.objects.order_by('-id').first()
    return f"{prefix}{(last.id + 1 if last else 1):06d}"


# ─── OPD ─────────────────────────────────────────────────────────────────────

@login_required
def opd_list(request):
    from datetime import date
    today = date.today()
    date_filter = request.GET.get('date', today.isoformat())
    query = request.GET.get('q', '')
    visits = OPDVisit.objects.select_related('patient', 'doctor__user').filter(
        visit_date=date_filter)
    if query:
        visits = visits.filter(
            Q(visit_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )
    return render(request, 'clinical/opd_list.html', {
        'visits': visits, 'date_filter': date_filter, 'query': query,
        'today': today.isoformat(),
    })


@login_required
def opd_create(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    if request.method == 'POST':
        d = request.POST
        patient = get_object_or_404(Patient, pk=d['patient'])
        doc_id = d.get('doctor')
        doctor = Doctor.objects.filter(pk=doc_id).first() if doc_id else None
        vitals = {k: d.get(k, '') for k in
                  ['blood_pressure', 'temperature', 'pulse', 'weight', 'height',
                   'oxygen_saturation', 'respiratory_rate']}
        visit = OPDVisit.objects.create(
            visit_number=_next('OPD', OPDVisit),
            patient=patient, doctor=doctor,
            triage_level=d.get('triage_level', '5_non_urgent'),
            chief_complaint=d['chief_complaint'],
            vital_signs={k: v for k, v in vitals.items() if v},
            notes=d.get('notes', ''),
            registered_by=request.user,
        )
        messages.success(request, f'OPD visit {visit.visit_number} registered!')
        return redirect('opd_detail', pk=visit.pk)
    return render(request, 'clinical/opd_form.html', {
        'patients': patients, 'doctors': doctors,
        'triage_choices': OPDVisit.TRIAGE_CHOICES,
    })


@login_required
def opd_detail(request, pk):
    visit = get_object_or_404(OPDVisit, pk=pk)
    notes = visit.clinical_notes.order_by('-created_at')
    return render(request, 'clinical/opd_detail.html', {'visit': visit, 'notes': notes})


@login_required
def opd_status_update(request, pk):
    visit = get_object_or_404(OPDVisit, pk=pk)
    if request.method == 'POST':
        visit.status = request.POST.get('status', visit.status)
        visit.referred_to = request.POST.get('referred_to', visit.referred_to)
        visit.save()
        messages.success(request, 'OPD status updated.')
    return redirect('opd_detail', pk=pk)


# ─── IPD ─────────────────────────────────────────────────────────────────────

@login_required
def ipd_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status', 'admitted')
    admissions = IPDAdmission.objects.select_related('patient', 'admitting_doctor__user',
                                                     'department').order_by('-admission_date')
    if status:
        admissions = admissions.filter(status=status)
    if query:
        admissions = admissions.filter(
            Q(admission_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query) |
            Q(room_number__icontains=query)
        )
    return render(request, 'clinical/ipd_list.html', {
        'admissions': admissions, 'query': query, 'status': status,
        'status_choices': IPDAdmission.STATUS_CHOICES,
    })


@login_required
def ipd_admit(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    nurses = User.objects.filter(role='nurse', is_active=True)
    from core.models import Department
    departments = Department.objects.filter(is_active=True)
    if request.method == 'POST':
        d = request.POST
        patient = get_object_or_404(Patient, pk=d['patient'])
        doctor = get_object_or_404(Doctor, pk=d['admitting_doctor'])
        dept = Department.objects.filter(pk=d.get('department')).first()
        nurse_id = d.get('attending_nurse')
        nurse = User.objects.filter(pk=nurse_id).first() if nurse_id else None
        adm = IPDAdmission.objects.create(
            admission_number=_next('IPD', IPDAdmission),
            patient=patient, admitting_doctor=doctor,
            department=dept,
            ward=d.get('ward', ''),
            room_number=d['room_number'],
            bed_number=d.get('bed_number', ''),
            room_type=d.get('room_type', 'general'),
            admission_diagnosis=d['admission_diagnosis'],
            expected_discharge=d.get('expected_discharge') or None,
            attending_nurse=nurse,
            notes=d.get('notes', ''),
        )
        messages.success(request, f'Patient admitted: {adm.admission_number}')
        return redirect('ipd_detail', pk=adm.pk)
    return render(request, 'clinical/ipd_admit_form.html', {
        'patients': patients, 'doctors': doctors, 'nurses': nurses,
        'departments': departments, 'room_types': IPDAdmission.ROOM_TYPE_CHOICES,
    })


@login_required
def ipd_detail(request, pk):
    adm = get_object_or_404(IPDAdmission, pk=pk)
    clinical_notes = adm.clinical_notes.order_by('-created_at')[:10]
    handovers = adm.handovers.order_by('-created_at')[:5]
    consultations = adm.consultation_requests.order_by('-requested_at')[:5]
    op_notes = adm.operation_notes.order_by('-operation_date')[:5]
    radiology = adm.radiology_orders.order_by('-ordered_at')[:5]
    service_orders = adm.service_orders.order_by('-created_at')[:5]
    files = adm.medical_files.order_by('-created_at')[:10]
    return render(request, 'clinical/ipd_detail.html', {
        'adm': adm, 'clinical_notes': clinical_notes, 'handovers': handovers,
        'consultations': consultations, 'op_notes': op_notes,
        'radiology': radiology, 'service_orders': service_orders, 'files': files,
    })


@login_required
def ipd_discharge(request, pk):
    adm = get_object_or_404(IPDAdmission, pk=pk)
    doctors = Doctor.objects.filter(status='active').select_related('user')
    if request.method == 'POST':
        d = request.POST
        follow_doctor_id = d.get('follow_up_doctor')
        follow_doc = Doctor.objects.filter(pk=follow_doctor_id).first() if follow_doctor_id else None
        DischargeRecord.objects.create(
            admission=adm,
            discharge_diagnosis=d['discharge_diagnosis'],
            treatment_summary=d['treatment_summary'],
            discharge_instructions=d.get('discharge_instructions', ''),
            follow_up_date=d.get('follow_up_date') or None,
            follow_up_doctor=follow_doc,
            diet_instructions=d.get('diet_instructions', ''),
            activity_restrictions=d.get('activity_restrictions', ''),
            discharge_medications=d.get('discharge_medications', ''),
            discharge_condition=d.get('discharge_condition', ''),
            discharged_by=request.user,
        )
        adm.status = 'discharged'
        adm.discharge_date = timezone.now()
        adm.final_diagnosis = d.get('discharge_diagnosis', '')
        adm.save()
        messages.success(request, f'Patient {adm.patient.get_full_name()} discharged.')
        return redirect('ipd_detail', pk=pk)
    return render(request, 'clinical/ipd_discharge_form.html', {'adm': adm, 'doctors': doctors})


# ─── Clinical Notes ───────────────────────────────────────────────────────────

@login_required
def clinical_note_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    adm_id = request.GET.get('admission')
    opd_id = request.GET.get('opd')
    admissions = IPDAdmission.objects.filter(patient=patient, status='admitted')
    if request.method == 'POST':
        d = request.POST
        vitals = {k: d.get(k, '') for k in
                  ['blood_pressure', 'temperature', 'pulse', 'weight', 'oxygen_saturation']}
        adm = IPDAdmission.objects.filter(pk=d.get('admission')).first()
        opd = OPDVisit.objects.filter(pk=d.get('opd_visit')).first()
        ClinicalNote.objects.create(
            patient=patient, admission=adm, opd_visit=opd,
            note_type=d.get('note_type', 'progress'),
            title=d.get('title', ''),
            subjective=d.get('subjective', ''),
            objective=d.get('objective', ''),
            assessment=d.get('assessment', ''),
            plan=d.get('plan', ''),
            content=d.get('content', ''),
            vital_signs={k: v for k, v in vitals.items() if v},
            written_by=request.user,
        )
        messages.success(request, 'Clinical note saved!')
        if adm:
            return redirect('ipd_detail', pk=adm.pk)
        return redirect('patient_detail', pk=patient_pk)
    return render(request, 'clinical/clinical_note_form.html', {
        'patient': patient, 'admissions': admissions,
        'note_types': ClinicalNote.NOTE_TYPES,
        'selected_adm': adm_id, 'selected_opd': opd_id,
    })


# ─── Operation Notes ─────────────────────────────────────────────────────────

@login_required
def operation_note_list(request):
    notes = OperationNote.objects.select_related('patient', 'surgeon__user').order_by('-operation_date')
    return render(request, 'clinical/operation_note_list.html', {'notes': notes})


@login_required
def operation_note_create(request, patient_pk=None):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    patient = Patient.objects.filter(pk=patient_pk).first() if patient_pk else None
    admissions = IPDAdmission.objects.filter(patient=patient, status='admitted') if patient else []
    if request.method == 'POST':
        d = request.POST
        pat = get_object_or_404(Patient, pk=d['patient'])
        surgeon = get_object_or_404(Doctor, pk=d['surgeon'])
        adm = IPDAdmission.objects.filter(pk=d.get('admission')).first()
        OperationNote.objects.create(
            operation_number=_next('OPN', OperationNote),
            patient=pat, surgeon=surgeon, admission=adm,
            procedure_name=d['procedure_name'],
            operation_date=d['operation_date'],
            status=d.get('status', 'completed'),
            assistant_surgeon=d.get('assistant_surgeon', ''),
            anesthetist=d.get('anesthetist', ''),
            anesthesia_type=d.get('anesthesia_type', ''),
            scrub_nurse=d.get('scrub_nurse', ''),
            circulating_nurse=d.get('circulating_nurse', ''),
            pre_op_diagnosis=d['pre_op_diagnosis'],
            post_op_diagnosis=d.get('post_op_diagnosis', ''),
            indication=d.get('indication', ''),
            procedure_details=d.get('procedure_details', ''),
            findings=d.get('findings', ''),
            complications=d.get('complications', ''),
            blood_loss=d.get('blood_loss', ''),
            specimens_sent=d.get('specimens_sent', ''),
            drains=d.get('drains', ''),
            closure=d.get('closure', ''),
            post_op_instructions=d.get('post_op_instructions', ''),
            duration_minutes=int(d['duration_minutes']) if d.get('duration_minutes') else None,
            created_by=request.user,
        )
        messages.success(request, 'Operation note saved!')
        return redirect('operation_note_list')
    return render(request, 'clinical/operation_note_form.html', {
        'patients': patients, 'doctors': doctors,
        'patient': patient, 'admissions': admissions,
        'status_choices': OperationNote.STATUS_CHOICES,
    })


@login_required
def operation_note_detail(request, pk):
    note = get_object_or_404(OperationNote, pk=pk)
    return render(request, 'clinical/operation_note_detail.html', {'note': note})


# ─── Consultation ─────────────────────────────────────────────────────────────

@login_required
def consultation_list(request):
    consults = ConsultationRequest.objects.select_related(
        'patient', 'requesting_doctor__user', 'consulting_doctor__user'
    ).order_by('-requested_at')
    status = request.GET.get('status', '')
    if status:
        consults = consults.filter(status=status)
    return render(request, 'clinical/consultation_list.html', {
        'consults': consults, 'status': status,
        'status_choices': ConsultationRequest.STATUS_CHOICES,
    })


@login_required
def consultation_create(request, patient_pk=None):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    patient = Patient.objects.filter(pk=patient_pk).first() if patient_pk else None
    if request.method == 'POST':
        d = request.POST
        pat = get_object_or_404(Patient, pk=d['patient'])
        req_doc = Doctor.objects.filter(pk=d.get('requesting_doctor')).first()
        con_doc = get_object_or_404(Doctor, pk=d['consulting_doctor'])
        adm = IPDAdmission.objects.filter(pk=d.get('admission')).first()
        ConsultationRequest.objects.create(
            request_number=_next('CON', ConsultationRequest),
            patient=pat, requesting_doctor=req_doc, consulting_doctor=con_doc,
            admission=adm, priority=d.get('priority', 'routine'),
            reason=d['reason'], clinical_summary=d.get('clinical_summary', ''),
        )
        messages.success(request, 'Consultation request sent!')
        return redirect('consultation_list')
    admissions = IPDAdmission.objects.filter(patient=patient, status='admitted') if patient else []
    return render(request, 'clinical/consultation_form.html', {
        'patients': patients, 'doctors': doctors, 'patient': patient,
        'admissions': admissions, 'priority_choices': ConsultationRequest.PRIORITY_CHOICES,
    })


@login_required
def consultation_respond(request, pk):
    consult = get_object_or_404(ConsultationRequest, pk=pk)
    if request.method == 'POST':
        consult.response = request.POST.get('response', '')
        consult.recommendations = request.POST.get('recommendations', '')
        consult.status = request.POST.get('status', 'completed')
        consult.responded_at = timezone.now()
        consult.save()
        messages.success(request, 'Consultation response saved!')
    return redirect('consultation_list')


# ─── Patient Handover ─────────────────────────────────────────────────────────

@login_required
def handover_list(request):
    from datetime import date
    date_filter = request.GET.get('date', date.today().isoformat())
    handovers = PatientHandover.objects.filter(handover_date=date_filter).select_related(
        'patient', 'handover_from', 'handover_to', 'admission'
    )
    return render(request, 'clinical/handover_list.html', {
        'handovers': handovers, 'date_filter': date_filter,
    })


@login_required
def handover_create(request, patient_pk=None):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    nurses = User.objects.filter(role__in=['nurse', 'admin'], is_active=True)
    patient = Patient.objects.filter(pk=patient_pk).first() if patient_pk else None
    admissions = IPDAdmission.objects.filter(patient=patient, status='admitted') if patient else []
    if request.method == 'POST':
        d = request.POST
        pat = get_object_or_404(Patient, pk=d['patient'])
        to_nurse = get_object_or_404(User, pk=d['handover_to'])
        adm = IPDAdmission.objects.filter(pk=d.get('admission')).first()
        vitals = {k: d.get(k, '') for k in
                  ['blood_pressure', 'temperature', 'pulse', 'oxygen_saturation']}
        PatientHandover.objects.create(
            patient=pat, admission=adm,
            handover_from=request.user, handover_to=to_nurse,
            shift=d['shift'], current_condition=d['current_condition'],
            vital_signs={k: v for k, v in vitals.items() if v},
            active_issues=d.get('active_issues', ''),
            pending_tasks=d.get('pending_tasks', ''),
            medications_due=d.get('medications_due', ''),
            special_instructions=d.get('special_instructions', ''),
        )
        messages.success(request, 'Handover record created!')
        return redirect('handover_list')
    return render(request, 'clinical/handover_form.html', {
        'patients': patients, 'nurses': nurses, 'patient': patient,
        'admissions': admissions, 'shift_choices': PatientHandover.SHIFT_CHOICES,
    })


# ─── Medical Files ─────────────────────────────────────────────────────────────

@login_required
def medical_file_upload(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    admissions = IPDAdmission.objects.filter(patient=patient)
    if request.method == 'POST':
        adm = IPDAdmission.objects.filter(pk=request.POST.get('admission')).first()
        MedicalFile.objects.create(
            patient=patient, admission=adm,
            file_type=request.POST.get('file_type', 'document'),
            title=request.POST['title'],
            description=request.POST.get('description', ''),
            file=request.FILES['file'],
            uploaded_by=request.user,
        )
        messages.success(request, 'File uploaded successfully!')
        return redirect('patient_detail', pk=patient_pk)
    return render(request, 'clinical/medical_file_form.html', {
        'patient': patient, 'admissions': admissions,
        'file_types': MedicalFile.FILE_TYPES,
    })


# ─── CBC Machine Results ──────────────────────────────────────────────────────

@login_required
def cbc_result_create(request, order_pk):
    from laboratory.models import LabOrder
    order = get_object_or_404(LabOrder, pk=order_pk)
    if request.method == 'POST':
        d = request.POST
        def dec(key):
            v = d.get(key, '').strip()
            return float(v) if v else None
        CBCResult.objects.create(
            lab_order=order, patient=order.patient,
            wbc=dec('wbc'), neutrophils_pct=dec('neutrophils_pct'),
            lymphocytes_pct=dec('lymphocytes_pct'), monocytes_pct=dec('monocytes_pct'),
            eosinophils_pct=dec('eosinophils_pct'), basophils_pct=dec('basophils_pct'),
            rbc=dec('rbc'), hemoglobin=dec('hemoglobin'), hematocrit=dec('hematocrit'),
            mcv=dec('mcv'), mch=dec('mch'), mchc=dec('mchc'), rdw=dec('rdw'),
            platelets=dec('platelets'), mpv=dec('mpv'),
            analyzer_name=d.get('analyzer_name', ''),
            flags=d.get('flags', ''), raw_output=d.get('raw_output', ''),
            notes=d.get('notes', ''), recorded_by=request.user,
        )
        order.status = 'completed'
        order.save()
        messages.success(request, 'CBC result recorded!')
        return redirect('lab_order_detail', pk=order_pk)
    existing = CBCResult.objects.filter(lab_order=order).first()
    return render(request, 'clinical/cbc_form.html', {'order': order, 'existing': existing})


# ─── Chemistry Results ────────────────────────────────────────────────────────

@login_required
def chemistry_result_create(request, order_pk):
    from laboratory.models import LabOrder
    order = get_object_or_404(LabOrder, pk=order_pk)
    if request.method == 'POST':
        d = request.POST
        def dec(key):
            v = d.get(key, '').strip()
            return float(v) if v else None
        ChemistryResult.objects.create(
            lab_order=order, patient=order.patient,
            panel=d.get('panel', 'comprehensive'),
            glucose=dec('glucose'), bun=dec('bun'), creatinine=dec('creatinine'),
            egfr=dec('egfr'), sodium=dec('sodium'), potassium=dec('potassium'),
            chloride=dec('chloride'), co2=dec('co2'), calcium=dec('calcium'),
            alt=dec('alt'), ast=dec('ast'), alp=dec('alp'),
            bilirubin_total=dec('bilirubin_total'), bilirubin_direct=dec('bilirubin_direct'),
            albumin=dec('albumin'), total_protein=dec('total_protein'),
            cholesterol_total=dec('cholesterol_total'), hdl=dec('hdl'),
            ldl=dec('ldl'), triglycerides=dec('triglycerides'),
            tsh=dec('tsh'), t3=dec('t3'), t4=dec('t4'),
            troponin=dec('troponin'), ck_mb=dec('ck_mb'),
            analyzer_name=d.get('analyzer_name', ''),
            flags=d.get('flags', ''), raw_output=d.get('raw_output', ''),
            notes=d.get('notes', ''), recorded_by=request.user,
        )
        order.status = 'completed'
        order.save()
        messages.success(request, 'Chemistry result recorded!')
        return redirect('lab_order_detail', pk=order_pk)
    existing = ChemistryResult.objects.filter(lab_order=order).first()
    return render(request, 'clinical/chemistry_form.html', {
        'order': order, 'existing': existing,
        'panel_choices': ChemistryResult.PANEL_CHOICES,
    })


# ─── Radiology ────────────────────────────────────────────────────────────────

@login_required
def radiology_order_list(request):
    orders = RadiologyOrder.objects.select_related(
        'patient', 'requesting_doctor__user').order_by('-ordered_at')
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'clinical/radiology_list.html', {
        'orders': orders, 'status': status,
        'status_choices': RadiologyOrder.STATUS_CHOICES,
    })


@login_required
def radiology_order_create(request):
    patients = Patient.objects.filter(status='active').order_by('first_name')
    doctors = Doctor.objects.filter(status='active').select_related('user')
    if request.method == 'POST':
        d = request.POST
        patient = get_object_or_404(Patient, pk=d['patient'])
        doctor = get_object_or_404(Doctor, pk=d['requesting_doctor'])
        adm = IPDAdmission.objects.filter(pk=d.get('admission')).first()
        RadiologyOrder.objects.create(
            order_number=_next('RAD', RadiologyOrder),
            patient=patient, requesting_doctor=doctor, admission=adm,
            modality=d['modality'],
            body_part=d['body_part'],
            clinical_indication=d['clinical_indication'],
            priority=d.get('priority', 'routine'),
        )
        messages.success(request, 'Radiology order created!')
        return redirect('radiology_order_list')
    return render(request, 'clinical/radiology_order_form.html', {
        'patients': patients, 'doctors': doctors,
        'modality_choices': RadiologyOrder.MODALITY_CHOICES,
        'priority_choices': [('routine','Routine'),('urgent','Urgent'),('emergency','Emergency')],
    })


@login_required
def radiology_report(request, pk):
    order = get_object_or_404(RadiologyOrder, pk=pk)
    existing = RadiologyResult.objects.filter(order=order).first()
    if request.method == 'POST':
        if existing:
            existing.findings = request.POST.get('findings', '')
            existing.impression = request.POST.get('impression', '')
            existing.recommendations = request.POST.get('recommendations', '')
            if 'image' in request.FILES:
                existing.image = request.FILES['image']
            existing.reported_by = request.user
            existing.save()
        else:
            existing = RadiologyResult.objects.create(
                order=order,
                findings=request.POST.get('findings', ''),
                impression=request.POST.get('impression', ''),
                recommendations=request.POST.get('recommendations', ''),
                image=request.FILES.get('image'),
                reported_by=request.user,
            )
        # upload additional images
        for img_file in request.FILES.getlist('additional_images'):
            ri = RadiologyImage.objects.create(order=order, image=img_file,
                                               caption=request.POST.get('caption', ''))
            existing.additional_images.add(ri)
        order.status = 'reported'
        order.reported_at = timezone.now()
        order.radiologist = request.user
        order.save()
        messages.success(request, 'Radiology report saved!')
        return redirect('radiology_order_list')
    images = order.images.all()
    return render(request, 'clinical/radiology_report_form.html', {
        'order': order, 'existing': existing, 'images': images,
    })
