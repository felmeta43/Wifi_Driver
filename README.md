# Hospital Management System

A full-stack, customizable Hospital Management System built with Django 5.

## Features

- **Dashboard** – Live stats, revenue chart, recent activity
- **Patient Management** – Registration, medical records, admissions, full history
- **Doctor Management** – Profiles, specializations, weekly schedules
- **Appointment Scheduling** – Book, track and manage appointments
- **Laboratory** – Lab order management, result entry, abnormal flagging
- **Pharmacy** – Medicine inventory, prescriptions, dispensing, stock control
- **Billing** – Invoicing, payment tracking, revenue reports (printable)
- **Staff Management** – Role-based user accounts (Admin, Doctor, Nurse, Receptionist, Pharmacist, Lab Tech, Accountant)
- **Hospital Settings** – Fully customizable name, logo, colors, currency, tax, contact info
- **Departments** – Configurable departments with icons

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_hospital       # creates admin/admin123 + seed data
python manage.py load_demo_data       # optional demo patients/doctors/etc.
python manage.py runserver
```

Open http://127.0.0.1:8000 and log in with **admin / admin123**

## Default Credentials

| Role          | Username       | Password   |
|---------------|----------------|------------|
| Administrator | admin          | admin123   |
| Receptionist  | receptionist   | recep123   |
| Doctors       | dr.smith etc.  | doctor123  |

## Customization

Visit **Hospital Settings** (admin sidebar) to change:
- Hospital name, logo, tagline
- Primary/secondary brand colors
- Currency symbol and tax rate
- Address, phone, email, social links
