from datetime import datetime

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.database.database import get_business_statistics, get_total_customers
from app.utils import format_currency


PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"
CARD_BG = "#FDEFF3"


def _month_label(month):
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%b %Y")
    except ValueError:
        return month


class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=WHITE)
        self.controller = controller

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=WHITE)
        self.scroll.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            self.scroll, text="Business Reports",
            font=ctk.CTkFont(size=26, weight="bold"), text_color=PINK_DARK
        ).pack(pady=(20, 4))
        ctk.CTkLabel(
            self.scroll,
            text="Invoiced revenue is based on invoice totals; it is not money received or profit.",
            text_color=PINK_TEXT, wraplength=850
        ).pack(pady=(0, 16))

        stats = get_business_statistics()
        cards = ctk.CTkFrame(self.scroll, fg_color=WHITE)
        cards.pack(fill="x", padx=20)
        for column in range(3):
            cards.grid_columnconfigure(column, weight=1)

        percentage = stats["percentage_change"]
        values = [
            ("Customers", str(get_total_customers())),
            ("Total invoices", str(stats["total_invoices"])),
            ("Average invoice value", format_currency(stats["average_invoice_value"])),
            ("This month's invoiced revenue", format_currency(stats["current_month_revenue"])),
            ("Previous month's invoiced revenue", format_currency(stats["previous_month_revenue"])),
            ("Change vs. previous month", (
                f"{percentage:+.1f}%" if percentage is not None
                else "No prior-month baseline"
            )),
            ("Year-to-date invoiced revenue", format_currency(stats["year_to_date_revenue"])),
        ]
        for index, (title, value) in enumerate(values):
            self.create_card(cards, title, value, index // 3, index % 3)

        self._add_section_title("Monthly Invoiced Revenue")
        revenue = stats["monthly_revenue"]
        chart_frame = ctk.CTkFrame(self.scroll, fg_color=WHITE)
        chart_frame.pack(fill="x", padx=20, pady=(0, 10))
        if not revenue:
            ctk.CTkLabel(
                chart_frame, text="No invoices yet. Monthly revenue will appear here after you create an invoice.",
                text_color=PINK_TEXT, wraplength=800
            ).pack(pady=20)
        else:
            labels = [_month_label(row["month"]) for row in revenue]
            amounts = [row["revenue"] for row in revenue]
            figure = Figure(figsize=(8.5, 3.4), dpi=100)
            figure.patch.set_facecolor(WHITE)
            axis = figure.add_subplot(111)
            axis.set_facecolor(WHITE)
            bars = axis.bar(labels, amounts, color="#F4A6C6", edgecolor="#C38699")
            axis.set_ylabel("Invoiced revenue (R)", color=PINK_TEXT, fontsize=9)
            axis.tick_params(axis="x", colors=PINK_TEXT, labelsize=8, rotation=35)
            axis.tick_params(axis="y", colors=PINK_TEXT, labelsize=8)
            for spine in axis.spines.values():
                spine.set_color(PINK)
            for bar, amount in zip(bars, amounts):
                axis.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    format_currency(amount), ha="center", va="bottom",
                    fontsize=6.5, color="#3A2A30"
                )
            figure.tight_layout()
            chart = FigureCanvasTkAgg(figure, master=chart_frame)
            chart.draw()
            chart.get_tk_widget().pack(fill="x")

        breakdown = ctk.CTkFrame(self.scroll, fg_color=WHITE)
        breakdown.pack(fill="x", padx=20, pady=(0, 12))
        if revenue:
            for month in revenue:
                row = ctk.CTkFrame(breakdown, fg_color=CARD_BG)
                row.pack(fill="x", pady=3)
                ctk.CTkLabel(
                    row, text=_month_label(month["month"]), text_color=PINK_TEXT
                ).pack(side="left", padx=15, pady=9)
                ctk.CTkLabel(
                    row, text=format_currency(month["revenue"]),
                    text_color=PINK_DARK, font=ctk.CTkFont(weight="bold")
                ).pack(side="right", padx=15)
        else:
            ctk.CTkLabel(
                breakdown, text="No monthly totals to display yet.",
                text_color=PINK_TEXT
            ).pack(pady=8)

        self._add_section_title("Best Customers by Invoiced Value")
        best_customers = stats["best_customers"]
        if not best_customers:
            ctk.CTkLabel(
                self.scroll, text="Customer rankings will appear after invoices have been created.",
                text_color=PINK_TEXT
            ).pack(anchor="w", padx=25, pady=(0, 20))
        else:
            for rank, customer in enumerate(best_customers, start=1):
                row = ctk.CTkFrame(self.scroll, fg_color=CARD_BG)
                row.pack(fill="x", padx=20, pady=3)
                ctk.CTkLabel(
                    row, text=f"{rank}. {customer['customer_name']}",
                    text_color=PINK_TEXT, anchor="w"
                ).pack(side="left", padx=15, pady=9)
                ctk.CTkLabel(
                    row, text=format_currency(customer["revenue"]),
                    text_color=PINK_DARK, font=ctk.CTkFont(weight="bold")
                ).pack(side="right", padx=15)

    def _add_section_title(self, text):
        ctk.CTkLabel(
            self.scroll, text=text,
            font=ctk.CTkFont(size=18, weight="bold"), text_color=PINK_DARK
        ).pack(anchor="w", padx=20, pady=(24, 10))

    def create_card(self, parent, title, value, row, column):
        card = ctk.CTkFrame(parent, width=260, height=100, fg_color=CARD_BG)
        card.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        card.grid_propagate(False)
        ctk.CTkLabel(
            card, text=title, text_color=PINK_TEXT, wraplength=235
        ).pack(pady=(14, 4))
        ctk.CTkLabel(
            card, text=value, font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PINK_DARK, wraplength=235
        ).pack()
