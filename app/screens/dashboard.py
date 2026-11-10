from datetime import date, datetime

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.database.database import (
    get_all_invoices,
    get_business_statistics,
    get_company_info,
    get_total_customers,
)
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
    secondary_button,
    stat_card,
)
from app.utils import format_currency


def _month_label(month):
    try:
        return datetime.strptime(month, "%Y-%m").strftime("%b %y")
    except ValueError:
        return month


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        self._chart = None
        self._stats = None
        self._invoices = []
        self._columns = 4

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)
        self.scroll.grid_columnconfigure(0, weight=1)

        def add_header_action(actions):
            self.new_invoice_button = ctk.CTkButton(
                actions,
                text="+ New Invoice",
                command=lambda: controller.show_frame("invoices"),
                fg_color=PINK,
                hover_color="#BE185D",
                text_color=SURFACE,
                corner_radius=8,
                height=40,
                font=font(FONT_SIZE["body"], "bold"),
            )
            self.new_invoice_button.pack()

        self.header = page_header(
            self.scroll, "", "", actions=add_header_action
        )
        self.header.pack(fill="x", pady=(0, 20))

        self.cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=(0, 24))

        self.chart_card = card(self.scroll)
        ctk.CTkLabel(
            self.chart_card,
            text="Revenue trend",
            text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 0))
        self.chart_body = ctk.CTkFrame(self.chart_card, fg_color=SURFACE)
        self.chart_body.pack(fill="x", padx=12, pady=(4, 12))
        self.chart_body.bind("<Configure>", self._resize_chart)
        self.chart_card.pack(fill="x", pady=(0, 24))

        self.recent_card = card(self.scroll)
        recent_heading = ctk.CTkFrame(self.recent_card, fg_color="transparent")
        recent_heading.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            recent_heading,
            text="Recent invoices",
            text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(side="left")
        secondary_button(
            recent_heading, "Manage invoices",
            command=lambda: controller.show_frame("manage_invoices"),
            height=34,
        ).pack(side="right")
        self.recent_body = ctk.CTkFrame(self.recent_card, fg_color=SURFACE)
        self.recent_body.pack(fill="x", padx=8, pady=(0, 8))
        self.recent_card.pack(fill="x")

        actions_card = card(self.scroll)
        ctk.CTkLabel(
            actions_card, text="Quick actions", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        quick_actions = ctk.CTkFrame(actions_card, fg_color="transparent")
        quick_actions.pack(fill="x", padx=12, pady=(0, 12))
        for label, key in (
            ("Manage invoices", "manage_invoices"),
            ("Customers", "customers"),
            ("Reports", "reports"),
        ):
            secondary_button(
                quick_actions, label, command=lambda target=key: controller.show_frame(target),
                height=36,
            ).pack(side="left", padx=4)
        actions_card.pack(fill="x", pady=(24, 0))
        self.scroll.bind("<Configure>", self._responsive_cards)
        self.refresh()

    def refresh(self):
        company = get_company_info()
        business_name = company["business_name"] if company else "Your Business"
        today = date.today().strftime("%A, %d %B %Y")
        self.header.winfo_children()[0].winfo_children()[0].configure(
            text=f"Welcome back, {business_name}"
        )
        title_block = self.header.winfo_children()[0]
        subtitle_label = title_block.winfo_children()[1] if len(title_block.winfo_children()) > 1 else None
        if subtitle_label is None:
            ctk.CTkLabel(
                title_block, text=today, text_color=SECONDARY,
                font=font(FONT_SIZE["body"]), anchor="w",
            ).pack(anchor="w", pady=(4, 0))
        else:
            subtitle_label.configure(text=today)

        self._stats = get_business_statistics()
        self._invoices = get_all_invoices()[:8]
        self._render_stats()
        self._render_chart()
        self._render_recent()

    def _responsive_cards(self, event):
        columns = 4 if event.width >= 900 else 2
        if columns != self._columns:
            self._columns = columns
            self._render_stats()

    def _render_stats(self):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        if self._stats is None:
            return
        for column in range(max(self._columns, 2)):
            self.cards_frame.grid_columnconfigure(column, weight=1)

        percentage = self._stats["percentage_change"]
        if percentage is None:
            change_caption, change_color = "No previous-month baseline", None
        else:
            change_caption = f"{percentage:+.1f}% vs. previous month"
            change_color = "#16A34A" if percentage >= 0 else "#DC2626"
        values = (
            ("This month's invoiced revenue", format_currency(self._stats["current_month_revenue"]),
             change_caption, change_color),
            ("Year-to-date revenue", format_currency(self._stats["year_to_date_revenue"]),
             "Invoiced revenue, not received", None),
            ("Total invoices", str(self._stats["total_invoices"]), "All recorded invoices", None),
            ("Average invoice value", format_currency(self._stats["average_invoice_value"]),
             "Based on recorded invoices", None),
            ("Customers", str(get_total_customers()), "Customer records", None),
        )
        for index, (label, value, caption, color) in enumerate(values):
            tile = stat_card(
                self.cards_frame, label, value, caption, accent=TEXT,
                width=190, height=116,
            )
            tile.grid(
                row=index // self._columns,
                column=index % self._columns,
                sticky="ew",
                padx=(0, 12),
                pady=(0, 12),
            )
            if color:
                inner = tile.winfo_children()[0]
                inner.winfo_children()[-1].destroy()
                caption_row = ctk.CTkFrame(inner, fg_color="transparent")
                caption_row.pack(fill="x", pady=(4, 0))
                ctk.CTkFrame(
                    caption_row, width=6, height=6, fg_color=color,
                    corner_radius=3,
                ).pack(side="left", padx=(0, 6), pady=4)
                ctk.CTkLabel(
                    caption_row, text=caption, text_color=SECONDARY,
                    font=font(FONT_SIZE["small"]), anchor="w",
                ).pack(side="left", fill="x", expand=True)

    def _render_chart(self):
        for widget in self.chart_body.winfo_children():
            widget.destroy()

        monthly = self._stats["monthly_revenue"] if self._stats else []
        if not monthly:
            empty_state(
                self.chart_body,
                "Monthly revenue will appear here after you create an invoice.",
                "Create invoice",
                lambda: self.controller.show_frame("invoices"),
            )
            return

        chart_width = max(self.chart_body.winfo_width(), 640)
        figure = Figure(figsize=(chart_width / 100, 2.4), dpi=100)
        figure.patch.set_facecolor(SURFACE)
        axis = figure.add_subplot(111)
        axis.set_facecolor(SURFACE)
        labels = [_month_label(row["month"]) for row in monthly]
        amounts = [row["revenue"] for row in monthly]
        axis.bar(labels, amounts, color=PINK, width=0.58)
        axis.grid(axis="y", color=BORDER, linewidth=0.7)
        axis.set_axisbelow(True)
        axis.tick_params(axis="x", colors=SECONDARY, labelsize=9, rotation=30)
        axis.tick_params(axis="y", colors=SECONDARY, labelsize=9)
        axis.set_ylabel("Invoiced revenue (R)", color=SECONDARY, fontsize=9)
        for spine in axis.spines.values():
            spine.set_visible(False)
        figure.tight_layout()
        self._figure = figure
        self._chart = FigureCanvasTkAgg(figure, master=self.chart_body)
        self._chart.draw()
        self._chart.get_tk_widget().pack(fill="x")

    def _resize_chart(self, _event):
        if self._chart is None or self.chart_body.winfo_width() < 2:
            return
        self._figure.set_size_inches(
            max(self.chart_body.winfo_width() / 100, 4), 2.4, forward=True
        )
        self._chart.draw_idle()

    def _render_recent(self):
        for widget in self.recent_body.winfo_children():
            widget.destroy()
        if not self._invoices:
            empty_state(
                self.recent_body,
                "No invoices yet. Create your first invoice to get started.",
                "Create invoice",
                lambda: self.controller.show_frame("invoices"),
            )
            return
        columns = [
            {"label": "Invoice number", "weight": 2},
            {"label": "Customer", "weight": 2},
            {"label": "Date", "weight": 1},
            {"label": "Total", "weight": 1, "anchor": "e"},
        ]
        rows = [
            (
                invoice["invoice_number"],
                invoice["customer_name"],
                invoice["invoice_date"],
                format_currency(invoice["total"]),
            )
            for invoice in self._invoices
        ]
        data_table(self.recent_body, columns, rows).pack(fill="x")
