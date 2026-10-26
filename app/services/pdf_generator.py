"""Generate professional PDF invoices in the application's invoices folder."""

import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Image,
    LongTable,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus import BaseDocTemplate, Frame

from app.database.database import get_company_info, get_customer_by_id, get_invoice_by_id
from app.utils import format_currency


PINK = colors.HexColor("#F4A6C6")
PINK_LIGHT = colors.HexColor("#FDEFF3")
TEXT_DARK = colors.HexColor("#3A2A30")
TEXT_GREY = colors.HexColor("#6B5A60")
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm
TABLE_WIDTHS = (112 * mm, 18 * mm, 38 * mm)


def _format_quantity(quantity):
    value = float(quantity or 0)
    return str(int(value)) if value.is_integer() else f"{value:g}"


def _format_date(value):
    if not value:
        return ""
    try:
        from datetime import date
        return date.fromisoformat(str(value)).strftime("%d %B %Y")
    except ValueError:
        return str(value)


def _invoice_table_rows(items):
    """Prepare the exact three displayed columns without changing line totals."""
    rows = [["Description", "Qty", "Total"]]
    for item in items:
        line_total = item.get("line_total")
        if line_total is None:
            line_total = (item.get("quantity") or 0) * (item.get("unit_price") or 0)
        rows.append([
            item.get("description") or "",
            _format_quantity(item.get("quantity")),
            format_currency(line_total),
        ])
    if not items:
        rows.append(["No line items recorded.", "", ""])
    return rows


def _draw_page_footer(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(PINK_LIGHT)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN, 14 * mm, PAGE_WIDTH - MARGIN, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_GREY)
    canvas.drawString(MARGIN, 9 * mm, "InvoiceFlow SA")
    canvas.drawRightString(
        PAGE_WIDTH - MARGIN, 9 * mm, f"Page {document.page}"
    )
    canvas.restoreState()


