import sys
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'Hong9090$',
    'database': 'clinic',
    'port': 3306,
}


def main():
    
    username = sys.argv[1] if len(sys.argv) > 1 else 'Honglyly'
    password = sys.argv[2] if len(sys.argv) > 2 else 'Hong9090$'
    email = 'hong@clinic.com'
    phone = '095535582'

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)

        
        cur.execute("SELECT userID FROM Users WHERE userName=%s", (username,))
        if cur.fetchone():
            print(f"⚠️  A user named '{username}' already exists. Nothing changed.")
            return

        hashed = generate_password_hash(password)
        cur.execute(
            "INSERT INTO Users (userName, password, roles, email, phone) "
            "VALUES (%s,%s,%s,%s,%s)",
            (username, hashed, 'Admin', email, phone)
        )
        conn.commit()

        print("✅ Admin created successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print("   (Change this password after your first login.)")

    except Error as e:
        print(f"❌ Database error: {e}")
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()