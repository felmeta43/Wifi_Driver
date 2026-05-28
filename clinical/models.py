from django.db import models
from django.utils import timezone


# ─── OPD / IPD ──────────────────────────────────────────────────────────────

class OPDVisit(models.Model):
    TRIAGE_CHOICES = [
        ('1_resuscitation', 'Level 1 – Resuscitation'),
        ('2_emergent', 'Level 2 – Emergent'),
        ('3_urgent', 'Level 3 – Urgent'),
        ('4_less_urgent', 'Level 4 – Less Urgent'),
        ('5_non_urgent', 'Level 5 – Non-Urgent'),
    ]
    STATUS_CHOICES = [
        ('waiting', 'Waiting'),
        ('with_doctor', 'With Doctor'),
        ('completed', 'Completed'),
        ('referred', 'Referred'),
        ('admitted', 'Admitted'),
    ]
    visit_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='opd_visits')
    doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='opd_visits')
    appointment = models.OneToOneField('appointments.Appointment', on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='opd_visit')
    visit_date = models.DateField(auto_now_add=True)
    arrival_time = models.TimeField(auto_now_add=True)
    triage_level = models.CharField(max_length=20, choices=TRIAGE_CHOICES,
                                    default='5_non_urgent')
    chief_complaint = models.TextField()
    vital_signs = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='waiting')
    referred_to = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    registered_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                      null=True, related_name='opd_registrations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OPD {self.visit_number} – {self.patient.get_full_name()}"


class IPDAdmission(models.Model):
    ROOM_TYPE_CHOICES = [
        ('general', 'General Ward'),
        ('private', 'Private Room'),
        ('semi_private', 'Semi-Private'),
        ('icu', 'ICU'),
        ('nicu', 'NICU'),
        ('emergency', 'Emergency'),
        ('isolation', 'Isolation'),
        ('ot', 'Operation Theatre'),
    ]
    STATUS_CHOICES = [
        ('admitted', 'Admitted'),
        ('transferred', 'Transferred'),
        ('discharged', 'Discharged'),
        ('absconded', 'Absconded'),
        ('deceased', 'Deceased'),
    ]
    admission_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='ipd_admissions')
    admitting_doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL,
                                         null=True, related_name='ipd_admissions')
    department = models.ForeignKey('core.Department', on_delete=models.SET_NULL,
                                   null=True, blank=True)
    ward = models.CharField(max_length=100, blank=True)
    room_number = models.CharField(max_length=20)
    bed_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=15, choices=ROOM_TYPE_CHOICES, default='general')
    admission_date = models.DateTimeField(auto_now_add=True)
    expected_discharge = models.DateField(null=True, blank=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='admitted')
    admission_diagnosis = models.TextField()
    final_diagnosis = models.TextField(blank=True)
    attending_nurse = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                        null=True, blank=True, related_name='ipd_patients')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-admission_date']

    def get_los(self):
        """Length of stay in days."""
        end = self.discharge_date or timezone.now()
        delta = end - self.admission_date
        return delta.days

    def __str__(self):
        return f"IPD {self.admission_number} – {self.patient.get_full_name()}"


class DischargeRecord(models.Model):
    admission = models.OneToOneField(IPDAdmission, on_delete=models.CASCADE,
                                     related_name='discharge_record')
    discharge_date = models.DateTimeField(auto_now_add=True)
    discharge_condition = models.CharField(max_length=100, blank=True)
    discharge_diagnosis = models.TextField()
    treatment_summary = models.TextField()
    discharge_instructions = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    follow_up_doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL,
                                         null=True, blank=True)
    diet_instructions = models.TextField(blank=True)
    activity_restrictions = models.TextField(blank=True)
    discharge_medications = models.TextField(blank=True)
    discharged_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Discharge: {self.admission}"


# ─── Clinical Notes ──────────────────────────────────────────────────────────

class ClinicalNote(models.Model):
    NOTE_TYPES = [
        ('progress', 'Progress Note'),
        ('soap', 'SOAP Note'),
        ('nursing', 'Nursing Note'),
        ('assessment', 'Nursing Assessment'),
        ('diet', 'Diet Note'),
        ('social', 'Social Work Note'),
        ('physio', 'Physiotherapy Note'),
        ('other', 'Other'),
    ]
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='clinical_notes')
    admission = models.ForeignKey(IPDAdmission, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='clinical_notes')
    opd_visit = models.ForeignKey(OPDVisit, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='clinical_notes')
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='progress')
    title = models.CharField(max_length=250)
    # SOAP fields (optional – used when note_type='soap')
    subjective = models.TextField(blank=True)
    objective = models.TextField(blank=True)
    assessment = models.TextField(blank=True)
    plan = models.TextField(blank=True)
    # free text
    content = models.TextField(blank=True)
    vital_signs = models.JSONField(default=dict, blank=True)
    written_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_note_type_display()} – {self.patient} – {self.created_at.date()}"


