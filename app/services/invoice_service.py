"""
=========================================================
InvoiceFlow SA
Invoice Service

This file contains the business logic for invoices.

Responsibilities:
- Generate invoice numbers
- Generate current date and time
- Calculate invoice totals
- Create invoice data dictionaries

NOTE:
This file DOES NOT communicate directly with SQLite.
It calls functions in database.py.
=========================================================
"""

from datetime import datetime

# Import database functions
from app.database.database import (
    create_invoice_with_items,
    get_next_invoice_number,
    get_invoice_by_id
)


# =========================================================
# Generate Invoice Number
# =========================================================

def generate_invoice_number():
    """
    Creates invoice numbers like:

    INV-2026-00001
    INV-2026-00002
    INV-2026-00003
    """

    current_year = datetime.now().year

    next_number = get_next_invoice_number(current_year)

    return f"INV-{current_year}-{next_number:05d}"


# =========================================================
# Get Today's Date
# =========================================================

def get_current_date():
    """
    Returns today's date.

    Stored in ISO format because it is easier
    to sort and search in the database.

    Example:
    2026-08-03
    """

    return datetime.now().strftime("%Y-%m-%d")


# =========================================================
# Get Current Time
# =========================================================

def get_current_time():
    """
    Returns the current time.

    Example:
    14:32
    """

    return datetime.now().strftime("%H:%M")


# =========================================================
# Calculate Totals
# =========================================================

def calculate_totals(items):
    """
    items should be:

    [
        {
            "description": "Garden Service",
            "quantity": 2,
            "unit_price": 500
        }
    ]

    No VAT is applied — InvoiceFlow SA targets small
    businesses that are typically not VAT registered.
    """

    subtotal = 0

    for item in items:
        line_total = item["quantity"] * item["unit_price"]
        subtotal += line_total

    return {
        "subtotal": round(subtotal, 2),
        "total": round(subtotal, 2)
    }


# =========================================================
# Create Invoice
# =========================================================

def create_invoice(customer_id, items, notes=""):
    """
    Creates a complete invoice.

    This function:

    • Generates invoice number
    • Generates date
    • Generates time
    • Calculates totals
    • Saves invoice
    • Saves invoice items
    """

    invoice_date = get_current_date()
    invoice_time = get_current_time()
    totals = calculate_totals(items)

    invoice_data = {
        "customer_id": customer_id,
        "invoice_date": invoice_date,
        "invoice_time": invoice_time,
        "subtotal": totals["subtotal"],
        "vat": 0,
        "total": totals["total"],
        "notes": notes
    }

    invoice_items = [
        {
            "description": item["description"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "line_total": item["quantity"] * item["unit_price"]
        }
        for item in items
    ]
    return create_invoice_with_items(invoice_data, invoice_items)


# =========================================================
# Duplicate Invoice (for month-end resends)
# =========================================================

def duplicate_invoice(source_invoice_id, items, notes=None):
    """
    Creates a NEW invoice for the same customer as an existing invoice,
    with a freshly generated invoice number, date and time.

    Used for month-end resends: reuse an old invoice's customer/items
    as a starting point, optionally edit items/prices, and this
    produces a new invoice record + new PDF — the original invoice
    is left untouched.
    """

    source = get_invoice_by_id(source_invoice_id)
    if source is None:
        raise ValueError(f"No invoice found with id {source_invoice_id}")

    if notes is None:
        notes = source.get("notes", "") or ""

    return create_invoice(source["customer_id"], items, notes)