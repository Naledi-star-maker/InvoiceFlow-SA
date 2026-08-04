"""
=========================================================
InvoiceFlow SA
PDF Generator

Turns a saved invoice into a professional PDF file,
saved into the /invoices folder.
=========================================================
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from app.database.database import get_invoice_by_id, get_company_info, get_customer_by_id


PINK = colors.HexColor("#F4A6C6")
PINK_LIGHT = colors.HexColor("#FDEFF3")
TEXT_DARK = colors.HexColor("#3A2A30")
TEXT_GREY = colors.HexColor("#6B5A60")


def generate_invoice_pdf(invoice_id):
    """
    Builds a PDF for the given invoice_id and saves it into /invoices.
    Returns the full file path of the created PDF.
    """

    invoice = get_invoice_by_id(invoice_id)
    if invoice is None:
        raise ValueError(f"No invoice found with id {invoice_id}")

    company = get_company_info()
    if company is None:
        raise ValueError("Company details have not been set up yet.")

    customer = get_customer_by_id(invoice["customer_id"])
    if customer is None:
        raise ValueError("Customer for this invoice could not be found.")

    os.makedirs("invoices", exist_ok=True)
    file_path = os.path.join("invoices", f"{invoice['invoice_number']}.pdf")

    page_width, page_height = A4
    c = canvas.Canvas(file_path, pagesize=A4)

    margin = 20 * mm
    y = page_height - margin

    # ---------- Header: Company name + Invoice label ----------
    if company.get("logo_path") and os.path.exists(company["logo_path"]):
        try:
            c.drawImage(company["logo_path"], margin, y - 20 * mm,
                        width=25 * mm, height=25 * mm, preserveAspectRatio=True, mask='auto')
            text_x = margin + 30 * mm
        except Exception:
            text_x = margin
    else:
        text_x = margin

    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(TEXT_DARK)
    c.drawString(text_x, y, company["business_name"])

    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_GREY)
    c.drawString(text_x, y - 14, company["address"])
    c.drawString(text_x, y - 26, f"{company['city']}, {company['province']} {company['postal_code']}")
    c.drawString(text_x, y - 38, f"Tel: {company['phone']}  |  Email: {company['email']}")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(PINK)
    c.drawRightString(page_width - margin, y, "INVOICE")

    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_DARK)
    c.drawRightString(page_width - margin, y - 18, f"Invoice #: {invoice['invoice_number']}")
    c.drawRightString(page_width - margin, y - 32, f"Date: {invoice['invoice_date']}")
    c.drawRightString(page_width - margin, y - 46, f"Time: {invoice['invoice_time']}")

    y -= 65 * mm / 3  # move down below header block

    # ---------- Divider ----------
    y -= 5
    c.setStrokeColor(PINK)
    c.setLineWidth(1.2)
    c.line(margin, y, page_width - margin, y)
    y -= 20

    # ---------- Bill To ----------
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(PINK)
    c.drawString(margin, y, "BILL TO")
    y -= 16

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_DARK)
    c.drawString(margin, y, customer["customer_name"])
    y -= 14

    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_GREY)
    if customer.get("business_name"):
        c.drawString(margin, y, customer["business_name"])
        y -= 12
    if customer.get("address"):
        address_line = customer["address"]
        if customer.get("city"):
            address_line += f", {customer['city']}"
        c.drawString(margin, y, address_line)
        y -= 12
    if customer.get("phone"):
        c.drawString(margin, y, f"Tel: {customer['phone']}")
        y -= 12
    if customer.get("email"):
        c.drawString(margin, y, f"Email: {customer['email']}")
        y -= 12

    y -= 15

    # ---------- Items table header ----------
    table_top = y
    col_desc_x = margin
    col_qty_x = page_width - margin - 110
    col_price_x = page_width - margin - 75
    col_total_x = page_width - margin

    c.setFillColor(PINK)
    c.rect(margin, y - 18, page_width - 2 * margin, 20, fill=1, stroke=0)

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(colors.white)
    c.drawString(col_desc_x + 5, y - 13, "DESCRIPTION")
    c.drawString(col_qty_x, y - 13, "QTY")
    c.drawString(col_price_x, y - 13, "PRICE")
    c.drawRightString(col_total_x - 5, y - 13, "TOTAL")

    y -= 18

    # ---------- Items table rows ----------
    c.setFont("Helvetica", 9)
    row_height = 20

    for index, item in enumerate(invoice["items"]):
        if y < 60 * mm:
            c.showPage()
            y = page_height - margin

        bg = PINK_LIGHT if index % 2 == 0 else colors.white
        c.setFillColor(bg)
        c.rect(margin, y - row_height, page_width - 2 * margin, row_height, fill=1, stroke=0)

        c.setFillColor(TEXT_DARK)
        c.setFont("Helvetica", 9)

        description = item["description"]
        if len(description) > 55:
            description = description[:52] + "..."

        c.drawString(col_desc_x + 5, y - 14, description)
        c.drawString(col_qty_x, y - 14, str(item["quantity"]))
        c.drawString(col_price_x, y - 14, f"R{item['unit_price']:.2f}")
        c.drawRightString(col_total_x - 5, y - 14, f"R{item['line_total']:.2f}")

        y -= row_height

    y -= 10

    # ---------- Totals ----------
    c.setStrokeColor(PINK)
    c.line(page_width - margin - 150, y, page_width - margin, y)
    y -= 18

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(TEXT_DARK)
    c.drawString(page_width - margin - 150, y, "TOTAL DUE")
    c.drawRightString(page_width - margin, y, f"R{invoice['total']:.2f}")
    y -= 30

    # ---------- Notes ----------
    if invoice.get("notes"):
        c.setFont("Helvetica-Oblique", 9)
        c.setFillColor(TEXT_GREY)
        c.drawString(margin, y, f"Notes: {invoice['notes']}")
        y -= 25

    # ---------- Banking details box ----------
    if y < 90 * mm:
        c.showPage()
        y = page_height - margin

    box_top = y
    box_height = 70
    c.setFillColor(PINK_LIGHT)
    c.rect(margin, box_top - box_height, page_width - 2 * margin, box_height, fill=1, stroke=0)

    by = box_top - 16
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PINK)
    c.drawString(margin + 10, by, "BANKING DETAILS")
    by -= 16

    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_DARK)
    c.drawString(margin + 10, by, f"Bank: {company['bank_name']}")
    c.drawString(margin + 230, by, f"Account Holder: {company['account_holder']}")
    by -= 14
    c.drawString(margin + 10, by, f"Account Number: {company['account_number']}")
    c.drawString(margin + 230, by, f"Branch Code: {company['branch_code']}")
    by -= 14
    c.drawString(margin + 10, by, f"Account Type: {company['account_type']}")

    reference_prefix = company.get("reference_prefix") or "INV"
    c.drawString(margin + 230, by, f"Reference: {invoice['invoice_number']}")

    y = box_top - box_height - 25

    # ---------- Thank you + signature ----------
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(PINK)
    c.drawCentredString(page_width / 2, y, "Thank you for your business!")

    if company.get("signature_path") and os.path.exists(company["signature_path"]):
        try:
            c.drawImage(company["signature_path"], page_width - margin - 40 * mm, y - 30,
                        width=40 * mm, height=15 * mm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    c.save()

    return file_path