import json
import math
import sqlite3
from datetime import date, timedelta

DATABASE_PATH = "database/invoiceflow.db"
UIF_MONTHLY_GROSS_CEILING = 17712.0
EMPLOYEE_IDENTIFICATION_TYPES = ("SA ID", "Passport")
DEFAULT_EXPENSE_CATEGORIES = (
    "Wages",
    "Car",
    "Petrol",
    "Maintenance",
    "Rent",
    "Stock/Supplies",
    "Phone & Data",
    "Other",
)


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
            due_date TEXT,
            pdf_path TEXT,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    """)

    cursor.execute("PRAGMA table_info(invoices)")
    invoice_columns = {row[1] for row in cursor.fetchall()}
    for column in ("due_date", "pdf_path"):
        if column not in invoice_columns:
            cursor.execute(f"ALTER TABLE invoices ADD COLUMN {column} TEXT")

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


def create_payments_table():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        )
    """)
    connection.commit()
    connection.close()


def create_budget_tables():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            UNIQUE(month, category)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT UNIQUE NOT NULL
        )
    """)
    cursor.executemany(
        "INSERT OR IGNORE INTO expense_categories (category) VALUES (?)",
        [(category,) for category in DEFAULT_EXPENSE_CATEGORIES],
    )
    connection.commit()
    connection.close()


def create_employee_tables():
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            cell_number TEXT NOT NULL,
            sa_id_number TEXT NOT NULL,
            identification_type TEXT NOT NULL DEFAULT 'SA ID',
            start_date TEXT NOT NULL,
            id_copy_path TEXT,
            contract_path TEXT,
            hourly_rate REAL NOT NULL DEFAULT 0
        )
    """)
    cursor.execute("PRAGMA table_info(employees)")
    employee_columns = {row[1] for row in cursor.fetchall()}
    for column, definition in (
        ("employee_id", "TEXT"),
        ("id_copy_path", "TEXT"),
        ("contract_path", "TEXT"),
        ("hourly_rate", "REAL NOT NULL DEFAULT 0"),
        ("identification_type", "TEXT NOT NULL DEFAULT 'SA ID'"),
    ):
        if column not in employee_columns:
            cursor.execute(f"ALTER TABLE employees ADD COLUMN {column} {definition}")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS salary_advances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            advance_date TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_pay_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            hours_json TEXT NOT NULL,
            hourly_rate REAL NOT NULL,
            gross_override REAL,
            gross_pay REAL NOT NULL,
            employee_uif REAL NOT NULL,
            employer_uif REAL NOT NULL,
            paye REAL NOT NULL DEFAULT 0,
            advance_deducted REAL NOT NULL DEFAULT 0,
            pay_date TEXT NOT NULL,
            UNIQUE(employee_id, month),
            FOREIGN KEY(employee_id) REFERENCES employees(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_id_sequence (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            last_number INTEGER NOT NULL
        )
    """)
    cursor.execute("PRAGMA table_info(employee_pay_records)")
    pay_columns = {row[1] for row in cursor.fetchall()}
    for column, definition in (
        ("gross_override", "REAL"),
        ("employee_uif", "REAL NOT NULL DEFAULT 0"),
        ("employer_uif", "REAL NOT NULL DEFAULT 0"),
        ("paye", "REAL NOT NULL DEFAULT 0"),
        ("advance_deducted", "REAL NOT NULL DEFAULT 0"),
        ("pay_date", "TEXT NOT NULL DEFAULT ''"),
    ):
        if column not in pay_columns:
            cursor.execute(
                f"ALTER TABLE employee_pay_records ADD COLUMN {column} {definition}"
            )
    cursor.execute("""
        SELECT COALESCE(MAX(CAST(substr(employee_id, 5) AS INTEGER)), 0)
        FROM employees WHERE employee_id LIKE 'EMP-%'
    """)
    next_employee_number = cursor.fetchone()[0]
    cursor.execute("""
        SELECT id FROM employees WHERE employee_id IS NULL OR employee_id = ''
        ORDER BY id
    """)
    for (employee_row_id,) in cursor.fetchall():
        next_employee_number += 1
        cursor.execute(
            "UPDATE employees SET employee_id = ? WHERE id = ?",
            (f"EMP-{next_employee_number:03d}", employee_row_id),
        )
    cursor.execute("""
        SELECT COALESCE(MAX(CAST(substr(employee_id, 5) AS INTEGER)), 0)
        FROM employees WHERE employee_id LIKE 'EMP-%'
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO employee_id_sequence (id, last_number) VALUES (1, ?)",
        (cursor.fetchone()[0],),
    )
    connection.commit()
    connection.close()


