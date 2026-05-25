

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "Hong9090$",
    "database": "clinic",
    "port": 3306,
    "use_pure": True,
}

DEFAULT_PASSWORD = "staff123"

SPECIALIZATIONS = ["General", "Dermatology", "Cosmetic", "Pediatrics", "Cardiology"]

DOCTORS = [
    ("Dr. Alice Brown",    "General"),
    ("Dr. Bopha Chan",     "Dermatology"),
    ("Dr. Charles Davis",  "Cosmetic"),
    ("Dr. Dara Heng",      "Pediatrics"),
    ("Dr. Emily Foster",   "Cardiology"),
    ("Dr. Frank Green",    "General"),
    ("Dr. Grace Kim",      "Dermatology"),
    ("Dr. Henry Lee",      "Cosmetic"),
    ("Dr. Iris Nguyen",    "Pediatrics"),
    ("Dr. Jacob Oh",       "Cardiology"),
]

PHARMACISTS = [
    "Tom Wilson",
    "Sophea Vann",
    "Nina Patel",
    "Oscar Reyes",
]


def create_user(cur, username, role, email, phone):
    """Insert a Users row with a hashed password; return the new userID."""
    cur.execute(
        "INSERT INTO Users (userName, password, roles, email, phone) "
        "VALUES (%s, %s, %s, %s, %s)",
        (username, generate_password_hash(DEFAULT_PASSWORD), role, email, phone),
    )
    return cur.lastrowid


def main():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()

        created_doctors = 0
        created_pharmacists = 0
        for i, (full_name, spec) in enumerate(DOCTORS, start=1):
            username = f"doctor{i:02d}"         
            email = f"doctor{i:02d}@clinic.com"
            phone = f"01000000{i:02d}"           

            cur.execute(
                "SELECT userID FROM Users WHERE userName = %s OR email = %s",
                (username, email),
            )
            if cur.fetchone():
                print(f"skip doctor: {username} already exists")
                continue

            uid = create_user(cur, username, "Doctor", email, phone)
            fee = 50.00 + (i * 5)                 # varied fees
            cur.execute(
                "INSERT INTO Doctors "
                "(doctorName, specialization, userID, email, phone, consultationFee) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (full_name, spec, uid, email, phone, fee),
            )
            created_doctors += 1

        # ---- Pharmacists ---------------------------------------------
        for i, full_name in enumerate(PHARMACISTS, start=1):
            username = f"pharma{i:02d}"           # pharma01 ... pharma10
            email = f"pharma{i:02d}@clinic.com"
            phone = f"02000000{i:02d}"

            cur.execute(
                "SELECT userID FROM Users WHERE userName = %s OR email = %s",
                (username, email),
            )
            if cur.fetchone():
                print(f"skip pharmacist: {username} already exists")
                continue

            uid = create_user(cur, username, "Pharmacist", email, phone)
            cur.execute(
                "INSERT INTO Pharmacists (pharmacistName, userID, email, phone) "
                "VALUES (%s, %s, %s, %s)",
                (full_name, uid, email, phone),
            )
            created_pharmacists += 1

        conn.commit()
        print(f"✅ Created {created_doctors} doctors and "
              f"{created_pharmacists} pharmacists.")
        print(f"   Login with username doctor01..doctor10 / pharma01..pharma4")
        print(f"   Password for all: {DEFAULT_PASSWORD}")

    except Error as e:
        print(f"❌ Database error: {e}")
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()