def _build_invoice_story(invoice, company, customer):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="InvoiceBusiness", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=15, leading=18, textColor=TEXT_DARK, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="InvoiceTitle", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=21, leading=25, textColor=PINK, alignment=TA_RIGHT
    ))
    styles.add(ParagraphStyle(
        name="InvoiceDetails", parent=styles["Normal"], fontSize=8.5,
        leading=12, textColor=TEXT_GREY
    ))
    styles.add(ParagraphStyle(
        name="InvoiceSection", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=9, leading=12, textColor=PINK, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="InvoiceCustomer", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=10, leading=13, textColor=TEXT_DARK, spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="InvoiceCell", parent=styles["Normal"], fontSize=8.5,
        leading=11, textColor=TEXT_DARK, wordWrap="CJK"
    ))
    styles.add(ParagraphStyle(
        name="InvoiceCellRight", parent=styles["InvoiceCell"],
        alignment=TA_RIGHT
    ))
    styles.add(ParagraphStyle(
        name="InvoiceCellCenter", parent=styles["InvoiceCell"],
        alignment=TA_CENTER
    ))

    def paragraph(value, style="InvoiceDetails"):
        return Paragraph(escape(str(value or "")), styles[style])

    business_lines = [
        company.get("address"),
        ", ".join(filter(None, (
            company.get("city"), company.get("province"), company.get("postal_code")
        ))),
        f"Tel: {company['phone']}" if company.get("phone") else None,
        company.get("email"),
    ]
    business_details = [paragraph(line) for line in business_lines if line]
    business_block = [
        paragraph(company.get("business_name") or "Business", "InvoiceBusiness"),
        *business_details
    ]
    logo_path = company.get("logo_path")
    if logo_path and os.path.isfile(logo_path):
        logo = Image(
            logo_path, width=25 * mm, height=25 * mm, kind="proportional"
        )
        business_block = Table(
            [[logo, business_block]],
            colWidths=(28 * mm, PAGE_WIDTH - 2 * MARGIN - 58 * mm - 28 * mm)
        )
        business_block.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))

    invoice_details = [
        paragraph(f"Invoice #: {invoice.get('invoice_number') or '—'}"),
        paragraph(f"Issue date: {_format_date(invoice.get('invoice_date')) or '—'}"),
    ]
    if invoice.get("due_date"):
        invoice_details.append(
            paragraph(f"Due date: {_format_date(invoice.get('due_date'))}")
        )
    if invoice.get("invoice_time"):
        invoice_details.append(paragraph(f"Time: {invoice['invoice_time']}"))

    header = Table(
        [[business_block, [paragraph("INVOICE", "InvoiceTitle"), *invoice_details]]],
        colWidths=(PAGE_WIDTH - 2 * MARGIN - 58 * mm, 58 * mm),
        hAlign="LEFT"
    )
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 1, PINK),
    ]))

    customer_lines = [
        customer.get("business_name"),
        customer.get("address"),
        ", ".join(filter(None, (
            customer.get("city"), customer.get("province"), customer.get("postal_code")
        ))),
        f"Tel: {customer['phone']}" if customer.get("phone") else None,
        customer.get("email"),
    ]
    customer_block = [
        paragraph("BILL TO", "InvoiceSection"),
        paragraph(customer.get("customer_name") or "Customer", "InvoiceCustomer"),
        *[paragraph(line) for line in customer_lines if line]
    ]

    story = [header, Spacer(1, 9 * mm), *customer_block, Spacer(1, 8 * mm)]

    header_style = ParagraphStyle(
        "InvoiceTableHeader", parent=styles["InvoiceCell"],
        fontName="Helvetica-Bold", textColor=colors.white
    )
    rows = _invoice_table_rows(invoice.get("items") or [])
    table_data = [[
        Paragraph("Description", header_style),
        Paragraph("Qty", header_style),
        Paragraph("Total", ParagraphStyle(
            "InvoiceTableHeaderRight", parent=header_style, alignment=TA_RIGHT
        )),
    ]]
    for description, quantity, total in rows[1:]:
        table_data.append([
            paragraph(description, "InvoiceCell"),
            paragraph(quantity, "InvoiceCellCenter"),
            paragraph(total, "InvoiceCellRight"),
        ])

    item_table = LongTable(
        table_data,
        colWidths=TABLE_WIDTHS,
        repeatRows=1,
        splitByRow=1,
        splitInRow=1,
        hAlign="LEFT"
    )
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PINK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PINK_LIGHT, colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, PINK),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, PINK_LIGHT),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 7 * mm))

    total_block = Table(
        [[paragraph("TOTAL DUE", "InvoiceCustomer"),
          paragraph(format_currency(invoice.get("total")), "InvoiceCellRight")]],
        colWidths=(PAGE_WIDTH - 2 * MARGIN - 42 * mm, 42 * mm)
    )
    total_block.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PINK_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, PINK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (1, 0), (1, 0), 14),
    ]))
    story.append(KeepTogether([total_block]))

    if invoice.get("notes"):
        story.extend([
            Spacer(1, 7 * mm),
            paragraph("Notes", "InvoiceSection"),
            paragraph(invoice["notes"], "InvoiceDetails"),
        ])

    banking = [
        (label, company.get(key))
        for label, key in (
            ("Bank", "bank_name"),
            ("Account holder", "account_holder"),
            ("Account number", "account_number"),
            ("Branch code", "branch_code"),
            ("Account type", "account_type"),
        )
        if company.get(key)
    ]
    if invoice.get("invoice_number"):
        banking.append(("Payment reference", invoice["invoice_number"]))
    if banking:
        story.extend([Spacer(1, 8 * mm), paragraph("BANKING DETAILS", "InvoiceSection")])
        bank_rows = [
            [paragraph(f"{label}: {value}") for label, value in banking[index:index + 2]]
            for index in range(0, len(banking), 2)
        ]
        if len(bank_rows[-1]) == 1:
            bank_rows[-1].append(paragraph(""))
        bank_table = Table(
            bank_rows,
            colWidths=((PAGE_WIDTH - 2 * MARGIN) / 2,) * 2,
            hAlign="LEFT"
        )
        bank_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PINK_LIGHT),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(bank_table)

    thanks = Paragraph(
        "Thank you for your business!",
        ParagraphStyle(
            "InvoiceThanks", parent=styles["Normal"], fontName="Helvetica-Oblique",
            fontSize=10, leading=13, textColor=PINK, alignment=TA_CENTER
        )
    )
    signature_path = company.get("signature_path")
    if signature_path and os.path.isfile(signature_path):
        signature = Image(
            signature_path, width=40 * mm, height=15 * mm, kind="proportional"
        )
        signature_block = Table(
            [[thanks, signature]],
            colWidths=(PAGE_WIDTH - 2 * MARGIN - 42 * mm, 42 * mm)
        )
        signature_block.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story.extend([Spacer(1, 8 * mm), signature_block])
    else:
        story.extend([Spacer(1, 8 * mm), thanks])
    return story


def generate_invoice_pdf(invoice_id):
    """Generate and save an invoice PDF, returning its path."""
    invoice = get_invoice_by_id(invoice_id)
    if invoice is None:
        raise ValueError(f"No invoice found with id {invoice_id}")

    company = get_company_info()
    if company is None:
        raise ValueError("Company details have not been set up yet.")

    customer = get_customer_by_id(invoice.get("customer_id"))
    if customer is None:
        raise ValueError("Customer for this invoice could not be found.")

    os.makedirs("invoices", exist_ok=True)
    file_path = os.path.join("invoices", f"{invoice.get('invoice_number', invoice_id)}.pdf")
    document = BaseDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=f"Invoice {invoice.get('invoice_number', '')}",
        author=company.get("business_name") or "InvoiceFlow SA",
    )
    frame = Frame(
        MARGIN, 20 * mm, PAGE_WIDTH - 2 * MARGIN,
        PAGE_HEIGHT - 37 * mm, id="invoice"
    )
    document.addPageTemplates([
        PageTemplate(id="invoice", frames=frame, onPage=_draw_page_footer)
    ])
    document.build(_build_invoice_story(invoice, company, customer))
    return file_path
