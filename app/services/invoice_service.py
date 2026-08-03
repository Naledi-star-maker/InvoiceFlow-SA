"""
=========================================================
InvoiceFlow SA
Invoice Service

This file contains the business logic for invoices.

Responsibilities:
• Generate invoice numbers
• Generate current date and time
• Calculate invoice totals
• Create invoice data dictionaries

NOTE:
This file DOES NOT communicate directly with SQLite.
It calls functions in database.py.
=========================================================
"""

from datetime import datetime

# Import database functions
from app.database.database import (
    add_invoice,
    add_invoice_item,
    get_next_invoice_number
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

    next_number = get_next_invoice_number()

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

def calculate_totals(items, vat_rate=0.15):
    """
    items should be:

    [
        {
            "description":"Garden Service",
            "quantity":2,
            "unit_price":500
        }
    ]
    """

    subtotal = 0

    for item in items:

        line_total = item["quantity"] * item["unit_price"]

        subtotal += line_total

    vat = subtotal * vat_rate

    total = subtotal + vat

    return {
        "subtotal": round(subtotal, 2),
        "vat": round(vat, 2),
        "total": round(total, 2)
    }


# =========================================================
# Create Invoice
# =========================================================

def create_invoice(customer_id, items):
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

    invoice_number = generate_invoice_number()

    invoice_date = get_current_date()

    invoice_time = get_current_time()

    totals = calculate_totals(items)

    invoice_data = {
        "customer_id": customer_id,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "invoice_time": invoice_time,
        "subtotal": totals["subtotal"],
        "vat": totals["vat"],
        "total": totals["total"]
    }

    # Save invoice
    invoice_id = add_invoice(invoice_data)

    # Save each invoice line
    for item in items:

        item_data = {
            "invoice_id": invoice_id,
            "description": item["description"],
            "quantity": item["quantity"],
            "unit_price": item["unit_price"],
            "line_total": item["quantity"] * item["unit_price"]
        }

        add_invoice_item(item_data)

    return invoice_id