class OperationNote(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='operation_notes')
    admission = models.ForeignKey(IPDAdmission, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='operation_notes')
    operation_number = models.CharField(max_length=20, unique=True)
    procedure_name = models.CharField(max_length=300)
    operation_date = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='scheduled')
    surgeon = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL,
                                null=True, related_name='surgeries')
    assistant_surgeon = models.CharField(max_length=200, blank=True)
    anesthetist = models.CharField(max_length=200, blank=True)
    anesthesia_type = models.CharField(max_length=100, blank=True)
    scrub_nurse = models.CharField(max_length=200, blank=True)
    circulating_nurse = models.CharField(max_length=200, blank=True)
    pre_op_diagnosis = models.TextField()
    post_op_diagnosis = models.TextField(blank=True)
    indication = models.TextField(blank=True)
    procedure_details = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    complications = models.TextField(blank=True)
    blood_loss = models.CharField(max_length=50, blank=True)
    specimens_sent = models.TextField(blank=True)
    drains = models.TextField(blank=True)
    closure = models.TextField(blank=True)
    post_op_instructions = models.TextField(blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                   null=True, related_name='operation_notes_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-operation_date']

    def __str__(self):
        return f"Op {self.operation_number} – {self.procedure_name} – {self.patient}"


# ─── Consultation & Handover ─────────────────────────────────────────────────

class ConsultationRequest(models.Model):
    PRIORITY_CHOICES = [
        ('routine', 'Routine'),
        ('urgent', 'Urgent'),
        ('emergency', 'Emergency'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('declined', 'Declined'),
    ]
    request_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='consultation_requests')
    admission = models.ForeignKey(IPDAdmission, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='consultation_requests')
    requesting_doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL,
                                          null=True, related_name='consultations_requested')
    consulting_doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL,
                                          null=True, related_name='consultations_received')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='routine')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    clinical_summary = models.TextField(blank=True)
    response = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Consult {self.request_number} – {self.patient}"


class PatientHandover(models.Model):
    SHIFT_CHOICES = [
        ('morning', 'Morning (07:00–15:00)'),
        ('afternoon', 'Afternoon (15:00–23:00)'),
        ('night', 'Night (23:00–07:00)'),
    ]
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='handovers')
    admission = models.ForeignKey(IPDAdmission, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='handovers')
    handover_from = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                      null=True, related_name='handovers_given')
    handover_to = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                    null=True, related_name='handovers_received')
    shift = models.CharField(max_length=15, choices=SHIFT_CHOICES)
    handover_date = models.DateField(auto_now_add=True)
    handover_time = models.TimeField(auto_now_add=True)
    current_condition = models.TextField()
    vital_signs = models.JSONField(default=dict, blank=True)
    active_issues = models.TextField(blank=True)
    pending_tasks = models.TextField(blank=True)
    medications_due = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Handover: {self.patient} – {self.handover_date} {self.shift}"


# ─── Medical Files ───────────────────────────────────────────────────────────

class MedicalFile(models.Model):
    FILE_TYPES = [
        ('report', 'Lab / Diagnostic Report'),
        ('image', 'Medical Image'),
        ('xray', 'X-Ray'),
        ('ecg', 'ECG'),
        ('scan', 'CT / MRI Scan'),
        ('document', 'Document'),
        ('consent', 'Consent Form'),
        ('prescription', 'Prescription'),
        ('discharge', 'Discharge Summary'),
        ('other', 'Other'),
    ]
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='medical_files')
    admission = models.ForeignKey(IPDAdmission, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='medical_files')
    file_type = models.CharField(max_length=15, choices=FILE_TYPES, default='document')
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='medical_files/%Y/%m/')
    uploaded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_file_type_display()} – {self.title} – {self.patient}"

    def is_image(self):
        ext = self.file.name.lower().split('.')[-1]
        return ext in ('jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'dcm')


# ─── Machine / Analyzer Results ─────────────────────────────────────────────

class CBCResult(models.Model):
    """Structured Complete Blood Count result (from CBC analyzer)."""
    lab_order = models.ForeignKey('laboratory.LabOrder', on_delete=models.CASCADE,
                                  related_name='cbc_results')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='cbc_results')
    # WBC series
    wbc = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text='×10³/µL')
    neutrophils_pct = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='%')
    lymphocytes_pct = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='%')
    monocytes_pct = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='%')
    eosinophils_pct = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='%')
    basophils_pct = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='%')
    # RBC series
    rbc = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='×10⁶/µL')
    hemoglobin = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='g/dL')
    hematocrit = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='%')
    mcv = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, help_text='fL')
    mch = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, help_text='pg')
    mchc = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, help_text='g/dL')
    rdw = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='%')
    # Platelets
    platelets = models.DecimalField(max_digits=8, decimal_places=0, null=True, blank=True, help_text='×10³/µL')
    mpv = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text='fL')
    # Meta
    analyzer_name = models.CharField(max_length=100, blank=True)
    flags = models.TextField(blank=True, help_text='Analyzer flags / comments')
    raw_output = models.TextField(blank=True, help_text='Raw CSV/HL7 from machine')
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CBC – {self.patient} – {self.recorded_at.date()}"


