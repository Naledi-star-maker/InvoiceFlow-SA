"""Create a monthly PDF accounting book from invoice and expense records."""

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

from app.database.database import get_company_info, get_month_summary
from app.utils import format_currency


PINK = colors.HexColor("#DB2777")
PINK_LIGHT = colors.HexColor("#E8E8EC")
TEXT_DARK = colors.HexColor("#0A0A0B")
TEXT_GREY = colors.HexColor("#52525B")
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm


def generate_accounting_insights(summary):
    insights = []
    total = summary["total_expenses"]
    spending = summary["spending_by_category"]
    budgets = summary["budgets"]
    if spending and total:
        category, amount = max(spending.items(), key=lambda item: item[1])
        insights.append(
            f"{category} is {amount / total:.0%} of your expenses "
            f"({format_currency(amount)})."
        )
    over_budget = [
        (category, amount - budgets[category])
        for category, amount in spending.items()
        if category in budgets and amount > budgets[category]
    ]
    if over_budget:
        category, overage = max(over_budget, key=lambda item: item[1])
        insights.append(f"{category} is {format_currency(overage)} over its budget.")
    elif budgets:
        near_budget = next((
            category for category, amount in spending.items()
            if budgets.get(category, 0) > 0
            and amount / budgets[category] >= 0.8
        ), None)
        if near_budget:
            insights.append(f"{near_budget} has used at least 80% of its budget.")
    previous = summary["previous_month_expenses"]
    if previous:
        change = (total - previous) / previous * 100
        if change > 0:
            insights.append(f"Expenses went up {change:.0f}% compared with last month.")
        elif change < 0:
            insights.append(
                f"Expenses went down {abs(change):.0f}% compared with last month."
            )
        else:
            insights.append("Expenses were unchanged from last month.")
    if summary["outstanding"] > 0:
        insights.append(
            f"{format_currency(summary['outstanding'])} of invoices from "
            "this month are still unpaid."
        )
    if summary["income_invoiced"] > summary["income_received"]:
        insights.append("Follow up on outstanding invoices to improve cash flow.")
    if not spending:
        insights.append("Add expenses to see which categories use the most money.")
    if not budgets:
        insights.append("Set monthly budgets to spot overspending sooner.")
    if not insights:
        insights.append("Your expenses are within budget for this month.")
    return insights[:5]


def _draw_footer(company_name):
    def draw(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(PINK_LIGHT)
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN, 14 * mm, PAGE_WIDTH - MARGIN, 14 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(TEXT_GREY)
        canvas.drawString(MARGIN, 9 * mm, company_name)
        canvas.drawRightString(
            PAGE_WIDTH - MARGIN, 9 * mm, f"Page {document.page}"
        )
        canvas.restoreState()
    return draw


def _make_paragraph(value, style):
    return Paragraph(escape(str(value or "")), style)


def _make_table(rows, widths, header=True, right_columns=()):
    table = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, PINK_LIGHT),
    ]
    if header:
        style.extend([
            ("BACKGROUND", (0, 0), (-1, 0), PINK),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ])
    for column in right_columns:
        style.append(("ALIGN", (column, 0), (column, -1), "RIGHT"))
    table.setStyle(TableStyle(style))
    return table