def _validate_employee_data(
    name, surname, cell_number, sa_id_number, start_date,
    identification_type="SA ID",
):
    if not name.strip() or not surname.strip():
        raise ValueError("Employee name and surname are required.")
    if not cell_number.strip():
        raise ValueError("Cell number is required.")
    if identification_type not in EMPLOYEE_IDENTIFICATION_TYPES:
        raise ValueError("Choose SA ID or Passport as the identification type.")
    if identification_type == "SA ID" and (
        not sa_id_number.isdigit() or len(sa_id_number) != 13
    ):
        raise ValueError("South African ID number must contain 13 digits.")
    if identification_type == "Passport" and not sa_id_number.strip():
        raise ValueError("Passport number is required.")
    parsed_date = date.fromisoformat(start_date)
    if parsed_date.isoformat() != start_date:
        raise ValueError("Start date must use YYYY-MM-DD format.")


def add_employee(
    name, surname, cell_number, sa_id_number, start_date,
    identification_type="SA ID",
):
    _validate_employee_data(
        name, surname, cell_number, sa_id_number, start_date, identification_type
    )
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute(
            "UPDATE employee_id_sequence SET last_number = last_number + 1 WHERE id = 1"
        )
        cursor.execute(
            "SELECT last_number FROM employee_id_sequence WHERE id = 1"
        )
        next_number = cursor.fetchone()[0]
        employee_number = f"EMP-{next_number:03d}"
        cursor.execute("""
            INSERT INTO employees (
                employee_id, name, surname, cell_number, sa_id_number,
                identification_type, start_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_number, name.strip(), surname.strip(), cell_number.strip(),
            sa_id_number.strip(), identification_type, start_date,
        ))
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_all_employees():
    connection = get_connection()
    try:
        rows = connection.execute("""
            SELECT id, employee_id, name, surname, cell_number, sa_id_number,
                   identification_type, start_date, id_copy_path, contract_path,
                   hourly_rate
            FROM employees
            ORDER BY surname COLLATE NOCASE, name COLLATE NOCASE
        """).fetchall()
        return [
            {
                "id": row[0], "employee_id": row[1], "name": row[2],
                "surname": row[3], "cell_number": row[4], "sa_id_number": row[5],
                "identification_type": row[6], "start_date": row[7],
                "id_copy_path": row[8], "contract_path": row[9],
                "hourly_rate": row[10],
            }
            for row in rows
        ]
    finally:
        connection.close()


def get_employee_by_id(employee_row_id):
    return next(
        (employee for employee in get_all_employees() if employee["id"] == employee_row_id),
        None,
    )


def update_employee(
    employee_row_id, name, surname, cell_number, sa_id_number, start_date,
    identification_type="SA ID",
):
    _validate_employee_data(
        name, surname, cell_number, sa_id_number, start_date, identification_type
    )
    connection = get_connection()
    try:
        cursor = connection.execute("""
            UPDATE employees
            SET name = ?, surname = ?, cell_number = ?, sa_id_number = ?,
                identification_type = ?, start_date = ?
            WHERE id = ?
        """, (
            name.strip(), surname.strip(), cell_number.strip(), sa_id_number.strip(),
            identification_type, start_date, employee_row_id,
        ))
        if cursor.rowcount == 0:
            raise ValueError(f"No employee found with id {employee_row_id}.")
        connection.commit()
    finally:
        connection.close()


def update_employee_document(employee_row_id, document_type, path):
    columns = {"id_copy": "id_copy_path", "contract": "contract_path"}
    column = columns.get(document_type)
    if column is None:
        raise ValueError("Unsupported employee document type.")
    connection = get_connection()
    try:
        cursor = connection.execute(
            f"UPDATE employees SET {column} = ? WHERE id = ?",
            (path, employee_row_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"No employee found with id {employee_row_id}.")
        connection.commit()
    finally:
        connection.close()


def delete_employee(employee_row_id):
    connection = get_connection()
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "DELETE FROM employee_pay_records WHERE employee_id = ?",
            (employee_row_id,),
        )
        connection.execute("DELETE FROM salary_advances WHERE employee_id = ?", (employee_row_id,))
        cursor = connection.execute("DELETE FROM employees WHERE id = ?", (employee_row_id,))
        if cursor.rowcount == 0:
            raise ValueError(f"No employee found with id {employee_row_id}.")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_employee_hourly_rate(employee_row_id, hourly_rate):
    if not math.isfinite(hourly_rate) or hourly_rate < 0:
        raise ValueError("Hourly rate must be a non-negative amount.")
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE employees SET hourly_rate = ? WHERE id = ?",
            (hourly_rate, employee_row_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"No employee found with id {employee_row_id}.")
        connection.commit()
    finally:
        connection.close()


def add_salary_advance(employee_row_id, advance_date, amount, description):
    parsed_date = date.fromisoformat(advance_date)
    if parsed_date.isoformat() != advance_date:
        raise ValueError("Advance date must use YYYY-MM-DD format.")
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("Advance amount must be greater than zero.")
    if not description.strip():
        raise ValueError("Advance description is required.")
    connection = get_connection()
    try:
        cursor = connection.execute("""
            INSERT INTO salary_advances (employee_id, advance_date, amount, description)
            VALUES (?, ?, ?, ?)
        """, (employee_row_id, advance_date, amount, description.strip()))
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_salary_advances(employee_row_id):
    connection = get_connection()
    try:
        rows = connection.execute("""
            SELECT id, employee_id, advance_date, amount, description
            FROM salary_advances WHERE employee_id = ?
            ORDER BY advance_date DESC, id DESC
        """, (employee_row_id,)).fetchall()
        return [
            {
                "id": row[0], "employee_id": row[1], "advance_date": row[2],
                "amount": row[3], "description": row[4],
            }
            for row in rows
        ]
    finally:
        connection.close()


def get_outstanding_advance(employee_row_id, month=None):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM salary_advances WHERE employee_id = ?",
            (employee_row_id,),
        )
        advances = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COALESCE(SUM(advance_deducted), 0) "
            "FROM employee_pay_records WHERE employee_id = ?",
            (employee_row_id,),
        )
        deducted = cursor.fetchone()[0]
        if month:
            cursor.execute("""
                SELECT advance_deducted FROM employee_pay_records
                WHERE employee_id = ? AND month = ?
            """, (employee_row_id, month))
            current_month_deduction = cursor.fetchone()
            if current_month_deduction:
                deducted -= current_month_deduction[0]
        return max(advances - deducted, 0)
    finally:
        connection.close()


def get_outstanding_advances():
    return [
        {
            "employee_id": employee["id"],
            "employee_number": employee["employee_id"],
            "name": f"{employee['name']} {employee['surname']}",
            "balance": get_outstanding_advance(employee["id"]),
        }
        for employee in get_all_employees()
    ]


def get_month_pay_record(employee_row_id, month):
    connection = get_connection()
    try:
        row = connection.execute("""
            SELECT id, employee_id, month, hours_json, hourly_rate, gross_override,
                   gross_pay, employee_uif, employer_uif, paye, advance_deducted,
                   pay_date
            FROM employee_pay_records
            WHERE employee_id = ? AND month = ?
        """, (employee_row_id, month)).fetchone()
        if row is None:
            return None
        return {
            "id": row[0], "employee_id": row[1], "month": row[2],
            "hours": json.loads(row[3]), "hourly_rate": row[4],
            "gross_override": row[5], "gross_pay": row[6],
            "employee_uif": row[7], "employer_uif": row[8],
            "paye": row[9], "advance_deducted": row[10], "pay_date": row[11],
        }
    finally:
        connection.close()


def save_month_pay_record(
    employee_row_id, month, hours, hourly_rate, gross_override, paye,
    advance_deducted, pay_date,
):
    month_date = date.fromisoformat(f"{month}-01")
    if month_date.strftime("%Y-%m") != month:
        raise ValueError("Pay period must use YYYY-MM format.")
    pay_day = date.fromisoformat(pay_date)
    if pay_day.isoformat() != pay_date:
        raise ValueError("Pay date must use YYYY-MM-DD format.")
    if not math.isfinite(hourly_rate) or hourly_rate < 0:
        raise ValueError("Hourly rate must be a non-negative amount.")
    if not math.isfinite(paye) or paye < 0:
        raise ValueError("PAYE must be a non-negative amount.")
    if not math.isfinite(advance_deducted) or advance_deducted < 0:
        raise ValueError("Advance deduction must be a non-negative amount.")
    if any(not math.isfinite(float(value)) or float(value) < 0 for value in hours.values()):
        raise ValueError("Hours must be non-negative numbers.")
    gross = (
        gross_override if gross_override is not None
        else sum(float(value) for value in hours.values()) * hourly_rate
    )
    if not math.isfinite(gross) or gross < 0:
        raise ValueError("Gross pay must be a non-negative amount.")
    outstanding = get_outstanding_advance(employee_row_id, month)
    if advance_deducted > outstanding + 0.000001:
        raise ValueError("Advance deduction cannot exceed the outstanding balance.")
    employee_uif = round(min(gross, UIF_MONTHLY_GROSS_CEILING) * 0.01, 2)
    employer_uif = employee_uif
    connection = get_connection()
    try:
        connection.execute("""
            INSERT INTO employee_pay_records (
                employee_id, month, hours_json, hourly_rate, gross_override,
                gross_pay, employee_uif, employer_uif, paye, advance_deducted,
                pay_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(employee_id, month) DO UPDATE SET
                hours_json = excluded.hours_json,
                hourly_rate = excluded.hourly_rate,
                gross_override = excluded.gross_override,
                gross_pay = excluded.gross_pay,
                employee_uif = excluded.employee_uif,
                employer_uif = excluded.employer_uif,
                paye = excluded.paye,
                advance_deducted = excluded.advance_deducted,
                pay_date = excluded.pay_date
        """, (
            employee_row_id, month, json.dumps(hours), hourly_rate, gross_override,
            gross, employee_uif, employer_uif, paye, advance_deducted, pay_date,
        ))
        connection.execute(
            "UPDATE employees SET hourly_rate = ? WHERE id = ?",
            (hourly_rate, employee_row_id),
        )
        connection.commit()
    finally:
        connection.close()
    return get_month_pay_record(employee_row_id, month)


def get_month_pay_records(month):
    connection = get_connection()
    try:
        rows = connection.execute("""
            SELECT employees.id, employees.employee_id, employees.name,
                   employees.surname, employee_pay_records.gross_pay,
                   employee_pay_records.employee_uif, employee_pay_records.employer_uif,
                   employee_pay_records.paye, employee_pay_records.pay_date
            FROM employee_pay_records
            JOIN employees ON employees.id = employee_pay_records.employee_id
            WHERE employee_pay_records.month = ?
            ORDER BY employees.surname COLLATE NOCASE, employees.name COLLATE NOCASE
        """, (month,)).fetchall()
        return [
            {
                "employee_row_id": row[0], "employee_id": row[1],
                "name": row[2], "surname": row[3], "gross_pay": row[4],
                "employee_uif": row[5], "employer_uif": row[6],
                "paye": row[7], "pay_date": row[8],
            }
            for row in rows
        ]
    finally:
        connection.close()


def get_expense_categories():
    connection = get_connection()
    try:
        rows = connection.execute(
            "SELECT category FROM expense_categories ORDER BY category COLLATE NOCASE"
        ).fetchall()
        return [row[0] for row in rows]
    finally:
        connection.close()


def add_expense_category(category):
    category = category.strip()
    if not category:
        raise ValueError("Category cannot be empty.")
    connection = get_connection()
    try:
        connection.execute(
            "INSERT OR IGNORE INTO expense_categories (category) VALUES (?)",
            (category,),
        )
        connection.commit()
    finally:
        connection.close()
    return category


def add_expense(expense_date, category, description, amount):
    expense_day = date.fromisoformat(expense_date)
    if expense_day.isoformat() != expense_date:
        raise ValueError("Expense date must use YYYY-MM-DD format.")
    if not category.strip() or not description.strip():
        raise ValueError("Category and description are required.")
    if not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
        raise ValueError("Expense amount must be greater than zero.")

    connection = get_connection()
    try:
        cursor = connection.execute("""
            INSERT INTO expenses (expense_date, category, description, amount)
            VALUES (?, ?, ?, ?)
        """, (expense_day.isoformat(), category.strip(), description.strip(), amount))
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_expense(expense_id, expense_date, category, description, amount):
    expense_day = date.fromisoformat(expense_date)
    if expense_day.isoformat() != expense_date:
        raise ValueError("Expense date must use YYYY-MM-DD format.")
    if not category.strip() or not description.strip():
        raise ValueError("Category and description are required.")
    if not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
        raise ValueError("Expense amount must be greater than zero.")

    connection = get_connection()
    try:
        cursor = connection.execute("""
            UPDATE expenses
            SET expense_date = ?, category = ?, description = ?, amount = ?
            WHERE id = ?
        """, (
            expense_day.isoformat(), category.strip(), description.strip(),
            amount, expense_id,
        ))
        if cursor.rowcount == 0:
            raise ValueError(f"No expense found with id {expense_id}.")
        connection.commit()
    finally:
        connection.close()


def delete_expense(expense_id):
    connection = get_connection()
    try:
        cursor = connection.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cursor.rowcount == 0:
            raise ValueError(f"No expense found with id {expense_id}.")
        connection.commit()
    finally:
        connection.close()


def set_monthly_budget(month, category, amount):
    month_date = date.fromisoformat(f"{month}-01")
    if month_date.strftime("%Y-%m") != month:
        raise ValueError("Budget month must use YYYY-MM format.")
    if not category.strip():
        raise ValueError("Category is required.")
    if not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount < 0:
        raise ValueError("Budget must be a non-negative amount.")

    connection = get_connection()
    try:
        cursor = connection.execute("""
            INSERT INTO budgets (month, category, amount)
            VALUES (?, ?, ?)
            ON CONFLICT(month, category) DO UPDATE SET amount = excluded.amount
        """, (month, category.strip(), amount))
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_month_summary(year, month):
    month_start = date(int(year), int(month), 1)
    if month_start.month == 12:
        next_month_start = date(month_start.year + 1, 1, 1)
    else:
        next_month_start = date(month_start.year, month_start.month + 1, 1)
    previous_month = (month_start - timedelta(days=1)).replace(day=1)
    month_key = month_start.strftime("%Y-%m")
    previous_month_key = previous_month.strftime("%Y-%m")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, expense_date, category, description, amount
            FROM expenses
            WHERE expense_date >= ? AND expense_date < ?
            ORDER BY expense_date DESC, id DESC
        """, (month_start.isoformat(), next_month_start.isoformat()))
        expenses = [
            {
                "id": row[0],
                "expense_date": row[1],
                "category": row[2],
                "description": row[3],
                "amount": row[4],
            }
            for row in cursor.fetchall()
        ]
        cursor.execute("""
            SELECT category, amount
            FROM budgets
            WHERE month = ?
            ORDER BY category COLLATE NOCASE
        """, (month_key,))
        budgets = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("""
            SELECT category, SUM(amount)
            FROM expenses
            WHERE expense_date >= ? AND expense_date < ?
            GROUP BY category
        """, (month_start.isoformat(), next_month_start.isoformat()))
        spending_by_category = {row[0]: row[1] for row in cursor.fetchall()}
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM invoices
            WHERE invoice_date >= ? AND invoice_date < ?
        """, (month_start.isoformat(), next_month_start.isoformat()))
        income_invoiced = cursor.fetchone()[0]

        has_payments = cursor.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'payments'
        """).fetchone() is not None
        if has_payments:
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0)
                FROM payments
                WHERE payment_date >= ? AND payment_date < ?
            """, (month_start.isoformat(), next_month_start.isoformat()))
            income_received = cursor.fetchone()[0]
            cursor.execute("""
                SELECT COALESCE(SUM(
                    invoices.total - COALESCE(invoice_payments.amount_paid, 0)
                ), 0)
                FROM invoices
                LEFT JOIN (
                    SELECT invoice_id, SUM(amount) AS amount_paid
                    FROM payments
                    GROUP BY invoice_id
                ) AS invoice_payments ON invoice_payments.invoice_id = invoices.id
                WHERE invoices.invoice_date >= ? AND invoices.invoice_date < ?
            """, (month_start.isoformat(), next_month_start.isoformat()))
            outstanding = max(cursor.fetchone()[0], 0)
        else:
            income_received = 0
            outstanding = income_invoiced

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE expense_date >= ? AND expense_date < ?
        """, (month_start.isoformat(), next_month_start.isoformat()))
        total_expenses = cursor.fetchone()[0]
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE expense_date >= ? AND expense_date < ?
        """, (f"{previous_month_key}-01", month_key + "-01"))
        previous_month_expenses = cursor.fetchone()[0]

        categories = sorted(
            set(budgets) | set(spending_by_category),
            key=str.casefold,
        )
        return {
            "month": month_key,
            "expenses": expenses,
            "budgets": budgets,
            "spending_by_category": spending_by_category,
            "categories": categories,
            "income_invoiced": income_invoiced,
            "income_received": income_received,
            "outstanding": outstanding,
            "total_expenses": total_expenses,
            "previous_month_expenses": previous_month_expenses,
        }
    finally:
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
                subtotal, vat, total, notes, due_date, pdf_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_number, data["customer_id"], data["invoice_date"],
            data["invoice_time"], data["subtotal"], data["vat"],
            data["total"], data.get("notes", ""), data.get("due_date", ""),
            data.get("pdf_path"),
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


def update_invoice(invoice_id, data, items):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("""
            UPDATE invoices
            SET customer_id = ?, subtotal = ?, vat = ?, total = ?,
                notes = ?, due_date = ?
            WHERE id = ?
        """, (
            data["customer_id"], data["subtotal"], data["vat"], data["total"],
            data.get("notes", ""), data.get("due_date", ""), invoice_id,
        ))
        if cursor.rowcount == 0:
            raise ValueError(f"No invoice found with id {invoice_id}.")
        cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        cursor.executemany("""
            INSERT INTO invoice_items (
                invoice_id, description, quantity, unit_price, line_total
            )
            VALUES (?, ?, ?, ?, ?)
        """, [
            (
                invoice_id, item["description"], item.get("quantity", 1),
                item["unit_price"], item["line_total"],
            )
            for item in items
        ])
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_invoice_pdf_path(invoice_id, pdf_path):
    connection = get_connection()
    try:
        cursor = connection.execute(
            "UPDATE invoices SET pdf_path = ? WHERE id = ?",
            (pdf_path, invoice_id),
        )
        if cursor.rowcount == 0:
            raise ValueError(f"No invoice found with id {invoice_id}.")
        connection.commit()
    finally:
        connection.close()


def get_all_invoices():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT invoices.id, invoices.invoice_number, customers.customer_name,
               invoices.invoice_date, invoices.total, invoices.pdf_path
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
            "total": row[4],
            "pdf_path": row[5],
        })

    return invoices


def get_invoice_by_id(invoice_id):
    connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, invoice_number, customer_id, invoice_date, invoice_time,
               subtotal, vat, total, notes, due_date, pdf_path
        FROM invoices
        WHERE id = ?
    """, (invoice_id,))
    row = cursor.fetchone()

    if row is None:
        connection.close()
        return None

    invoice = {
        "id": row["id"],
        "invoice_number": row["invoice_number"],
        "customer_id": row["customer_id"],
        "invoice_date": row["invoice_date"],
        "invoice_time": row["invoice_time"],
        "subtotal": row["subtotal"],
        "vat": row["vat"],
        "total": row["total"],
        "notes": row["notes"],
        "due_date": row["due_date"],
        "pdf_path": row["pdf_path"],
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


def add_payment(invoice_id, amount, payment_date, note=""):
    payment_day = date.fromisoformat(payment_date)
    if payment_day.isoformat() != payment_date:
        raise ValueError("Payment date must use YYYY-MM-DD format.")
    if not isinstance(amount, (int, float)) or not math.isfinite(amount) or amount <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO payments (invoice_id, amount, payment_date, note)
            VALUES (?, ?, ?, ?)
        """, (invoice_id, amount, payment_day.isoformat(), note))
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_payments_for_invoice(invoice_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, invoice_id, amount, payment_date, note
            FROM payments
            WHERE invoice_id = ?
            ORDER BY payment_date DESC, id DESC
        """, (invoice_id,))
        return [
            {
                "id": row[0],
                "invoice_id": row[1],
                "amount": row[2],
                "payment_date": row[3],
                "note": row[4] or "",
            }
            for row in cursor.fetchall()
        ]
    finally:
        connection.close()


