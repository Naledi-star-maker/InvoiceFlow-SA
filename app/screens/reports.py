from datetime import datetime

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.database.database import get_business_statistics, get_total_customers
from app.theme import (
    BG,
    BORDER,
    FONT_SIZE,
    PINK,
    SECONDARY,
    SURFACE,
    TEXT,
    card,
    data_table,
    empty_state,
    font,
    page_header,
    stat_card,
)
from app.utils import format_currency


def _month_label(month):
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%B %Y")
    except ValueError:
        return month


class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        self._columns = 3
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.scroll.bind("<Configure>", self._responsive_cards)
        self.refresh()

    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()
        page_header(
            self.scroll,
            "Business reports",
            "Revenue is based on invoice totals; it is not money received or profit.",
        ).pack(fill="x", pady=(0, 20))

        self.stats = get_business_statistics()
        cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 24))
        self.cards_frame = cards_frame
        values = (
            ("This month's invoiced revenue", format_currency(self.stats["current_month_revenue"])),
            ("Year-to-date revenue", format_currency(self.stats["year_to_date_revenue"])),
            ("Total invoices", str(self.stats["total_invoices"])),
            ("Average invoice value", format_currency(self.stats["average_invoice_value"])),
            ("Customers", str(get_total_customers())),
        )
        self._render_cards(values)

        self._section_heading(self.scroll, "Monthly invoiced revenue")
        chart_card = card(self.scroll)
        chart_card.pack(fill="x", pady=(0, 20))
        monthly = self.stats["monthly_revenue"]
        if not monthly:
            empty_state(
                chart_card,
                "Monthly revenue will appear here after you create an invoice.",
            )
        else:
            self._render_chart(chart_card, monthly)

        self._section_heading(self.scroll, "Monthly breakdown")
        breakdown_card = card(self.scroll)
        breakdown_card.pack(fill="x", pady=(0, 20))
        if monthly:
            data_table(
                breakdown_card,
                [
                    {"label": "Month", "weight": 2},
                    {"label": "Invoiced revenue", "weight": 1, "anchor": "e"},
                ],
                [
                    (_month_label(row["month"]), format_currency(row["revenue"]))
                    for row in monthly
                ],
                empty_text="No monthly totals to display yet.",
            ).pack(fill="x", padx=8, pady=8)
        else:
            empty_state(breakdown_card, "No monthly totals to display yet.")

        self._section_heading(self.scroll, "Best customers by invoiced value")
        customers_card = card(self.scroll)
        customers_card.pack(fill="x")
        best_customers = self.stats["best_customers"]
        if best_customers:
            data_table(
                customers_card,
                [
                    {"label": "Customer", "weight": 2},
                    {"label": "Invoiced revenue", "weight": 1, "anchor": "e"},
                ],
                [
                    (customer["customer_name"], format_currency(customer["revenue"]))
                    for customer in best_customers
                ],
            ).pack(fill="x", padx=8, pady=8)
        else:
            empty_state(
                customers_card,
                "Customer rankings will appear after invoices have been created.",
            )

        self._section_heading(self.scroll, "Month-over-month")
        percentage = self.stats["percentage_change"]
        if percentage is None:
            caption, accent = "No previous-month baseline", SECONDARY
        else:
            caption = f"{percentage:+.1f}% compared with the previous month"
            accent = "#16A34A" if percentage >= 0 else "#DC2626"
        comparison = stat_card(
            self.scroll,
            "Change in invoiced revenue",
            caption,
            "Compared with previous month",
            accent=accent,
        )
        comparison.pack(fill="x")

    def _render_cards(self, values):
        for child in self.cards_frame.winfo_children():
            child.destroy()
        columns = max(self._columns, 2)
        for column in range(columns):
            self.cards_frame.grid_columnconfigure(column, weight=1)
        for index, (label, value) in enumerate(values):
            tile = stat_card(
                self.cards_frame, label, value, "Invoiced revenue where applicable",
                width=240, height=116,
            )
            tile.grid(
                row=index // columns, column=index % columns,
                sticky="ew", padx=(0, 12), pady=(0, 12),
            )

    def _responsive_cards(self, event):
        if not hasattr(self, "cards_frame"):
            return
        columns = 3 if event.width >= 900 else 2
        if columns != self._columns:
            self._columns = columns
            values = (
                ("This month's invoiced revenue", format_currency(self.stats["current_month_revenue"])),
                ("Year-to-date revenue", format_currency(self.stats["year_to_date_revenue"])),
                ("Total invoices", str(self.stats["total_invoices"])),
                ("Average invoice value", format_currency(self.stats["average_invoice_value"])),
                ("Customers", str(get_total_customers())),
            )
            self._render_cards(values)

    @staticmethod
    def _section_heading(parent, title):
        ctk.CTkLabel(
            parent, text=title, text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"), anchor="w",
        ).pack(fill="x", pady=(20, 8))

    @staticmethod
    def _render_chart(parent, monthly):
        chart_frame = ctk.CTkFrame(parent, fg_color=SURFACE)
        chart_frame.pack(fill="x", padx=12, pady=12)
        figure = Figure(figsize=(8.8, 3.2), dpi=100)
        figure.patch.set_facecolor(SURFACE)
        axis = figure.add_subplot(111)
        axis.set_facecolor(SURFACE)
        labels = [_month_label(row["month"]) for row in monthly]
        amounts = [row["revenue"] for row in monthly]
        axis.bar(labels, amounts, color=PINK, width=0.58)
        axis.grid(axis="y", color=BORDER, linewidth=0.7)
        axis.set_axisbelow(True)
        axis.set_ylabel("Invoiced revenue (R)", color=SECONDARY, fontsize=9)
        axis.tick_params(axis="x", colors=SECONDARY, labelsize=8, rotation=35)
        axis.tick_params(axis="y", colors=SECONDARY, labelsize=8)
        for spine in axis.spines.values():
            spine.set_visible(False)
        figure.tight_layout()
        chart = FigureCanvasTkAgg(figure, master=chart_frame)
        chart.draw()
        chart.get_tk_widget().pack(fill="x")
        def resize_chart(event):
            figure.set_size_inches(max(event.width / 100, 4), 3.2, forward=True)
            chart.draw_idle()

        chart_frame.bind("<Configure>", resize_chart)
