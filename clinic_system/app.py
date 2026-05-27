"""
Clinic Management System
Flask + MySQL Web Application
"""

from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
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
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Hong9090$',      
    'database': 'clinic',
    'port': 3306,
    'use_pure': True,              # IMPORTANT: use the pure-Python connector.
                                   # The C extension (connection_cext) throws
                                   # "Python type ... cannot be converted" on
                                   # newer Python versions. This avoids it.
}


def get_db_connection():
    """Open a new database connection. Returns None on failure."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return None


def query_db(query, args=(), fetch=True, one=False):
    """
    Generic DB helper.

    - SELECT statements: returns rows (a list, or a single dict if one=True).
    - INSERT / UPDATE / DELETE: commits and returns the new row id (lastrowid).

    NOTE: detection is based on whether the query starts with SELECT, so you do
    NOT need to pass fetch=False for writes anymore. This is the key fix: the
    previous version only committed when fetch=False, so every INSERT silently
    failed to save.
    """
    conn = get_db_connection()
    if conn is None:
        # Surface a clear error instead of crashing on conn.cursor()
        raise Exception(
            "Could not connect to the database. "
            "Check that MySQL is running and DB_CONFIG (host/user/password/database/port) is correct."
        )

    cursor = conn.cursor(dictionary=True)
    try:
       
        if args is None:
            args = ()
        elif not isinstance(args, (list, tuple)):
            args = (args,)
        args = tuple(args)

        cursor.execute(query, args)

        if query.strip().lower().startswith('select'):
            rv = cursor.fetchall()
            if one:
                rv = rv[0] if rv else None
            return rv
        else:
            conn.commit()                # commit INSERT/UPDATE/DELETE
            return cursor.lastrowid      # so user_id / appt_id work again
    finally:
        cursor.close()
        conn.close()


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
        "SELECT doctorID, doctorName, specialization, consultationFee FROM Doctors LIMIT 6"
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
        # NOTE: Admin is intentionally NOT allowed here. Letting anyone register
        # as Admin via a public form would be a security hole. Create admins by
        # seeding the database with a hashed password instead (see seed_admin.py).
        if role not in ('Doctor', 'Patient', 'Pharmacist'):
            flash('Invalid role.', 'danger')
            return redirect(url_for('register'))

        # Check duplicates
        existing = query_db(
            "SELECT userID FROM Users WHERE userName=%s OR email=%s",
            (username, email), one=True
        )
        if existing:
            flash('Username or email already registered.', 'danger')
            return redirect(url_for('register'))

        hashed = generate_password_hash(password)
        user_id = query_db(
            "INSERT INTO Users (userName, password, roles, email, phone) VALUES (%s,%s,%s,%s,%s)",
            (username, hashed, role, email, phone)
        )
        
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
            (username,), one=True
        )

        if user and check_password_hash(user['password'], password):
            session['userID'] = user['userID']
            session['username'] = user['userName']
            session['role'] = user['roles']
            session['email'] = user['email']

            if user['roles'] == 'Doctor':
                row = query_db("SELECT doctorID FROM Doctors WHERE userID=%s", (user['userID'],), one=True)
                session['profileID'] = row['doctorID'] if row else None
            elif user['roles'] == 'Patient':
                row = query_db("SELECT patientID FROM Patients WHERE userID=%s", (user['userID'],), one=True)
                session['profileID'] = row['patientID'] if row else None
            elif user['roles'] == 'Pharmacist':
                row = query_db("SELECT pharmacistID FROM Pharmacists WHERE userID=%s", (user['userID'],), one=True)
                session['profileID'] = row['pharmacistID'] if row else None
            else:  # Admin has no profile table
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
            (pid,), one=True)['c']
        stats['completed'] = query_db(
            """SELECT COUNT(*) AS c FROM Appointments
               WHERE patientID=%s AND status='Completed'""",
            (pid,), one=True)['c']
        stats['invoices'] = query_db(
            """SELECT COUNT(*) AS c FROM Invoices i
               JOIN Appointments a ON i.appointmentID=a.appointmentID
               WHERE a.patientID=%s AND i.paymentStatus='Pending'""",
            (pid,), one=True)['c']

        recent = query_db(
            """SELECT a.appointmentID, a.appointmentDate, a.status, d.doctorName, d.specialization
               FROM Appointments a JOIN Doctors d ON a.doctorID=d.doctorID
               WHERE a.patientID=%s ORDER BY a.appointmentDate DESC LIMIT 5""",
            (pid,))
        return render_template('dashboard_patient.html', stats=stats, recent=recent)

    elif role == 'Doctor':
        did = session.get('profileID')
        stats['today'] = query_db(
            """SELECT COUNT(*) AS c FROM Appointments
               WHERE doctorID=%s AND DATE(appointmentDate)=CURDATE() AND status='Scheduled'""",
            (did,), one=True)['c']
        stats['upcoming'] = query_db(
            """SELECT COUNT(*) AS c FROM Appointments
               WHERE doctorID=%s AND status='Scheduled'""",
            (did,), one=True)['c']
        stats['patients'] = query_db(
            """SELECT COUNT(DISTINCT patientID) AS c FROM Appointments WHERE doctorID=%s""",
            (did,), one=True)['c']

        recent = query_db(
            """SELECT a.appointmentID, a.appointmentDate, a.status, a.reason,
                      p.patientName
               FROM Appointments a JOIN Patients p ON a.patientID=p.patientID
               WHERE a.doctorID=%s ORDER BY a.appointmentDate DESC LIMIT 5""",
            (did,))
        return render_template('dashboard_doctor.html', stats=stats, recent=recent)

    elif role == 'Pharmacist':
        stats['medicines'] = query_db("SELECT COUNT(*) AS c FROM Medicines", one=True)['c']
        stats['prescriptions'] = query_db(
            "SELECT COUNT(*) AS c FROM Prescriptions", one=True)['c']
        stats['low_stock'] = query_db(
            "SELECT COUNT(*) AS c FROM Medicines WHERE stock < 20", one=True)['c']

        recent = query_db(
            """SELECT pr.prescriptionID, pr.quantity, pr.createdAt,
                      m.medicineName, p.patientName
               FROM Prescriptions pr
               JOIN Medicines m ON pr.medicineID=m.medicineID
               JOIN Appointments a ON pr.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               ORDER BY pr.createdAt DESC LIMIT 5""")
        return render_template('dashboard_pharmacist.html', stats=stats, recent=recent)

    else:  # Admin
        stats['doctors'] = query_db("SELECT COUNT(*) AS c FROM Doctors", one=True)['c']
        stats['patients'] = query_db("SELECT COUNT(*) AS c FROM Patients", one=True)['c']
        stats['appointments'] = query_db("SELECT COUNT(*) AS c FROM Appointments", one=True)['c']
        stats['revenue'] = query_db(
            "SELECT COALESCE(SUM(amount),0) AS c FROM Invoices WHERE paymentStatus='Paid'",
            one=True)['c']
        return render_template('dashboard_admin.html', stats=stats)

@app.route('/admin/add-doctor', methods=['GET', 'POST'])
@role_required('Admin')
def add_doctor():
    if request.method == 'POST':
        username   = request.form['username'].strip()
        password   = request.form['password']
        full_name  = request.form['full_name'].strip()
        email      = request.form['email'].strip()
        phone      = request.form['phone'].strip()
        spec       = request.form.get('specialization', 'General')
        fee        = request.form.get('consultationFee', '50') or '50'
        photo      = request.form.get('photo_url', '').strip()
        telegram   = request.form.get('telegram', '').strip()
        facebook   = request.form.get('facebook', '').strip()

        if len(username) < 5 or len(password) < 6:
            flash('Username must be 5+ chars and password 6+ chars.', 'danger')
            return redirect(url_for('add_doctor'))

        if spec not in VALID_SPECIALIZATIONS:
            spec = 'General'

        if query_db("SELECT userID FROM Users WHERE userName=%s OR email=%s",
                    (username, email), fetch=True, one=True):
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('add_doctor'))

        user_id = query_db(
            "INSERT INTO Users (userName, password, roles, email, phone) "
            "VALUES (%s,%s,'Doctor',%s,%s)",
            (username, generate_password_hash(password), email, phone))
        query_db(
            "INSERT INTO Doctors (doctorName, specialization, userID, email, phone, consultationFee, photo_url,telegram, facebook) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (full_name, spec, user_id, email, phone, fee, photo or None,telegram or None, facebook or None))

        flash(f'Doctor account for {full_name} created.', 'success')
        return redirect(url_for('doctors_list'))

    return render_template('add_doctor.html', specializations=VALID_SPECIALIZATIONS)


@app.route('/admin/add-pharmacist', methods=['GET', 'POST'])
@role_required('Admin')
def add_pharmacist():
    if request.method == 'POST':
        username  = request.form['username'].strip()
        password  = request.form['password']
        full_name = request.form['full_name'].strip()
        email     = request.form['email'].strip()
        phone     = request.form['phone'].strip()
        photo     = request.form.get('photo_url', '').strip()

        if len(username) < 5 or len(password) < 6:
            flash('Username must be 5+ chars and password 6+ chars.', 'danger')
            return redirect(url_for('add_pharmacist'))

        if query_db("SELECT userID FROM Users WHERE userName=%s OR email=%s",
                    (username, email), fetch=True, one=True):
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('add_pharmacist'))

        user_id = query_db(
            "INSERT INTO Users (userName, password, roles, email, phone) "
            "VALUES (%s,%s,'Pharmacist',%s,%s)",
            (username, generate_password_hash(password), email, phone))
        query_db(
            "INSERT INTO Pharmacists (pharmacistName, userID, email, phone, photo_url) "
            "VALUES (%s,%s,%s,%s,%s)",
            (full_name, user_id, email, phone, photo or None))

        flash(f'Pharmacist account for {full_name} created.', 'success')
        return redirect(url_for('doctors_list'))

    return render_template('add_pharmacist.html')
# -----------------------------------------------------
# Doctors listing (public-ish)
# -----------------------------------------------------
@app.route('/doctors')
def doctors_list():
    doctors = query_db(
        "SELECT doctorID, doctorName, specialization, consultationFee, email,photo_url,telegram,facebook FROM Doctors"
    )
    pharmacists = query_db(
        "SELECT pharmacistID, pharmacistName,email,phone,photo_url FROM Pharmacists ORDER BY pharmacistID")
    return render_template('doctors.html', doctors=doctors,pharmacists=pharmacists)


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
            (session['profileID'],))
    elif role == 'Doctor':
        rows = query_db(
            """SELECT a.*, p.patientName, d.doctorName, d.specialization
               FROM Appointments a
               JOIN Patients p ON a.patientID=p.patientID
               JOIN Doctors d ON a.doctorID=d.doctorID
               WHERE a.doctorID=%s ORDER BY a.appointmentDate DESC""",
            (session['profileID'],))
    else:
        rows = query_db(
            """SELECT a.*, p.patientName, d.doctorName, d.specialization
               FROM Appointments a
               JOIN Patients p ON a.patientID=p.patientID
               JOIN Doctors d ON a.doctorID=d.doctorID
               ORDER BY a.appointmentDate DESC""")
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
        
        # Block booking the SAME doctor on the SAME day
        existing = query_db(
            """SELECT appointmentID FROM Appointments
               WHERE patientID=%s AND doctorID=%s
               AND status='Scheduled'""",
            (session['profileID'], doctor_id),
            fetch=True, one=True)
        if existing:
            flash('You already have a scheduled appointment with this doctor. '
                  'Please wait until it is completed before booking again.', 'warning')
            return redirect(url_for('book_appointment'))

        try:
            appt_id = query_db(
                """INSERT INTO Appointments (patientID, doctorID, appointmentDate, reason, status)
                   VALUES (%s,%s,%s,%s,'Scheduled')""",
                (session['profileID'], doctor_id, appointment_date, reason)
            )

            fee_row = query_db("SELECT consultationFee FROM Doctors WHERE doctorID=%s",
                               (doctor_id,), one=True)
            fee = fee_row['consultationFee'] if fee_row else 50.00
            query_db(
                "INSERT INTO Invoices (appointmentID, amount, paymentStatus) VALUES (%s,%s,'Pending')",
                (appt_id, fee)
            )

            flash('Appointment booked successfully. Invoice issued.', 'success')
            return redirect(url_for('appointments'))
        except Exception as e:
            # Broad catch so non-MySQL errors are visible too; check the terminal.
            import traceback
            traceback.print_exc()
            flash(f'Error booking appointment: {e}', 'danger')
            return redirect(url_for('book_appointment'))

    doctors = query_db(
        "SELECT doctorID, doctorName, specialization, consultationFee FROM Doctors")
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
    rows = query_db("SELECT * FROM Medicines ORDER BY medicineName")
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
# Replace your OLD prescriptions() route with THIS version.
# It no longer joins on pr.medicineID (that old column isn't used now).
# Instead it counts the medicines from PrescriptionItems.

# Replace your OLD prescriptions() route with THIS version.
# It no longer joins on pr.medicineID (that old column isn't used now).
# Instead it counts the medicines from PrescriptionItems.

@app.route('/prescriptions')
@login_required
def prescriptions():
    role = session.get('role')
    if role == 'Patient':
        rows = query_db(
            """SELECT pr.prescriptionID, pr.diagnosis, pr.createdAt, pr.paymentStatus,
                      a.appointmentDate, d.doctorName,
                      COUNT(pi.itemID) AS medCount,
                      COALESCE(SUM(pi.quantity*m.price),0) AS total
               FROM Prescriptions pr
               JOIN Appointments a ON pr.appointmentID=a.appointmentID
               JOIN Doctors d ON a.doctorID=d.doctorID
               LEFT JOIN PrescriptionItems pi ON pi.prescriptionID=pr.prescriptionID
               LEFT JOIN Medicines m ON pi.medicineID=m.medicineID
               WHERE a.patientID=%s GROUP BY pr.prescriptionID
               ORDER BY pr.createdAt DESC""", (session['profileID'],))
    elif role == 'Doctor':
        rows = query_db(
            """SELECT pr.prescriptionID, pr.diagnosis, pr.createdAt, pr.paymentStatus,
                      a.appointmentDate, p.patientName,
                      COUNT(pi.itemID) AS medCount,
                      COALESCE(SUM(pi.quantity*m.price),0) AS total
               FROM Prescriptions pr
               JOIN Appointments a ON pr.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               LEFT JOIN PrescriptionItems pi ON pi.prescriptionID=pr.prescriptionID
               LEFT JOIN Medicines m ON pi.medicineID=m.medicineID
               WHERE a.doctorID=%s GROUP BY pr.prescriptionID
               ORDER BY pr.createdAt DESC""", (session['profileID'],))
    else:
        rows = query_db(
            """SELECT pr.prescriptionID, pr.diagnosis, pr.createdAt, pr.paymentStatus,
                      a.appointmentDate, p.patientName, d.doctorName,
                      COUNT(pi.itemID) AS medCount,
                      COALESCE(SUM(pi.quantity*m.price),0) AS total
               FROM Prescriptions pr
               JOIN Appointments a ON pr.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               JOIN Doctors d ON a.doctorID=d.doctorID
               LEFT JOIN PrescriptionItems pi ON pi.prescriptionID=pr.prescriptionID
               LEFT JOIN Medicines m ON pi.medicineID=m.medicineID
               GROUP BY pr.prescriptionID ORDER BY pr.createdAt DESC""")
    return render_template('prescriptions.html', prescriptions=rows)


# ---------------- DOCTOR: WRITE PRESCRIPTION ----------------
@app.route('/prescriptions/add', methods=['GET', 'POST'])
@role_required('Doctor')
def add_prescription():
    if request.method == 'POST':
        appointment_id = request.form['appointmentID']
        diagnosis      = request.form.get('diagnosis', '').strip()
        medicine_ids   = request.form.getlist('medicineID')
        quantities     = request.form.getlist('quantity')
        instructions   = request.form.getlist('instructions')

        if not medicine_ids:
            flash('Add at least one medicine.', 'danger')
            return redirect(url_for('add_prescription'))

        prescription_id = query_db(
            "INSERT INTO Prescriptions (appointmentID, diagnosis, paymentStatus) "
            "VALUES (%s,%s,'Unpaid')", (appointment_id, diagnosis))

        for i in range(len(medicine_ids)):
            mid = medicine_ids[i]
            qty = int(quantities[i]) if i < len(quantities) and quantities[i] else 1
            ins = instructions[i] if i < len(instructions) else ''
            if mid:
                query_db(
                    "INSERT INTO PrescriptionItems (prescriptionID, medicineID, quantity, instructions) "
                    "VALUES (%s,%s,%s,%s)", (prescription_id, mid, qty, ins))

        flash('Prescription created. Sent to pharmacy.', 'success')
        return redirect(url_for('prescriptions'))

    appts = query_db(
        """SELECT a.appointmentID, a.appointmentDate, p.patientName
           FROM Appointments a JOIN Patients p ON a.patientID=p.patientID
           WHERE a.doctorID=%s AND a.status IN ('Scheduled','Completed')
           ORDER BY a.appointmentDate DESC""", (session['profileID'],))
    meds = query_db("SELECT medicineID, medicineName, price FROM Medicines ORDER BY medicineName")
    return render_template('add_prescription.html', appointments=appts, medicines=meds)


# ---------------- HELPER: prescription detail ----------------
def get_prescription_detail(prescription_id):
    pres = query_db(
        """SELECT pr.*, a.appointmentDate, a.patientID, p.patientName, d.doctorName
           FROM Prescriptions pr
           JOIN Appointments a ON pr.appointmentID=a.appointmentID
           JOIN Patients p ON a.patientID=p.patientID
           JOIN Doctors d ON a.doctorID=d.doctorID
           WHERE pr.prescriptionID=%s""", (prescription_id,), fetch=True, one=True)
    items = query_db(
        """SELECT pi.quantity, pi.instructions, m.medicineName, m.price,
                  (pi.quantity*m.price) AS lineTotal
           FROM PrescriptionItems pi JOIN Medicines m ON pi.medicineID=m.medicineID
           WHERE pi.prescriptionID=%s""", (prescription_id,))
    total = sum(float(it['lineTotal']) for it in items) if items else 0.0
    return pres, items, total


@app.route('/patient_pay/<int:pid>', methods=['GET', 'POST'])
@role_required('Patient')
def patient_pay(pid):
    pres, items, total = get_prescription_detail(pid)
    if not pres:
        flash('Prescription not found.', 'danger')
        return redirect(url_for('prescriptions'))
    if pres['patientID'] != session.get('profileID'):
        flash('You do not have permission to view this prescription.', 'danger')
        return redirect(url_for('prescriptions'))

    if request.method == 'POST':
        if pres['paymentStatus'] == 'Paid':
            flash('This prescription is already paid.', 'info')
            return redirect(url_for('patient_pay', pid=pid))
        query_db(
            "UPDATE Prescriptions SET paymentStatus='Paid', paymentMethod='QR', paidAt=NOW() WHERE prescriptionID=%s",
            (pid,))
        flash('Payment confirmed. Please collect your medicine at the pharmacy.', 'success')
        return redirect(url_for('patient_pay', pid=pid))

    payee_account = "001 234 567"
    payee_name = "Dermacare Clinic"
    return render_template('patient_pay.html', pres=pres, items=items, total=total,
                           payee_account=payee_account, payee_name=payee_name)


# ---------------- PRINTABLE PRESCRIPTION ----------------
@app.route('/prescriptions/<int:pid>/print')
@login_required
def print_prescription(pid):
    pres, items, total = get_prescription_detail(pid)
    if not pres:
        flash('Prescription not found.', 'danger')
        return redirect(url_for('prescriptions'))
    return render_template('prescription_print.html', pres=pres, items=items, total=total)


# ---------------- PHARMACIST: QUEUE ----------------
@app.route('/pharmacy')
@role_required('Pharmacist', 'Admin')
def pharmacy_queue():
    rows = query_db(
        """SELECT pr.prescriptionID, pr.diagnosis, pr.paymentStatus, pr.createdAt,
                  pr.dispensed, p.patientName, d.doctorName,
                  COALESCE(SUM(pi.quantity*m.price),0) AS total
           FROM Prescriptions pr
           JOIN Appointments a ON pr.appointmentID=a.appointmentID
           JOIN Patients p ON a.patientID=p.patientID
           JOIN Doctors d ON a.doctorID=d.doctorID
           LEFT JOIN PrescriptionItems pi ON pi.prescriptionID=pr.prescriptionID
           LEFT JOIN Medicines m ON pi.medicineID=m.medicineID
           GROUP BY pr.prescriptionID ORDER BY pr.createdAt DESC""")
    return render_template('pharmacy_queue.html', prescriptions=rows)


# ---------------- PHARMACIST: DETAIL + PAYMENT ----------------
@app.route('/pharmacy/<int:pid>')
@role_required('Pharmacist', 'Admin')
def pharmacy_detail(pid):
    pres, items, total = get_prescription_detail(pid)
    if not pres:
        flash('Prescription not found.', 'danger')
        return redirect(url_for('pharmacy_queue'))
    payee_account = "001 234 567"          # <-- your ABA account to display
    payee_name    = "Dermacare Clinic"
    return render_template('pharmacy_detail.html', pres=pres, items=items, total=total,
                           payee_account=payee_account, payee_name=payee_name)


@app.route('/pharmacy/<int:pid>/pay/<method>')
@role_required('Pharmacist', 'Admin')
def pharmacy_pay(pid, method):
    if method not in ('Cash', 'QR'):
        flash('Invalid payment method.', 'danger')
        return redirect(url_for('pharmacy_detail', pid=pid))
    query_db("UPDATE Prescriptions SET paymentStatus='Paid', paymentMethod=%s, "
             "paidAt=NOW(), pharmacistID=%s WHERE prescriptionID=%s",
             (method, session.get('profileID'), pid))
    flash(f'Payment received ({method}). Marked as paid.', 'success')
    return redirect(url_for('pharmacy_detail', pid=pid))


# ---------------- PHARMACIST: DISPENSE (reduce stock) ----------------
@app.route('/pharmacy/<int:pid>/dispense')
@role_required('Pharmacist', 'Admin')
def pharmacy_dispense(pid):
    pres, items, total = get_prescription_detail(pid)
    if not pres:
        flash('Prescription not found.', 'danger')
        return redirect(url_for('pharmacy_queue'))
    if pres['paymentStatus'] != 'Paid':
        flash('Cannot dispense before payment is received.', 'warning')
        return redirect(url_for('pharmacy_detail', pid=pid))
    if pres['dispensed']:
        flash('Already dispensed.', 'info')
        return redirect(url_for('pharmacy_detail', pid=pid))

    item_rows = query_db(
        "SELECT pi.medicineID, pi.quantity, m.medicineName, m.stock "
        "FROM PrescriptionItems pi JOIN Medicines m ON pi.medicineID=m.medicineID "
        "WHERE pi.prescriptionID=%s", (pid,))
    for it in item_rows:
        if it['stock'] < it['quantity']:
            flash(f"Not enough stock for {it['medicineName']} "
                  f"(need {it['quantity']}, have {it['stock']}).", 'danger')
            return redirect(url_for('pharmacy_detail', pid=pid))
    for it in item_rows:
        query_db("UPDATE Medicines SET stock=stock-%s WHERE medicineID=%s",
                 (it['quantity'], it['medicineID']))
    query_db("UPDATE Prescriptions SET dispensed=1, dispensedAt=NOW() WHERE prescriptionID=%s", (pid,))
    flash('Medication dispensed. Inventory updated.', 'success')
    return redirect(url_for('pharmacy_detail', pid=pid))


# ---------------- DOCTOR: PATIENT HISTORY ----------------
@app.route('/patients/<int:patient_id>/history')
@role_required('Doctor', 'Admin')
def patient_history(patient_id):
    patient = query_db("SELECT * FROM Patients WHERE patientID=%s",
                       (patient_id,), fetch=True, one=True)
    if not patient:
        flash('Patient not found.', 'danger')
        return redirect(url_for('appointments'))
    appts = query_db(
        """SELECT a.appointmentDate, a.reason, a.status, d.doctorName, d.specialization
           FROM Appointments a JOIN Doctors d ON a.doctorID=d.doctorID
           WHERE a.patientID=%s ORDER BY a.appointmentDate DESC""", (patient_id,))
    pres = query_db(
        """SELECT pr.prescriptionID, pr.diagnosis, pr.createdAt, pr.paymentStatus,
                  d.doctorName
           FROM Prescriptions pr
           JOIN Appointments a ON pr.appointmentID=a.appointmentID
           JOIN Doctors d ON a.doctorID=d.doctorID
           WHERE a.patientID=%s ORDER BY pr.createdAt DESC""", (patient_id,))
    return render_template('patient_history.html', patient=patient,
                           appointments=appts, prescriptions=pres)


# ---------------- PATIENT: CHECK IN ----------------
@app.route('/appointments/<int:aid>/checkin')
@role_required('Patient')
def appointment_checkin(aid):
    appt = query_db("SELECT * FROM Appointments WHERE appointmentID=%s AND patientID=%s",
                    (aid, session['profileID']), fetch=True, one=True)
    if not appt:
        flash('Appointment not found.', 'danger')
        return redirect(url_for('appointments'))
    if appt['status'] != 'Scheduled':
        flash('Only scheduled appointments can be checked in.', 'warning')
        return redirect(url_for('appointments'))
    query_db("UPDATE Appointments SET checkedIn=1, checkedInAt=NOW() WHERE appointmentID=%s", (aid,))
    flash('Checked in. Please wait to be called.', 'success')
    return redirect(url_for('appointments'))


# ---------------- PATIENT/ANYONE: EDIT PROFILE ----------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = query_db("SELECT * FROM Users WHERE userID=%s", (session['userID'],), fetch=True, one=True)
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        query_db("UPDATE Users SET email=%s, phone=%s WHERE userID=%s",
                 (email, phone, session['userID']))
        if session.get('role') == 'Patient':
            full_name = request.form.get('full_name', '').strip()
            query_db("UPDATE Patients SET patientName=%s, email=%s, phone=%s WHERE userID=%s",
                     (full_name, email, phone, session['userID']))
        flash('Profile updated.', 'success')
        return redirect(url_for('edit_profile'))
    profile = None
    if session.get('role') == 'Patient':
        profile = query_db("SELECT * FROM Patients WHERE userID=%s",
                           (session['userID'],), fetch=True, one=True)
    return render_template('edit_profile.html', user=user, profile=profile)

 
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
            (session['profileID'],))
    elif role == 'Doctor':
        rows = query_db(
            """SELECT i.*, a.appointmentDate, p.patientName
               FROM Invoices i
               JOIN Appointments a ON i.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               WHERE a.doctorID=%s ORDER BY i.issuedAt DESC""",
            (session['profileID'],))
    else:
        rows = query_db(
            """SELECT i.*, a.appointmentDate, p.patientName, d.doctorName
               FROM Invoices i
               JOIN Appointments a ON i.appointmentID=a.appointmentID
               JOIN Patients p ON a.patientID=p.patientID
               JOIN Doctors d ON a.doctorID=d.doctorID
               ORDER BY i.issuedAt DESC""")
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
        " FROM Messages ORDER BY createdAt DESC"
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