def generate_accounting_book(year, month):
    """Generate a month accounting-book PDF in the invoices export folder."""
    summary = get_month_summary(year, month)
    company = get_company_info() or {}
    company_name = company.get("business_name") or "InvoiceFlow SA"
    month_title = f"{calendar.month_name[int(month)]} {int(year)}"

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="BookTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=20, leading=24, textColor=TEXT_DARK, alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name="BookSection", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=TEXT_DARK, spaceBefore=10, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="BookCell", parent=styles["Normal"], fontSize=8, leading=10,
        textColor=TEXT_DARK, wordWrap="CJK",
    ))
    styles.add(ParagraphStyle(
        name="BookCellRight", parent=styles["BookCell"], alignment=TA_RIGHT,
    ))
    styles.add(ParagraphStyle(
        name="BookHeader", parent=styles["BookCell"], fontName="Helvetica-Bold",
        textColor=colors.white,
    ))

    def cell(value, right=False):
        return _make_paragraph(value, styles["BookCellRight" if right else "BookCell"])

    brand = [cell(company_name)]
    address = ", ".join(filter(None, (
        company.get("address"), company.get("city"), company.get("province"),
        company.get("postal_code"),
    )))
    if address:
        brand.append(cell(address))
    if company.get("email"):
        brand.append(cell(company["email"]))
    logo_path = company.get("logo_path")
    if logo_path and os.path.isfile(logo_path):
        logo = Image(logo_path, width=22 * mm, height=22 * mm, kind="proportional")
        company_block = Table([[logo, brand]], colWidths=(24 * mm, 80 * mm))
        company_block.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
    else:
        company_block = brand

    story = [
        Table(
            [[company_block, Paragraph(escape(month_title), styles["BookTitle"])]],
            colWidths=(PAGE_WIDTH - 2 * MARGIN - 65 * mm, 65 * mm),
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEBELOW", (0, 0), (-1, -1), 1, PINK),
            ]),
        ),
        Spacer(1, 7 * mm),
        Paragraph("Income summary", styles["BookSection"]),
    ]

    income_rows = [[
        Paragraph("Invoiced", styles["BookHeader"]),
        Paragraph("Received", styles["BookHeader"]),
        Paragraph("Outstanding", styles["BookHeader"]),
    ], [
        cell(format_currency(summary["income_invoiced"])),
        cell(format_currency(summary["income_received"])),
        cell(format_currency(summary["outstanding"])),
    ]]
    story.append(_make_table(income_rows, (58 * mm, 58 * mm, 58 * mm), right_columns=(0, 1, 2)))

    expenses = summary["expenses"]
    story.append(Paragraph("Expenses by date", styles["BookSection"]))
    expense_rows = [[
        Paragraph("Date", styles["BookHeader"]),
        Paragraph("Category", styles["BookHeader"]),
        Paragraph("Description", styles["BookHeader"]),
        Paragraph("Amount", styles["BookHeader"]),
    ]]
    expense_rows.extend([
        [cell(item["expense_date"]), cell(item["category"]),
         cell(item["description"]), cell(format_currency(item["amount"]), True)]
        for item in expenses
    ] or [[cell("No expenses recorded"), cell(""), cell(""), cell(format_currency(0), True)]])
    story.append(_make_table(
        expense_rows,
        (28 * mm, 38 * mm, 78 * mm, 24 * mm),
        right_columns=(3,),
    ))

    story.append(Paragraph("Expenses by category", styles["BookSection"]))
    category_totals = summary["spending_by_category"]
    category_rows = [[
        Paragraph("Category", styles["BookHeader"]),
        Paragraph("Total expenses", styles["BookHeader"]),
    ]]
    category_rows.extend([
        [cell(category), cell(format_currency(amount), True)]
        for category, amount in sorted(category_totals.items(), key=lambda item: item[0].casefold())
    ] or [[cell("No expenses recorded"), cell(format_currency(0), True)]])
    story.append(_make_table(category_rows, (125 * mm, 55 * mm), right_columns=(1,)))

    story.append(Paragraph("Budget vs actual", styles["BookSection"]))
    categories = sorted(
        set(summary["budgets"]) | set(category_totals),
        key=str.casefold,
    )
    budget_rows = [[
        Paragraph("Category", styles["BookHeader"]),
        Paragraph("Budget", styles["BookHeader"]),
        Paragraph("Spent", styles["BookHeader"]),
        Paragraph("Remaining", styles["BookHeader"]),
        Paragraph("% used", styles["BookHeader"]),
    ]]
    for category in categories:
        budget = summary["budgets"].get(category, 0)
        spent = category_totals.get(category, 0)
        percent = f"{spent / budget:.0%}" if budget else ("Over budget" if spent else "—")
        budget_rows.append([
            cell(category), cell(format_currency(budget), True),
            cell(format_currency(spent), True),
            cell(format_currency(budget - spent), True), cell(percent, True),
        ])
    if len(budget_rows) == 1:
        budget_rows.append([
            cell("No budgets or expenses"), cell(format_currency(0), True),
            cell(format_currency(0), True), cell(format_currency(0), True),
            cell("—", True),
        ])
    story.append(_make_table(
        budget_rows, (42 * mm, 32 * mm, 32 * mm, 38 * mm, 26 * mm),
        right_columns=(1, 2, 3, 4),
    ))

    profit = summary["income_received"] - summary["total_expenses"]
    story.extend([
        Paragraph("Profit / loss", styles["BookSection"]),
        _make_table(
            [[cell("Income received minus total expenses"),
              cell(format_currency(profit), True)]],
            (125 * mm, 55 * mm),
            header=False,
            right_columns=(1,),
        ),
        Paragraph("Things to improve", styles["BookSection"]),
    ])
    story.extend(
        cell(f"•  {insight}") for insight in generate_accounting_insights(summary)
    )

    bank_details = [
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
    if bank_details:
        story.append(Paragraph("Banking details", styles["BookSection"]))
        bank_rows = [
            [cell(f"{label}: {value}") for label, value in bank_details[index:index + 2]]
            for index in range(0, len(bank_details), 2)
        ]
        if len(bank_rows[-1]) == 1:
            bank_rows[-1].append(cell(""))
        story.append(_make_table(bank_rows, (87 * mm, 87 * mm), header=False))

    output_folder = "invoices"
    os.makedirs(output_folder, exist_ok=True)
    file_path = os.path.join(
        output_folder, f"Accounting-Book-{summary['month']}.pdf"
    )
    document = BaseDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=17 * mm,
        bottomMargin=20 * mm,
        title=f"Monthly Accounting Book - {month_title}",
        author=company_name,
    )
    frame = Frame(
        MARGIN, 20 * mm, PAGE_WIDTH - 2 * MARGIN,
        PAGE_HEIGHT - 37 * mm, id="accounting-book",
    )
    document.addPageTemplates([
        PageTemplate(
            id="accounting-book",
            frames=frame,
            onPage=_draw_footer(company_name),
        )
    ])
    document.build(story)
    return file_path
