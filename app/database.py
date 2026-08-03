import sqlite3

DATABASE_PATH = "database/invoiceflow.db"

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    return connection

def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company (
            id INTEGER PRIMARY KEY,
            business_name TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            province TEXT NOT NULL,
            postal_code TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            logo_path TEXT,
            bank_name TEXT NOT NULL,
            account_holder TEXT NOT NULL,
            account_number TEXT NOT NULL,
            branch_code TEXT NOT NULL,
            account_type TEXT NOT NULL,
            reference_prefix TEXT,
            signature_path TEXT
        )
    """)

    connection.commit()
    connection.close()

def save_company_info(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO company (
            id, business_name, owner_name, address, city, province,
            postal_code, phone, email, logo_path, bank_name,
            account_holder, account_number, branch_code, account_type,
            reference_prefix, signature_path
        )
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["business_name"], data["owner_name"], data["address"],
        data["city"], data["province"], data["postal_code"],
        data["phone"], data["email"], data["logo_path"],
        data["bank_name"], data["account_holder"], data["account_number"],
        data["branch_code"], data["account_type"],
        data["reference_prefix"], data["signature_path"]
    ))

    connection.commit()
    connection.close()

def get_company_info():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM company WHERE id = 1")
    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    company = {
        "id": row[0],
        "business_name": row[1],
        "owner_name": row[2],
        "address": row[3],
        "city": row[4],
        "province": row[5],
        "postal_code": row[6],
        "phone": row[7],
        "email": row[8],
        "logo_path": row[9],
        "bank_name": row[10],
        "account_holder": row[11],
        "account_number": row[12],
        "branch_code": row[13],
        "account_type": row[14],
        "reference_prefix": row[15],
        "signature_path": row[16]
    }

    return company

if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully.")