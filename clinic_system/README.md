# Aurelia Clinic — Clinic Management System

A professional Flask + MySQL web application for clinic management, supporting Patients, Doctors, Pharmacists, and Admins.

## Features

- **Role-based authentication**: Patient, Doctor, Pharmacist, and Admin accounts
- **Appointment management**: Patients book, Doctors complete/cancel
- **Prescription system**: Doctors prescribe from medicine inventory
- **Medicine inventory**: Pharmacists manage stock and pricing
- **Invoicing**: Auto-generated invoices, pay/cancel workflow
- **Refined UI**: Editorial-medical aesthetic with Fraunces serif + Inter sans

## Tech Stack

- Backend: Python 3.9+, Flask 3.0
- Database: MySQL 8.0
- Frontend: Jinja2 templates, vanilla HTML/CSS (no JS framework)
- Security: Werkzeug password hashing, session-based auth, role decorators

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up MySQL database

Make sure MySQL is running. Then:

```bash
mysql -u root -p < database.sql
```

This creates the `clinic` database, all tables, and seeds sample data.

### 3. Configure database connection (optional)

By default the app connects to MySQL at `localhost` with user `root` and no password. Override via environment variables:

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=yourpassword
export DB_NAME=clinic
export SECRET_KEY=your-random-secret-here
```

### 4. Run the app

```bash
python app.py
```

Visit `http://localhost:5000`.

## Project Structure

```
clinic_system/
├── app.py                  # Flask application (all routes & logic)
├── database.sql            # Schema + sample data
├── requirements.txt
├── static/
│   └── css/style.css       # Stylesheet
└── templates/
    ├── base.html           # Layout (navbar, footer, flash)
    ├── index.html          # Landing page
    ├── login.html
    ├── register.html
    ├── dashboard_*.html    # Role-specific dashboards (×4)
    ├── doctors.html
    ├── appointments.html
    ├── book_appointment.html
    ├── medicines.html
    ├── add_medicine.html
    ├── prescriptions.html
    ├── add_prescription.html
    ├── invoices.html
    └── 404.html
```

## Default Accounts

The sample data includes user accounts, but the seeded passwords are placeholders.  
**Register fresh accounts via `/register` for each role** — the registration form will properly hash passwords.

To test all flows quickly:
1. Register a **Patient** → log in → book an appointment
2. Register a **Doctor** → log in → mark the appointment complete, write a prescription
3. Register a **Pharmacist** → log in → add new medicines, view prescriptions
4. Patient logs back in → pays the auto-generated invoice

## Database Schema

Tables: `Users`, `Doctors`, `Patients`, `Pharmacists`, `Appointments`, `Medicines`, `Prescriptions`, `Invoices`.

All role tables link to `Users.userID`. Foreign keys cascade on delete where appropriate. Check constraints enforce minimum name/phone lengths.

## Security Notes for Production

This system is suitable for a real working clinic with the following caveats — before production deployment:

- Set a strong `SECRET_KEY` via environment variable
- Use HTTPS (deploy behind nginx/Apache with TLS)
- Restrict the MySQL user (don't use `root` in production)
- Add CSRF tokens to forms (e.g., Flask-WTF)
- Enable rate limiting on `/login` and `/register`
- Set session cookie flags: `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`
- Add database backups
- Consider GDPR/HIPAA compliance depending on jurisdiction

## License

For your project use.
