import sqlite3
from datetime import date, timedelta

DATABASE_PATH = "database/invoiceflow.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
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
    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            "SELECT COUNT(*) FROM invoices WHERE customer_id = ?",
            (customer_id,)
        )
        if cursor.fetchone()[0]:
            raise CustomerHasInvoicesError(
                "This customer cannot be deleted because invoices are linked "
                "to their account."
            )

        cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        connection.commit()
    except sqlite3.IntegrityError as error:
        connection.rollback()
        raise CustomerHasInvoicesError(
            "This customer cannot be deleted because invoices are linked "
            "to their account."
        ) from error
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


class CustomerHasInvoicesError(ValueError):
    """Raised when a customer with linked invoices is deleted."""


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

def get_customer_by_id(customer_id):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return {
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
    }


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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_number_sequences (
            invoice_year INTEGER PRIMARY KEY,
            last_number INTEGER NOT NULL
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


def _next_invoice_sequence(cursor, invoice_year):
    prefix = f"INV-{invoice_year}-"
    cursor.execute(
        "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ?",
        (f"{prefix}%",)
    )
    highest_existing = 0
    for (invoice_number,) in cursor.fetchall():
        suffix = invoice_number[len(prefix):]
        if suffix.isdigit():
            highest_existing = max(highest_existing, int(suffix))

    cursor.execute(
        "SELECT last_number FROM invoice_number_sequences WHERE invoice_year = ?",
        (invoice_year,)
    )
    sequence_row = cursor.fetchone()
    last_number = max(
        highest_existing,
        sequence_row[0] if sequence_row else 0
    )
    next_number = last_number + 1

    cursor.execute("""
        INSERT INTO invoice_number_sequences (invoice_year, last_number)
        VALUES (?, ?)
        ON CONFLICT(invoice_year) DO UPDATE SET last_number = excluded.last_number
    """, (invoice_year, next_number))
    return next_number


def get_next_invoice_number(invoice_year=None):
    connection = get_connection()
    cursor = connection.cursor()
    year = invoice_year if invoice_year is not None else date.today().year
    try:
        cursor.execute(
            "SELECT last_number FROM invoice_number_sequences WHERE invoice_year = ?",
            (year,)
        )
        sequence_row = cursor.fetchone()
        cursor.execute(
            "SELECT invoice_number FROM invoices WHERE invoice_number LIKE ?",
            (f"INV-{year}-%",)
        )
        prefix = f"INV-{year}-"
        existing_numbers = [
            int(number[len(prefix):])
            for (number,) in cursor.fetchall()
            if number[len(prefix):].isdigit()
        ]
        last_number = max(
            [sequence_row[0] if sequence_row else 0, *existing_numbers]
        )
        return last_number + 1
    finally:
        connection.close()


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


def create_invoice_with_items(data, items):
    """Atomically assign a year-based invoice number and save its items."""
    invoice_date = date.fromisoformat(data["invoice_date"])
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_number_sequences (
                invoice_year INTEGER PRIMARY KEY,
                last_number INTEGER NOT NULL
            )
        """)
        sequence = _next_invoice_sequence(cursor, invoice_date.year)
        invoice_number = f"INV-{invoice_date.year}-{sequence:05d}"
        cursor.execute("""
            INSERT INTO invoices (
                invoice_number, customer_id, invoice_date, invoice_time,
                subtotal, vat, total, notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_number, data["customer_id"], data["invoice_date"],
            data["invoice_time"], data["subtotal"], data["vat"],
            data["total"], data.get("notes", "")
        ))
        invoice_id = cursor.lastrowid

        cursor.executemany("""
            INSERT INTO invoice_items (
                invoice_id, description, quantity, unit_price, line_total
            )
            VALUES (?, ?, ?, ?, ?)
        """, [
            (
                invoice_id, item["description"], item["quantity"],
                item["unit_price"], item["line_total"]
            )
            for item in items
        ])
        connection.commit()
        return invoice_id
    except Exception:
        connection.rollback()
        raise
    finally:
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
# =====================================================
# REPORT FUNCTIONS
# Used by the Dashboard and Reports screen
# =====================================================

