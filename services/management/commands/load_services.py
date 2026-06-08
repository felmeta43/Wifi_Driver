"""
Management command to load all hospital services from the Excel file.

Usage:
    python manage.py load_services
    python manage.py load_services --excel /path/to/services.xlsx
    python manage.py load_services --clear          # wipe existing services first
    python manage.py load_services --skip-lab-tests # skip populating LabTest table

Sheets loaded:
    Card        → ServiceCategory "Consultation Cards"   (service_type=opd)
    Laboratory  → ServiceCategory "Laboratory"           (service_type=diagnostic) + LabTest
    Imaging     → ServiceCategory "Imaging / Radiology"  (service_type=diagnostic)
    General     → ServiceCategory "General Nursing"      (service_type=other)
    Procedure   → ServiceCategory "Procedure / Surgery"  (service_type=procedure)
    Cardiology  → ServiceCategory "Cardiology"           (service_type=diagnostic)
    Pathology   → ServiceCategory "Pathology"            (service_type=diagnostic)
    Endoscopy   → ServiceCategory "Endoscopy"            (service_type=procedure)
"""

import os
import re
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError

try:
    import openpyxl
except ImportError:
    raise CommandError("openpyxl is required. Run: pip install openpyxl")

from services.models import Service, ServiceCategory
from laboratory.models import LabTest


# ── Sheet → category meta ─────────────────────────────────────────────────────
SHEET_CONFIG = [
    # (sheet_name, category_name, service_type, code_prefix, icon)
    ('Card',       'Consultation Cards',    'opd',        'CONS', 'fa-id-card'),
    ('Laboratory', 'Laboratory',            'diagnostic', 'LAB',  'fa-flask'),
    ('Imaging',    'Imaging / Radiology',   'diagnostic', 'IMG',  'fa-x-ray'),
    ('General',    'General Nursing',       'other',      'GEN',  'fa-hand-holding-medical'),
    ('Procedure',  'Procedure / Surgery',   'procedure',  'PROC', 'fa-scalpel-path'),
    ('Cardiology', 'Cardiology',            'diagnostic', 'CRDLG','fa-heart'),
    ('Pathology',  'Pathology',             'diagnostic', 'PATH', 'fa-microscope'),
    ('Endoscopy',  'Endoscopy',             'procedure',  'ENDO', 'fa-stethoscope'),
]

# Lab tests that are orderable panels/tests (not sub-parameters of another test).
# We mark items whose parent is a TOP-LEVEL group as orderable, and items that
# ARE top-level groups themselves as categories (skip as Service but create as
# ServiceCategory description).  Sub-parameters (e.g. WBC inside CBC) are
# stored as LabTest for result entry but not as a standalone Service order.

LAB_TOP_LEVEL_GROUPS = {
    'HEMATOLOGY', 'SEROLOGY', 'CLINICAL CHEMISTRY', 'HORMONE ANALYSIS',
    'MICRO-BIOLOGY', 'PARA-MICRO', 'BODY FLUID ANALYSIS',
}


def _slug(text, prefix, n):
    """Generate a short unique code, e.g. LAB001."""
    return f"{prefix}{n:04d}"


def _clean(val):
    """Return stripped string or empty string for None."""
    if val is None:
        return ''
    return str(val).strip()


def _price(val):
    """Parse price cell; return Decimal(0) if blank/None."""
    if val is None:
        return Decimal('0')
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal('0')


def _normal_range(low, high):
    """Build a normal range string from two cells."""
    low, high = _clean(low), _clean(high)
    if low and high:
        return f"{low} – {high}"
    if low:
        return f"≥ {low}"
    if high:
        return f"≤ {high}"
    return ''


