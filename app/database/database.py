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

    return {
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


def update_company_info(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE company SET
            business_name = ?, owner_name = ?, address = ?, city = ?,
            province = ?, postal_code = ?, phone = ?, email = ?,
            logo_path = ?, bank_name = ?, account_holder = ?,
            account_number = ?, branch_code = ?, account_type = ?,
            reference_prefix = ?, signature_path = ?
        WHERE id = 1
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


def create_customers_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            business_name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            province TEXT,
            postal_code TEXT,
            notes TEXT
        )
    """)

    connection.commit()
    connection.close()


def add_customer(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO customers (
            customer_name, business_name, phone, email,
            address, city, province, postal_code, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["customer_name"], data["business_name"], data["phone"],
        data["email"], data["address"], data["city"],
        data["province"], data["postal_code"], data["notes"]
    ))

    connection.commit()
    connection.close()


def get_all_customers():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM customers ORDER BY customer_name ASC")
    rows = cursor.fetchall()

    connection.close()

    customers = []
    for row in rows:
        customers.append({
            "id": row[0],
            "customer_name": row[1],
            "business_name": row[2],
            "phone": row[3],
            "email": row[4],
            "address": row[5],
            "city": row[6],
            "province": row[7],
            "postal_code": row[8],
            "notes": row[9]
        })

    return customers


def update_customer(customer_id, data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE customers SET
            customer_name = ?, business_name = ?, phone = ?, email = ?,
            address = ?, city = ?, province = ?, postal_code = ?, notes = ?
        WHERE id = ?
    """, (
        data["customer_name"], data["business_name"], data["phone"],
        data["email"], data["address"], data["city"],
        data["province"], data["postal_code"], data["notes"], customer_id
    ))

    connection.commit()
    connection.close()


def delete_customer(customer_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))

    connection.commit()
    connection.close()


def search_customers(keyword):
    connection = get_connection()
    cursor = connection.cursor()

    search_term = f"%{keyword}%"
    cursor.execute("""
        SELECT * FROM customers
        WHERE customer_name LIKE ? OR business_name LIKE ? OR phone LIKE ? OR email LIKE ?
        ORDER BY customer_name ASC
    """, (search_term, search_term, search_term, search_term))

    rows = cursor.fetchall()
    connection.close()

    customers = []
    for row in rows:
        customers.append({
            "id": row[0],
            "customer_name": row[1],
            "business_name": row[2],
            "phone": row[3],
            "email": row[4],
            "address": row[5],
            "city": row[6],
            "province": row[7],
            "postal_code": row[8],
            "notes": row[9]
        })

    return customers


def create_invoices_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            invoice_date TEXT NOT NULL,
            invoice_time TEXT NOT NULL,
            subtotal REAL NOT NULL,
            vat REAL NOT NULL,
            total REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    """)

    connection.commit()
    connection.close()


def create_invoice_items_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        )
    """)

    connection.commit()
    connection.close()


def get_next_invoice_number():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM invoices")
    count = cursor.fetchone()[0]

    connection.close()

    return count + 1


def add_invoice(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO invoices (
            invoice_number, customer_id, invoice_date, invoice_time,
            subtotal, vat, total, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["invoice_number"], data["customer_id"], data["invoice_date"],
        data["invoice_time"], data["subtotal"], data["vat"], data["total"],
        data.get("notes", "")
    ))

    invoice_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return invoice_id


def add_invoice_item(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO invoice_items (
            invoice_id, description, quantity, unit_price, line_total
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        data["invoice_id"], data["description"], data["quantity"],
        data["unit_price"], data["line_total"]
    ))

    connection.commit()
    connection.close()


def get_all_invoices():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT invoices.id, invoices.invoice_number, customers.customer_name,
               invoices.invoice_date, invoices.total
        FROM invoices
        JOIN customers ON invoices.customer_id = customers.id
        ORDER BY invoices.id DESC
    """)
    rows = cursor.fetchall()
    connection.close()

    invoices = []
    for row in rows:
        invoices.append({
            "id": row[0],
            "invoice_number": row[1],
            "customer_name": row[2],
            "invoice_date": row[3],
            "total": row[4]
        })

    return invoices


def get_invoice_by_id(invoice_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    row = cursor.fetchone()

    if row is None:
        connection.close()
        return None

    invoice = {
        "id": row[0],
        "invoice_number": row[1],
        "customer_id": row[2],
        "invoice_date": row[3],
        "invoice_time": row[4],
        "subtotal": row[5],
        "vat": row[6],
        "total": row[7],
        "notes": row[8]
    }

    cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    item_rows = cursor.fetchall()
    connection.close()

    items = []
    for item_row in item_rows:
        items.append({
            "id": item_row[0],
            "invoice_id": item_row[1],
            "description": item_row[2],
            "quantity": item_row[3],
            "unit_price": item_row[4],
            "line_total": item_row[5]
        })

    invoice["items"] = items
    return invoice


def delete_invoice(invoice_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))

    connection.commit()
    connection.close()


def search_invoices(keyword):
    connection = get_connection()
    cursor = connection.cursor()

    search_term = f"%{keyword}%"
    cursor.execute("""
        SELECT invoices.id, invoices.invoice_number, customers.customer_name,
               invoices.invoice_date, invoices.total
        FROM invoices
        JOIN customers ON invoices.customer_id = customers.id
        WHERE invoices.invoice_number LIKE ? OR customers.customer_name LIKE ?
           OR invoices.invoice_date LIKE ?
        ORDER BY invoices.id DESC
    """, (search_term, search_term, search_term))

    rows = cursor.fetchall()
    connection.close()

    invoices = []
    for row in rows:
        invoices.append({
            "id": row[0],
            "invoice_number": row[1],
            "customer_name": row[2],
            "invoice_date": row[3],
            "total": row[4]
        })

    return invoices


if __name__ == "__main__":
    create_tables()
    create_customers_table()
    create_invoices_table()
    create_invoice_items_table()
    print("Database and tables created successfully.")