class ChemistryResult(models.Model):
    """Structured Chemistry Analyzer result."""
    PANEL_CHOICES = [
        ('basic', 'Basic Metabolic Panel'),
        ('comprehensive', 'Comprehensive Metabolic Panel'),
        ('lipid', 'Lipid Panel'),
        ('liver', 'Liver Function Tests'),
        ('kidney', 'Kidney Function Tests'),
        ('thyroid', 'Thyroid Panel'),
        ('cardiac', 'Cardiac Markers'),
        ('custom', 'Custom'),
    ]
    lab_order = models.ForeignKey('laboratory.LabOrder', on_delete=models.CASCADE,
                                  related_name='chemistry_results')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='chemistry_results')
    panel = models.CharField(max_length=15, choices=PANEL_CHOICES, default='comprehensive')
    # Metabolic
    glucose = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text='mg/dL')
    bun = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text='mg/dL')
    creatinine = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='mg/dL')
    egfr = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True, help_text='mL/min')
    sodium = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, help_text='mEq/L')
    potassium = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='mEq/L')
    chloride = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, help_text='mEq/L')
    co2 = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, help_text='mEq/L')
    calcium = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='mg/dL')
    # Liver
    alt = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True, help_text='U/L')
    ast = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True, help_text='U/L')
    alp = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True, help_text='U/L')
    bilirubin_total = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='mg/dL')
    bilirubin_direct = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='mg/dL')
    albumin = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='g/dL')
    total_protein = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text='g/dL')
    # Lipid
    cholesterol_total = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True, help_text='mg/dL')
    hdl = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True, help_text='mg/dL')
    ldl = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True, help_text='mg/dL')
    triglycerides = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True, help_text='mg/dL')
    # Thyroid
    tsh = models.DecimalField(max_digits=7, decimal_places=3, null=True, blank=True, help_text='mIU/L')
    t3 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='ng/dL')
    t4 = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text='µg/dL')
    # Cardiac
    troponin = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, help_text='ng/mL')
    ck_mb = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True, help_text='U/L')
    analyzer_name = models.CharField(max_length=100, blank=True)
    flags = models.TextField(blank=True)
    raw_output = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chemistry ({self.get_panel_display()}) – {self.patient} – {self.recorded_at.date()}"


class RadiologyOrder(models.Model):
    MODALITY_CHOICES = [
        ('xray', 'X-Ray'),
        ('ct', 'CT Scan'),
        ('mri', 'MRI'),
        ('ultrasound', 'Ultrasound'),
        ('ecg', 'ECG'),
        ('echo', 'Echocardiography'),
        ('mammogram', 'Mammogram'),
        ('dexa', 'DEXA Scan'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('in_progress', 'In Progress'),
        ('reported', 'Reported'),
        ('cancelled', 'Cancelled'),
    ]
    order_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE,
                                related_name='radiology_orders')
    requesting_doctor = models.ForeignKey('doctors.Doctor', on_delete=models.SET_NULL,
                                          null=True, related_name='radiology_orders')
    admission = models.ForeignKey(IPDAdmission, on_delete=models.SET_NULL,
                                  null=True, blank=True, related_name='radiology_orders')
    modality = models.CharField(max_length=15, choices=MODALITY_CHOICES)
    body_part = models.CharField(max_length=150)
    clinical_indication = models.TextField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ordered')
    priority = models.CharField(max_length=10,
                                choices=[('routine','Routine'),('urgent','Urgent'),('emergency','Emergency')],
                                default='routine')
    ordered_at = models.DateTimeField(auto_now_add=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    radiologist = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='radiology_reports')

    class Meta:
        ordering = ['-ordered_at']

    def __str__(self):
        return f"{self.order_number} – {self.get_modality_display()} – {self.patient}"


class RadiologyResult(models.Model):
    order = models.OneToOneField(RadiologyOrder, on_delete=models.CASCADE,
                                 related_name='result')
    findings = models.TextField()
    impression = models.TextField()
    recommendations = models.TextField(blank=True)
    image = models.FileField(upload_to='radiology/%Y/%m/', null=True, blank=True,
                             help_text='Upload JPEG/PNG/PDF/DICOM image')
    additional_images = models.ManyToManyField('RadiologyImage', blank=True)
    reported_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    reported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report – {self.order}"


class RadiologyImage(models.Model):
    """Multiple images per radiology result."""
    order = models.ForeignKey(RadiologyOrder, on_delete=models.CASCADE,
                              related_name='images')
    image = models.FileField(upload_to='radiology/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.order}"