def get_month_payment_summary(year, month):
    month_start = date(int(year), int(month), 1)
    if month_start.month == 12:
        next_month_start = date(month_start.year + 1, 1, 1)
    else:
        next_month_start = date(month_start.year, month_start.month + 1, 1)

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT customers.customer_name, invoices.invoice_number,
                   invoices.total, COALESCE(SUM(payments.amount), 0) AS amount_paid,
                   invoices.total - COALESCE(SUM(payments.amount), 0) AS balance,
                   invoices.id
            FROM invoices
            JOIN customers ON customers.id = invoices.customer_id
            LEFT JOIN payments ON payments.invoice_id = invoices.id
            WHERE invoices.invoice_date >= ? AND invoices.invoice_date < ?
            GROUP BY invoices.id
            ORDER BY customers.customer_name COLLATE NOCASE,
                     invoices.invoice_number
        """, (month_start.isoformat(), next_month_start.isoformat()))

        summary = []
        for row in cursor.fetchall():
            amount_paid = row[3]
            if amount_paid <= 0:
                status = "Unpaid"
            elif amount_paid < row[2]:
                status = "Partly paid"
            else:
                status = "Paid"
            summary.append({
                "customer_name": row[0],
                "invoice_number": row[1],
                "total": row[2],
                "amount_paid": amount_paid,
                "balance": max(row[4], 0),
                "status": status,
                "invoice_id": row[5],
            })
        return summary
    finally:
        connection.close()


def delete_invoice(invoice_id):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("SELECT pdf_path FROM invoices WHERE id = ?", (invoice_id,))
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"No invoice found with id {invoice_id}.")
        pdf_path = row[0]
        if cursor.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'payments'
        """).fetchone():
            cursor.execute("DELETE FROM payments WHERE invoice_id = ?", (invoice_id,))
        cursor.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        connection.commit()
        return pdf_path
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_invoice_count_and_total():
    connection = get_connection()
    try:
        return connection.execute(
            "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM invoices"
        ).fetchone()
    finally:
        connection.close()


def delete_all_invoices(reset_numbering=False):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("BEGIN IMMEDIATE")
        cursor.execute("SELECT pdf_path FROM invoices WHERE pdf_path IS NOT NULL")
        pdf_paths = [row[0] for row in cursor.fetchall()]
        if cursor.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'payments'
        """).fetchone():
            cursor.execute("DELETE FROM payments")
        cursor.execute("DELETE FROM invoice_items")
        cursor.execute("DELETE FROM invoices")
        if reset_numbering:
            if cursor.execute("""
                SELECT 1 FROM sqlite_master
                WHERE type = 'table' AND name = 'invoice_number_sequences'
            """).fetchone():
                cursor.execute("DELETE FROM invoice_number_sequences")
        connection.commit()
        return pdf_paths
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def search_invoices(keyword):
    connection = get_connection()
    cursor = connection.cursor()

    search_term = f"%{keyword}%"
    cursor.execute("""
        SELECT invoices.id, invoices.invoice_number, customers.customer_name,
               invoices.invoice_date, invoices.total, invoices.pdf_path
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
            "total": row[4],
            "pdf_path": row[5],
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
    create_payments_table()
    create_budget_tables()
    create_employee_tables()
    print("Database and tables created successfully.")