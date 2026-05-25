"""
Clinic Management System
Flask + MySQL Web Application
"""

from flask import Flask,jsonify ,render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production-please')

# -----------------------------------------------------
# Database configuration
# -----------------------------------------------------
DB_CONFIG ={
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Hong9090$',       # add your root password if you set one
    'database': 'clinic',
    'port': 3306
}


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return None


def query_db(query, args=(), fetch=True, one=False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, args)

    rv = None
    if fetch:
        rv = cursor.fetchall()
        if one:
            rv = rv[0] if rv else None
    else:
        conn.commit()  # for INSERT/UPDATE/DELETE

    cursor.close()
    conn.close()
    return rv



def parse_datetime_local(value):
    """Convert HTML datetime-local input to MySQL DATETIME format."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None


# -----------------------------------------------------
# Authentication decorators
# -----------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'userID' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'userID' not in session:
                flash('Please log in to continue.', 'warning')
                return redirect(url_for('login'))
            if session.get('role') not in allowed_roles:
                flash('You do not have permission to access that page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# -----------------------------------------------------
# Public pages
# -----------------------------------------------------
@app.route('/')
def index():
    doctors = query_db(
        "SELECT doctorID, doctorName, specialization, consultationFee FROM Doctors LIMIT 6",
        fetch=True
    )
    return render_template('index.html', doctors=doctors)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', 'General enquiry').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Please provide your name, email, and message.', 'danger')
            return redirect(url_for('contact'))

        query_db(
            """INSERT INTO Messages (name, email, phone, subject, message)
               VALUES (%s,%s,%s,%s,%s)""",
            (name, email, phone, subject, message)
        )

        flash(f'Thank you {name}! We will get back to you within 24 hours.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')


# -----------------------------------------------------
# Auth: register, login, logout
# -----------------------------------------------------
VALID_SPECIALIZATIONS = ('Dermatology', 'Cosmetic', 'General', 'Pediatrics', 'Cardiology')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        role = request.form['role']
        email = request.form['email'].strip()
        phone = request.form['phone'].strip()
        full_name = request.form['full_name'].strip()

        # Basic validation
        if len(username) < 5:
            flash('Username must be at least 5 characters.', 'danger')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('register'))
        if role not in ('Doctor', 'Patient', 'Pharmacist'):
            flash('Invalid role.', 'danger')
            return redirect(url_for('register'))

        # Check duplicates
        existing = query_db(
            "SELECT userID FROM Users WHERE userName=%s OR email=%s",
            (username, email), fetch=True, one=True
        )
        if existing:
            flash('Username or email already registered.', 'danger')
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        user_id = query_db(
            "INSERT INTO Users (userName, password, roles, email, phone) VALUES (%s,%s,%s,%s,%s)",
            (username, hashed, role, email, phone)
        )

        # Insert into role-specific table
        if role == 'Doctor':
            specialization = request.form.get('specialization', 'General')
            if specialization not in VALID_SPECIALIZATIONS:
                specialization = 'General'
            query_db(
                "INSERT INTO Doctors (doctorName, specialization, userID, email, phone) VALUES (%s,%s,%s,%s,%s)",
                (full_name, specialization, user_id, email, phone)
            )
        elif role == 'Patient':
            query_db(
                "INSERT INTO Patients (patientName, userID, email, phone) VALUES (%s,%s,%s,%s)",
                (full_name, user_id, email, phone)
            )
        elif role == 'Pharmacist':
            query_db(
                "INSERT INTO Pharmacists (pharmacistName, userID, email, phone) VALUES (%s,%s,%s,%s)",
                (full_name, user_id, email, phone)
            )

        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = query_db(
            "SELECT * FROM Users WHERE userName=%s",
            (username,), fetch=True, one=True
        )

        if user and check_password_hash(user['password'], password):
            session['userID'] = user['userID']
            session['username'] = user['userName']
            session['role'] = user['roles']
            session['email'] = user['email']

            # Look up role profile ID
            if user['roles'] == 'Doctor':
                row = query_db("SELECT doctorID FROM Doctors WHERE userID=%s", (user['userID'],), fetch=True, one=True)
                session['profileID'] = row['doctorID'] if row else None
            elif user['roles'] == 'Patient':
                row = query_db("SELECT patientID FROM Patients WHERE userID=%s", (user['userID'],), fetch=True, one=True)
                session['profileID'] = row['patientID'] if row else None
            elif user['roles'] == 'Pharmacist':
                row = query_db("SELECT pharmacistID FROM Pharmacists WHERE userID=%s", (user['userID'],), fetch=True, one=True)
                session['profileID'] = row['pharmacistID'] if row else None
            else:
                session['profileID'] = None

            flash(f'Welcome back, {user["userName"]}!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


# -----------------------------------------------------
# Dashboard (role-aware)
# -----------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    stats = {}

    if role == 'Patient':
        pid = session.get('profileID')
        stats['upcoming'] = query_db(
            """SELECT COUNT(*) AS c FROM Appointments
               WHERE patientID=%s AND status='Scheduled'""",
            (pid,), fetch=True, one=True)['c']
        stats['completed'] = query_db(
            """SELECT COUNT(*) AS c FROM Appointments
               WHERE patientID=%s AND status='Completed'""",
            (pid,), fetch=True, one=True)['c']
        stats['invoices'] = query_db(
            """SELECT COUNT(*) AS c FROM Invoices i
               JOIN Appointments a ON i.appointmentID=a.appointmentID
               WHERE a.patientID=%s AND i.paymentStatus='Pending'""",
            (pid,), fetch=True, one=True)['c']

        recent = query_db(
            """SELECT a.appointmentID, a.appointmentDate, a.status, d.doctorName, d.specialization
               FROM Appointments a JOIN Doctors d ON a.doctorID=d.doctorID
               WHERE a.patientID=%s ORDER BY a.appointmentDate DESC LIMIT 5""",
            (pid,), fetch=True)
        return render_template('dashboard_patient.html', stats=stats, recent=recent)

    elif role == 'Doctor':
        did = session.get('profileID')
        stats['today'] = query_db(
            """SELECT COUNT(*) AS c FROM Appointments
               WHERE doctorID=%s AND DATE(appointmentDate)=CURDATE() AND status='Scheduled'""",
            (did,), fetch=True, one=True)['c']
        stats['upcoming'] = query_db(
            """SELECT COUNT(*) AS c FROM Appointments
               WHERE doctorID=%s AND status='Scheduled'""",
            (did,), fetch=True, one=True)['c']
        stats['patients'] = query_db(
            """SELECT COUNT(DISTINCT patientID) AS c FROM Appointments WHERE doctorID=%s""",
            (did,), fetch=True, one=True)['c']

        recent = query_db(
            """SELECT a.appointmentID, a.appointmentDate, a.status, a.reason,
                      p.patientName
               FROM Appointments a JOIN Patients p ON a.patientID=p.patientID
               WHERE a.doctorID=%s ORDER BY a.appointmentDate DESC LIMIT 5""",
            (did,), fetch=True)
        return render_template('dashboard_doctor.html', stats=stats, recent=recent)

    elif role == 'Pharmacist':
        stats['medicines'] = query_db("SELECT COUNT(*) AS c FROM Medicines", fetch=True, one=True)['c']
        stats['prescriptions'] = query_db(
            "SELECT COUNT(*) AS c FROM Prescriptions", fetch=True, one=True)['c']
        stats['low_stock'] = query_db(
            "SELECT COUNT(*) AS c FROM Medicines WHERE stock < 20", fetch=True, one=True)['c']

        recent = query_db(
            """SELECT pr.prescriptionID, pr.quantity, pr.createdAt,
                      m.medicineName, p.patientName
               FROM Prescriptions pr
               JOIN Medicines m ON pr.medicineID=m.medicineID
               JOIN Appointments a ON pr.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               ORDER BY pr.createdAt DESC LIMIT 5""",
            fetch=True)
        return render_template('dashboard_pharmacist.html', stats=stats, recent=recent)

    else:  # Admin
        stats['doctors'] = query_db("SELECT COUNT(*) AS c FROM Doctors", fetch=True, one=True)['c']
        stats['patients'] = query_db("SELECT COUNT(*) AS c FROM Patients", fetch=True, one=True)['c']
        stats['appointments'] = query_db("SELECT COUNT(*) AS c FROM Appointments", fetch=True, one=True)['c']
        stats['revenue'] = query_db(
            "SELECT COALESCE(SUM(amount),0) AS c FROM Invoices WHERE paymentStatus='Paid'",
            fetch=True, one=True)['c']
        return render_template('dashboard_admin.html', stats=stats)


# -----------------------------------------------------
# Doctors listing (public-ish)
# -----------------------------------------------------
@app.route('/doctors')
def doctors_list():
    doctors = query_db(
        "SELECT doctorID, doctorName, specialization, consultationFee, email FROM Doctors",
        fetch=True
    )
    return render_template('doctors.html', doctors=doctors)


# -----------------------------------------------------
# Appointments
# -----------------------------------------------------
@app.route('/appointments')
@login_required
def appointments():
    role = session.get('role')
    if role == 'Patient':
        rows = query_db(
            """SELECT a.*, d.doctorName, d.specialization
               FROM Appointments a JOIN Doctors d ON a.doctorID=d.doctorID
               WHERE a.patientID=%s ORDER BY a.appointmentDate DESC""",
            (session['profileID'],), fetch=True)
    elif role == 'Doctor':
        rows = query_db(
            """SELECT a.*, p.patientName, d.doctorName, d.specialization
               FROM Appointments a
               JOIN Patients p ON a.patientID=p.patientID
               JOIN Doctors d ON a.doctorID=d.doctorID
               WHERE a.doctorID=%s ORDER BY a.appointmentDate DESC""",
            (session['profileID'],), fetch=True)
    else:
        rows = query_db(
            """SELECT a.*, p.patientName, d.doctorName, d.specialization
               FROM Appointments a
               JOIN Patients p ON a.patientID=p.patientID
               JOIN Doctors d ON a.doctorID=d.doctorID
               ORDER BY a.appointmentDate DESC""", fetch=True)
    return render_template('appointments.html', appointments=rows)


@app.route('/appointments/book', methods=['GET', 'POST'])
@role_required('Patient')
def book_appointment():
    if request.method == 'POST':
        doctor_id = request.form['doctorID']
        appointment_date_raw = request.form['appointmentDate']
        appointment_date = parse_datetime_local(appointment_date_raw)
        reason = request.form.get('reason', '')

        if not appointment_date:
            flash('Please choose a valid date and time for the appointment.', 'danger')
            return redirect(url_for('book_appointment'))

        if not session.get('profileID'):
            flash('Unable to find your patient profile. Please contact support.', 'danger')
            return redirect(url_for('dashboard'))

        try:
            appt_id = query_db(
                """INSERT INTO Appointments (patientID, doctorID, appointmentDate, reason, status)
                   VALUES (%s,%s,%s,%s,'Scheduled')""",
                (session['profileID'], doctor_id, appointment_date, reason)
            )

            # Auto-generate an invoice based on the doctor's consultation fee
            fee_row = query_db("SELECT consultationFee FROM Doctors WHERE doctorID=%s",
                               (doctor_id,), fetch=True, one=True)
            fee = fee_row['consultationFee'] if fee_row else 50.00
            query_db(
                "INSERT INTO Invoices (appointmentID, amount, paymentStatus) VALUES (%s,%s,'Pending')",
                (appt_id, fee)
            )

            flash('Appointment booked successfully. Invoice issued.', 'success')
            return redirect(url_for('appointments'))
        except Error as e:
            flash(f'Error booking appointment: {e}', 'danger')

    doctors = query_db(
        "SELECT doctorID, doctorName, specialization, consultationFee FROM Doctors",
        fetch=True)
    return render_template('book_appointment.html', doctors=doctors)


@app.route('/appointments/<int:aid>/status/<string:new_status>')
@role_required('Doctor', 'Admin')
def update_appointment_status(aid, new_status):
    if new_status not in ('Scheduled', 'Completed', 'Cancelled'):
        flash('Invalid status.', 'danger')
        return redirect(url_for('appointments'))
    query_db("UPDATE Appointments SET status=%s WHERE appointmentID=%s", (new_status, aid))
    flash(f'Appointment marked as {new_status}.', 'success')
    return redirect(url_for('appointments'))


# -----------------------------------------------------
# Medicines
# -----------------------------------------------------
@app.route('/medicines')
@login_required
def medicines():
    rows = query_db("SELECT * FROM Medicines ORDER BY medicineName", fetch=True)
    return render_template('medicines.html', medicines=rows)


@app.route('/medicines/add', methods=['GET', 'POST'])
@role_required('Pharmacist', 'Admin')
def add_medicine():
    if request.method == 'POST':
        name = request.form['medicineName'].strip()
        category = request.form.get('category', '').strip()
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
        description = request.form.get('description', '').strip()

        query_db(
            """INSERT INTO Medicines (medicineName, category, price, stock, description)
               VALUES (%s,%s,%s,%s,%s)""",
            (name, category, price, stock, description)
        )
        flash('Medicine added.', 'success')
        return redirect(url_for('medicines'))
    return render_template('add_medicine.html')


@app.route('/medicines/<int:mid>/delete')
@role_required('Pharmacist', 'Admin')
def delete_medicine(mid):
    try:
        query_db("DELETE FROM Medicines WHERE medicineID=%s", (mid,))
        flash('Medicine deleted.', 'success')
    except Error as e:
        flash(f'Cannot delete: {e}', 'danger')
    return redirect(url_for('medicines'))


# -----------------------------------------------------
# Prescriptions
# -----------------------------------------------------
@app.route('/prescriptions')
@login_required
def prescriptions():
    role = session.get('role')
    if role == 'Patient':
        rows = query_db(
            """SELECT pr.*, m.medicineName, m.category, d.doctorName,
                      a.appointmentDate
               FROM Prescriptions pr
               JOIN Medicines m ON pr.medicineID=m.medicineID
               JOIN Appointments a ON pr.appointmentID=a.appointmentID
               JOIN Doctors d ON a.doctorID=d.doctorID
               WHERE a.patientID=%s ORDER BY pr.createdAt DESC""",
            (session['profileID'],), fetch=True)
    elif role == 'Doctor':
        rows = query_db(
            """SELECT pr.*, m.medicineName, m.category, p.patientName,
                      a.appointmentDate
               FROM Prescriptions pr
               JOIN Medicines m ON pr.medicineID=m.medicineID
               JOIN Appointments a ON pr.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               WHERE a.doctorID=%s ORDER BY pr.createdAt DESC""",
            (session['profileID'],), fetch=True)
    else:
        rows = query_db(
            """SELECT pr.*, m.medicineName, m.category, p.patientName, d.doctorName,
                      a.appointmentDate
               FROM Prescriptions pr
               JOIN Medicines m ON pr.medicineID=m.medicineID
               JOIN Appointments a ON pr.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               JOIN Doctors d ON a.doctorID=d.doctorID
               ORDER BY pr.createdAt DESC""", fetch=True)
    return render_template('prescriptions.html', prescriptions=rows)


@app.route('/prescriptions/add', methods=['GET', 'POST'])
@role_required('Doctor')
def add_prescription():
    if request.method == 'POST':
        appointment_id = request.form['appointmentID']
        medicine_id = request.form['medicineID']
        quantity = int(request.form.get('quantity', 1))
        instructions = request.form.get('instructions', '')

        query_db(
            """INSERT INTO Prescriptions (appointmentID, medicineID, quantity, instructions)
               VALUES (%s,%s,%s,%s)""",
            (appointment_id, medicine_id, quantity, instructions)
        )
        flash('Prescription created.', 'success')
        return redirect(url_for('prescriptions'))

    appts = query_db(
        """SELECT a.appointmentID, a.appointmentDate, p.patientName
           FROM Appointments a JOIN Patients p ON a.patientID=p.patientID
           WHERE a.doctorID=%s AND a.status IN ('Scheduled','Completed')
           ORDER BY a.appointmentDate DESC""",
        (session['profileID'],), fetch=True)
    meds = query_db("SELECT medicineID, medicineName, price FROM Medicines", fetch=True)
    return render_template('add_prescription.html', appointments=appts, medicines=meds)


# -----------------------------------------------------
# Invoices
# -----------------------------------------------------
@app.route('/invoices')
@login_required
def invoices():
    role = session.get('role')
    if role == 'Patient':
        rows = query_db(
            """SELECT i.*, a.appointmentDate, d.doctorName
               FROM Invoices i
               JOIN Appointments a ON i.appointmentID=a.appointmentID
               JOIN Doctors d ON a.doctorID=d.doctorID
               WHERE a.patientID=%s ORDER BY i.issuedAt DESC""",
            (session['profileID'],), fetch=True)
    elif role == 'Doctor':
        rows = query_db(
            """SELECT i.*, a.appointmentDate, p.patientName
               FROM Invoices i
               JOIN Appointments a ON i.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               WHERE a.doctorID=%s ORDER BY i.issuedAt DESC""",
            (session['profileID'],), fetch=True)
    else:
        rows = query_db(
            """SELECT i.*, a.appointmentDate, p.patientName, d.doctorName
               FROM Invoices i
               JOIN Appointments a ON i.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               JOIN Doctors d ON a.doctorID=d.doctorID
               ORDER BY i.issuedAt DESC""", fetch=True)
    return render_template('invoices.html', invoices=rows)


@app.route('/invoices/<int:iid>/pay')
@login_required
def pay_invoice(iid):
    query_db(
        "UPDATE Invoices SET paymentStatus='Paid', paidAt=NOW() WHERE invoiceID=%s",
        (iid,))
    flash('Invoice marked as paid.', 'success')
    return redirect(url_for('invoices'))


@app.route('/invoices/<int:iid>/cancel')
@role_required('Admin', 'Pharmacist')
def cancel_invoice(iid):
    query_db("UPDATE Invoices SET paymentStatus='Cancelled' WHERE invoiceID=%s", (iid,))
    flash('Invoice cancelled.', 'info')
    return redirect(url_for('invoices'))


@app.route('/messages')
@role_required('Admin')
def messages():
    rows = query_db(
        "SELECT messageID, name, email, phone, subject, message, createdAt"
        " FROM Messages ORDER BY createdAt DESC",
        fetch=True
    )
    return render_template('messages.html', messages=rows)


# -----------------------------------------------------
# Error handlers
# -----------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


# -----------------------------------------------------
# Run
# -----------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)