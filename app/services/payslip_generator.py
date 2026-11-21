"""Generate employee payslip PDFs."""

import calendar
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.database.database import (
    get_company_info,
    get_employee_by_id,
    get_month_pay_record,
)
from app.utils import format_currency


PINK = colors.HexColor("#DB2777")
PINK_LIGHT = colors.HexColor("#E8E8EC")
TEXT_DARK = colors.HexColor("#0A0A0B")
TEXT_GREY = colors.HexColor("#52525B")
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm


def _draw_footer(canvas, document):
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


def generate_payslip(employee_row_id, month):
    """Generate a payslip for a saved employee pay record."""
    employee = get_employee_by_id(employee_row_id)
    if employee is None:
        raise ValueError(f"No employee found with id {employee_row_id}")
    pay = get_month_pay_record(employee_row_id, month)
    if pay is None:
        raise ValueError(f"No pay record found for {employee['employee_id']} in {month}")
    company = get_company_info() or {}
    company_name = company.get("business_name") or "InvoiceFlow SA"

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="PayslipTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=20, leading=24, textColor=TEXT_DARK, alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name="PayslipSection", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=TEXT_DARK, spaceBefore=14, spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="PayslipCell", parent=styles["Normal"], fontSize=9, leading=12,
        textColor=TEXT_DARK,
    ))
    styles.add(ParagraphStyle(
        name="PayslipRight", parent=styles["PayslipCell"], alignment=TA_RIGHT,
    ))

    def paragraph(value, style="PayslipCell"):
        return Paragraph(escape(str(value or "")), styles[style])

    company_lines = [paragraph(company_name)]
    address = ", ".join(filter(None, (
        company.get("address"), company.get("city"), company.get("province"),
        company.get("postal_code"),
    )))
    if address:
        company_lines.append(paragraph(address))
    for key in ("phone", "email"):
        if company.get(key):
            company_lines.append(paragraph(company[key]))

    logo_path = company.get("logo_path")
    if logo_path and os.path.isfile(logo_path):
        logo = Image(logo_path, width=22 * mm, height=22 * mm, kind="proportional")
        company_block = Table([[logo, company_lines]], colWidths=(25 * mm, 95 * mm))
        company_block.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
    else:
        company_block = company_lines

    month_year = f"{calendar.month_name[int(month[5:7])]} {month[:4]}"
    story = [
        Table(
            [[company_block, Paragraph(
                escape(f"Payslip - {month_year}"), styles["PayslipTitle"]
            )]],
            colWidths=(PAGE_WIDTH - 2 * MARGIN - 65 * mm, 65 * mm),
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), 1, PINK),
            ]),
        ),
        Spacer(1, 8 * mm),
        paragraph(f"Employee: {employee['name']} {employee['surname']}"),
        paragraph(f"Employee ID: {employee['employee_id']}"),
        paragraph(f"SA ID number: {employee['sa_id_number']}"),
        paragraph(f"Pay date: {pay['pay_date']}"),
        Paragraph("Earnings", styles["PayslipSection"]),
    ]

    hours_worked = sum(float(hours) for hours in pay["hours"].values())
    earnings_rows = [
        [paragraph("Description"), paragraph("Amount", "PayslipRight")],
        [paragraph(f"Hours worked ({hours_worked:g} hours at {format_currency(pay['hourly_rate'])}/hour)"),
         paragraph("")],
        [paragraph("Gross pay"), paragraph(format_currency(pay["gross_pay"]), "PayslipRight")],
    ]
    story.append(_make_table(earnings_rows))
    story.append(Paragraph("Deductions", styles["PayslipSection"]))
    deductions_rows = [
        [paragraph("Deduction"), paragraph("Amount", "PayslipRight")],
        [paragraph("Employee UIF"), paragraph(format_currency(pay["employee_uif"]), "PayslipRight")],
        [paragraph("PAYE"), paragraph(format_currency(pay["paye"]), "PayslipRight")],
    ]
    story.append(_make_table(deductions_rows))
    net_pay = pay["gross_pay"] - pay["employee_uif"] - pay["paye"]
    net_table = Table(
        [[paragraph("NET PAY"), paragraph(format_currency(net_pay), "PayslipRight")]],
        colWidths=(PAGE_WIDTH - 2 * MARGIN - 42 * mm, 42 * mm),
    )
    net_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FDF2F8")),
        ("BOX", (0, 0), (-1, -1), 0.8, PINK_LIGHT),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.extend([
        Spacer(1, 4 * mm),
        net_table,
        Paragraph("Employer contribution", styles["PayslipSection"]),
        paragraph(f"Employer UIF: {format_currency(pay['employer_uif'])}"),
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
    if banking:
        story.append(Paragraph("Company banking details", styles["PayslipSection"]))
        bank_rows = [
            [paragraph(f"{label}: {value}") for label, value in banking[index:index + 2]]
            for index in range(0, len(banking), 2)
        ]
        if len(bank_rows[-1]) == 1:
            bank_rows[-1].append(paragraph(""))
        story.append(_make_table(bank_rows, (87 * mm, 87 * mm), header=False))

    output_folder = os.path.join("payslips", month)
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(
        output_folder, f"{employee['employee_id']}-{month}.pdf"
    )
    document = BaseDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=f"Payslip - {month_year} - {employee['employee_id']}",
        author=company_name,
    )
    frame = Frame(
        MARGIN, 20 * mm, PAGE_WIDTH - 2 * MARGIN,
        PAGE_HEIGHT - 37 * mm, id="payslip",
    )
    document.addPageTemplates([
        PageTemplate(id="payslip", frames=frame, onPage=_draw_footer)
    ])
    document.build(story)
    return file_path


def _make_table(rows, widths=None, header=True):
    if widths is None:
        widths = (PAGE_WIDTH - 2 * MARGIN - 42 * mm, 42 * mm)
    table = Table(rows, colWidths=widths, repeatRows=1 if header else 0)
    commands = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, PINK_LIGHT),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FAFAFA")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    table.setStyle(TableStyle(commands))
    return table