class Command(BaseCommand):
    help = 'Load hospital services from Excel file into Service / LabTest tables.'

    def add_arguments(self, parser):
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))),
            'data', 'services.xlsx',
        )
        parser.add_argument(
            '--excel',
            default=default_path,
            help='Path to the Excel file (default: data/services.xlsx)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing Service and ServiceCategory records first.',
        )
        parser.add_argument(
            '--skip-lab-tests',
            action='store_true',
            help='Do not populate the LabTest table.',
        )

    # ──────────────────────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        excel_path = options['excel']
        if not os.path.exists(excel_path):
            raise CommandError(
                f"Excel file not found: {excel_path}\n"
                "Copy it to data/services.xlsx or pass --excel <path>."
            )

        self.stdout.write(f"Reading {excel_path} …")
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
        except Exception as e:
            raise CommandError(f"Cannot open Excel file: {e}")

        if options['clear']:
            Service.objects.all().delete()
            ServiceCategory.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing services and categories."))

        totals = {'categories': 0, 'services': 0, 'lab_tests': 0, 'skipped': 0}

        for sheet_name, cat_name, svc_type, prefix, icon in SHEET_CONFIG:
            if sheet_name not in wb.sheetnames:
                self.stdout.write(self.style.WARNING(f"  Sheet '{sheet_name}' not found, skipping."))
                continue

            # Create / get the ServiceCategory
            category, created = ServiceCategory.objects.get_or_create(
                name=cat_name,
                defaults={'icon': icon, 'is_active': True},
            )
            if created:
                totals['categories'] += 1

            ws = wb[sheet_name]

            if sheet_name == 'Laboratory':
                n_svc, n_lab = self._load_laboratory(
                    ws, category, svc_type, prefix,
                    options['skip_lab_tests'], totals,
                )
                self.stdout.write(
                    f"  {sheet_name:12s} → {n_svc} services, {n_lab} lab tests"
                )
            elif sheet_name == 'Imaging':
                n = self._load_imaging(ws, category, svc_type, prefix, totals)
                self.stdout.write(f"  {sheet_name:12s} → {n} services")
            else:
                n = self._load_generic(ws, category, svc_type, prefix, totals)
                self.stdout.write(f"  {sheet_name:12s} → {n} services")

        self.stdout.write(self.style.SUCCESS(
            f"\nDone.  Categories: {totals['categories']}  "
            f"Services: {totals['services']}  "
            f"Lab tests: {totals['lab_tests']}  "
            f"Skipped (duplicate): {totals['skipped']}"
        ))

    # ── Generic sheets (Card, General, Procedure, Cardiology, Pathology, Endoscopy)
    def _load_generic(self, ws, category, svc_type, prefix, totals):
        counter = Service.objects.filter(code__startswith=prefix).count()
        loaded = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            name = _clean(row[1] if len(row) > 1 else None)
            if not name:
                continue
            avail = _clean(row[4] if len(row) > 4 else 'y').lower()
            price = _price(row[3] if len(row) > 3 else None)
            parent = _clean(row[2] if len(row) > 2 else None)
            description = f"Parent service: {parent}" if parent else ''

            counter += 1
            code = _slug(name, prefix, counter)
            _, created = Service.objects.get_or_create(
                name=name,
                category=category,
                defaults={
                    'code': code,
                    'service_type': svc_type,
                    'price': price,
                    'description': description,
                    'is_active': avail != 'n',
                    'requires_doctor': svc_type in ('opd', 'procedure'),
                    'duration_minutes': 30,
                },
            )
            if created:
                totals['services'] += 1
                loaded += 1
            else:
                totals['skipped'] += 1
        return loaded

    # ── Laboratory sheet ──────────────────────────────────────────────────────
    def _load_laboratory(self, ws, category, svc_type, prefix, skip_lab, totals):
        """
        Columns: No | Service Name | Parent | Price | Available? |
                 UOM | Data Type | N.Range From | N.Range To | T.Range Low | T.Range High | ...
        Strategy:
          - Top-level group rows (no parent, not a sub-test) → skip as Service
          - Second-level panels (e.g. CBC, LIVER FUNCTION TEST) → create Service + LabTest
          - Sub-parameter rows (e.g. WBC under CBC) → create LabTest only (not orderable Service)
        """
        # First pass: collect all names → parents to classify
        rows_data = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            name = _clean(row[1] if len(row) > 1 else None)
            if not name:
                continue
            rows_data.append({
                'name':   name,
                'parent': _clean(row[2] if len(row) > 2 else None),
                'price':  _price(row[3] if len(row) > 3 else None),
                'avail':  _clean(row[4] if len(row) > 4 else 'y').lower(),
                'uom':    _clean(row[5] if len(row) > 5 else None),
                'dtype':  _clean(row[6] if len(row) > 6 else None),
                'nlow':   _clean(row[7] if len(row) > 7 else None),
                'nhigh':  _clean(row[8] if len(row) > 8 else None),
            })

        # Build a set of names that ARE parents of other rows (so they're group headers)
        parent_names = {r['parent'] for r in rows_data if r['parent']}
        # Top-level groups = no parent themselves AND they act as parents of others
        top_level_groups = {
            r['name'] for r in rows_data
            if not r['parent'] and r['name'] in parent_names
        }
        # Second-level = parent is a top-level group → these are orderable services
        orderable = {
            r['name'] for r in rows_data
            if r['parent'] in top_level_groups
        }

        svc_counter = Service.objects.filter(code__startswith=prefix).count()
        lab_counter = LabTest.objects.count()
        n_svc = 0
        n_lab = 0

        for r in rows_data:
            name   = r['name']
            parent = r['parent']
            uom    = r['uom']
            nrange = _normal_range(r['nlow'], r['nhigh'])
            price  = r['price']
            avail  = r['avail'] != 'n'

            description = f"Panel: {parent}" if parent else ''

            # ── Create LabTest for anything with UOM or normal range, or orderable tests
            if not skip_lab and (uom or nrange or name in orderable):
                _, created = LabTest.objects.get_or_create(
                    name=name,
                    defaults={
                        'unit': uom,
                        'normal_range': nrange,
                        'price': price,
                        'description': description,
                        'is_active': avail,
                    },
                )
                if created:
                    totals['lab_tests'] += 1
                    n_lab += 1

            # ── Create Service for orderable panels (second-level) only
            if name in orderable or (not parent and name not in top_level_groups):
                svc_counter += 1
                code = _slug(name, prefix, svc_counter)
                _, created = Service.objects.get_or_create(
                    name=name,
                    category=category,
                    defaults={
                        'code': code,
                        'service_type': svc_type,
                        'price': price,
                        'description': description,
                        'is_active': avail,
                        'requires_doctor': True,
                        'duration_minutes': 60,
                    },
                )
                if created:
                    totals['services'] += 1
                    n_svc += 1
                else:
                    totals['skipped'] += 1

        return n_svc, n_lab

    # ── Imaging sheet ─────────────────────────────────────────────────────────
    def _load_imaging(self, ws, category, svc_type, prefix, totals):
        """
        Columns: # | Service Name | Parent (XRAY / ULTRASOUND / CT SCAN…) | Price | Available? | Body Part
        Create one Service per row; skip the parent-only header rows (no body part, no #).
        """
        # Collect parents from the sheet (ULTRASOUND, X-RAY, CT SCAN, MRI …)
        parent_names = set()
        all_rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            name   = _clean(row[1] if len(row) > 1 else None)
            parent = _clean(row[2] if len(row) > 2 else None)
            if name:
                all_rows.append((name, parent, row))
                if parent:
                    parent_names.add(parent)

        # Top-level modality groups (they appear as parent but have no parent themselves)
        modality_groups = {
            name for name, parent, _ in all_rows
            if not parent and name in parent_names
        }

        counter = Service.objects.filter(code__startswith=prefix).count()
        loaded  = 0

        for name, parent, row in all_rows:
            if name in modality_groups:
                continue  # skip ULTRASOUND / X-RAY header rows

            price      = _price(row[3] if len(row) > 3 else None)
            avail      = _clean(row[4] if len(row) > 4 else 'y').lower()
            body_part  = _clean(row[5] if len(row) > 5 else None)
            description = ' | '.join(filter(None, [
                f"Modality: {parent}" if parent else '',
                f"Body part: {body_part}" if body_part else '',
            ]))

            counter += 1
            code = _slug(name, prefix, counter)
            _, created = Service.objects.get_or_create(
                name=name,
                category=category,
                defaults={
                    'code': code,
                    'service_type': svc_type,
                    'price': price,
                    'description': description,
                    'is_active': avail != 'n',
                    'requires_doctor': True,
                    'duration_minutes': 45,
                },
            )
            if created:
                totals['services'] += 1
                loaded += 1
            else:
                totals['skipped'] += 1

        return loaded