def get_business_statistics(reference_date=None):
    """Return invoiced-revenue statistics based on ISO invoice dates."""
    today = reference_date or date.today()
    month_start = today.replace(day=1)
    previous_month_end = month_start
    previous_month_start = (month_start - timedelta(days=1)).replace(day=1)
    year_start = date(today.year, 1, 1)
    year_to_date_end = today + timedelta(days=1)
    if month_start.month == 12:
        next_month_start = date(month_start.year + 1, 1, 1)
    else:
        next_month_start = date(month_start.year, month_start.month + 1, 1)

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT
                COALESCE(SUM(CASE
                    WHEN invoice_date >= ? AND invoice_date < ? THEN total
                    ELSE 0
                END), 0),
                COALESCE(SUM(CASE
                    WHEN invoice_date >= ? AND invoice_date < ? THEN total
                    ELSE 0
                END), 0),
                COALESCE(SUM(CASE
                    WHEN invoice_date >= ? AND invoice_date < ? THEN total
                    ELSE 0
                END), 0),
                COUNT(*),
                COALESCE(AVG(total), 0)
            FROM invoices
            WHERE length(invoice_date) = 10
        """, (
            month_start.isoformat(), next_month_start.isoformat(),
            previous_month_start.isoformat(), previous_month_end.isoformat(),
            year_start.isoformat(), year_to_date_end.isoformat()
        ))
        current, previous, year_to_date, invoice_count, average = cursor.fetchone()

        percentage_change = None
        if previous:
            percentage_change = (current - previous) / previous * 100

        cursor.execute("""
            SELECT substr(invoice_date, 1, 7) AS month, SUM(total) AS revenue
            FROM invoices
            WHERE length(invoice_date) = 10
            GROUP BY month
            ORDER BY month
        """)
        monthly_revenue = [
            {"month": row[0], "revenue": row[1]}
            for row in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT customers.id, customers.customer_name, SUM(invoices.total) AS revenue
            FROM invoices
            JOIN customers ON customers.id = invoices.customer_id
            GROUP BY customers.id, customers.customer_name
            ORDER BY revenue DESC, customers.customer_name COLLATE NOCASE
            LIMIT 5
        """)
        best_customers = [
            {
                "customer_id": row[0],
                "customer_name": row[1],
                "revenue": row[2]
            }
            for row in cursor.fetchall()
        ]

        return {
            "current_month_revenue": current,
            "previous_month_revenue": previous,
            "percentage_change": percentage_change,
            "year_to_date_revenue": year_to_date,
            "total_invoices": invoice_count,
            "average_invoice_value": average,
            "monthly_revenue": monthly_revenue,
            "best_customers": best_customers
        }
    finally:
        connection.close()


def get_total_revenue():
    connection = get_connection()
    try:
        result = connection.execute("SELECT COALESCE(SUM(total), 0) FROM invoices")
        return result.fetchone()[0]
    finally:
        connection.close()


def get_total_customers():
    """
    Returns the number of customers.
    """

    connection = get_connection()
    try:
        return connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    finally:
        connection.close()


def get_total_invoices():
    """
    Returns the number of invoices.
    """

    connection = get_connection()
    try:
        return connection.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
    finally:
        connection.close()


def get_monthly_revenue():
    """
    Returns revenue grouped by month.

    Example:

    January 2026  -> R1500
    February 2026 -> R3200
    """

    return get_business_statistics()["monthly_revenue"]


def get_recent_invoices(limit=10):
    """
    Returns the latest invoices.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            invoice_number,
            invoice_date,
            total
        FROM invoices
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    connection.close()

    invoices = []

    for row in rows:

        invoices.append({
            "invoice_number": row[0],
            "invoice_date": row[1],
            "total": row[2]
        })

    return invoices

if __name__ == "__main__":
    create_tables()
    create_customers_table()
    create_invoices_table()
    create_invoice_items_table()
    print("Database and tables created successfully.")