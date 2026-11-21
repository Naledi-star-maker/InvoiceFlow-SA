import calendar
import math
import sqlite3
from datetime import date

import customtkinter as ctk

from app.database.database import (
    add_payment,
    get_month_payment_summary,
    get_payments_for_invoice,
)
from app.theme import (
    BG,
    DANGER,
    FONT_SIZE,
    PINK,
    SECONDARY,
    SURFACE,
    SUCCESS,
    TEXT,
    card,
    data_table,
    font,
    labeled_entry,
    page_header,
    secondary_button,
    set_inline_error,
    stat_card,
    toast,
)
from app.utils import format_currency


STATUS_COLORS = {
    "Paid": SUCCESS,
    "Partly paid": "#D97706",
    "Unpaid": DANGER,
}


class PaymentsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        today = date.today()
        self._selected_filter = "All"
        self._summary = []

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)
        self.scroll.grid_columnconfigure(0, weight=1)
        page_header(
            self.scroll,
            "Payments",
            "Track payments received and outstanding invoice balances.",
        ).pack(fill="x", pady=(0, 16))

        period_card = card(self.scroll)
        period_card.pack(fill="x", pady=(0, 16))
        period_row = ctk.CTkFrame(period_card, fg_color="transparent")
        period_row.pack(fill="x", padx=16, pady=16)
        ctk.CTkLabel(
            period_row, text="Invoice month", text_color=SECONDARY,
            font=font(FONT_SIZE["label"], "bold"),
        ).pack(side="left", padx=(0, 10))
        month_values = [calendar.month_name[month] for month in range(1, 13)]
        self.month_selector = ctk.CTkOptionMenu(
            period_row, values=month_values, command=lambda _value: self.refresh(),
        )
        self.month_selector.set(calendar.month_name[today.month])
        self.month_selector.pack(side="left", padx=(0, 16))
        self.year_selector = ctk.CTkOptionMenu(
            period_row,
            values=[str(year) for year in range(2000, today.year + 2)],
            command=lambda _value: self.refresh(),
        )
        self.year_selector.set(str(today.year))
        self.year_selector.pack(side="left")

        self.summary_cards = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.summary_cards.pack(fill="x", pady=(0, 8))
        for column in range(3):
            self.summary_cards.grid_columnconfigure(column, weight=1)

        filter_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        filter_row.pack(fill="x", pady=(0, 8))
        self.filter_buttons = {}
        for label in ("All", "Paid", "Unpaid"):
            button = secondary_button(
                filter_row, label, command=lambda value=label: self._set_filter(value),
                width=100, height=34,
            )
            button.pack(side="left", padx=(0, 8))
            self.filter_buttons[label] = button
        self._update_filter_buttons()

        self.table_card = card(self.scroll)
        self.table_card.pack(fill="x")
        self.refresh()

    def refresh(self):
        year = int(self.year_selector.get())
        month = list(calendar.month_name).index(self.month_selector.get())
        self._summary = get_month_payment_summary(year, month)
        self._render_summary_cards()
        self._render_table()

    def _render_summary_cards(self):
        for child in self.summary_cards.winfo_children():
            child.destroy()

        total_invoiced = sum(row["total"] for row in self._summary)
        total_received = sum(row["amount_paid"] for row in self._summary)
        outstanding = sum(row["balance"] for row in self._summary)
        values = (
            ("Total invoiced", total_invoiced, PINK),
            ("Total received", total_received, SUCCESS),
            ("Outstanding", outstanding, DANGER),
        )
        month_caption = (
            f"{self.month_selector.get()} "
            f"{self.year_selector.get()}"
        )
        for column, (label, amount, accent) in enumerate(values):
            stat_card(
                self.summary_cards, label, format_currency(amount),
                month_caption,
                accent=accent,
            ).grid(row=0, column=column, sticky="ew", padx=(0, 12))

    def _render_table(self):
        for child in self.table_card.winfo_children():
            child.destroy()

        rows = [
            row for row in self._summary
            if self._selected_filter == "All"
            or (
                self._selected_filter == "Paid" and row["status"] == "Paid"
            )
            or (
                self._selected_filter == "Unpaid" and row["status"] != "Paid"
            )
        ]
        columns = (
            {"label": "Customer", "weight": 2},
            {"label": "Invoice number", "weight": 2},
            {"label": "Total", "weight": 1, "anchor": "e"},
            {"label": "Paid", "weight": 1, "anchor": "e"},
            {"label": "Balance", "weight": 1, "anchor": "e"},
            {"label": "Status", "weight": 1},
        )
        table = data_table(
            self.table_card,
            columns,
            [
                (
                    row["customer_name"],
                    row["invoice_number"],
                    format_currency(row["total"]),
                    format_currency(row["amount_paid"]),
                    format_currency(row["balance"]),
                    row["status"],
                )
                for row in rows
            ],
            empty_text="No invoices match this month and filter.",
            row_command=lambda index: self._open_payment_dialog(rows[index]),
        )
        table.pack(fill="x")
        for table_row in table.winfo_children()[1:]:
            labels = table_row.winfo_children()
            if len(labels) == len(columns):
                status = labels[-1].cget("text")
                labels[-1].configure(text_color=STATUS_COLORS[status])

    def _set_filter(self, value):
        self._selected_filter = value
        self._update_filter_buttons()
        self._render_table()

    def _update_filter_buttons(self):
        for label, button in self.filter_buttons.items():
            selected = label == self._selected_filter
            button.configure(
                fg_color=PINK if selected else SURFACE,
                hover_color="#BE185D" if selected else "#F4F4F5",
                text_color=SURFACE if selected else TEXT,
            )

    def _open_payment_dialog(self, invoice):
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Payments - {invoice['invoice_number']}")
        dialog.geometry("480x620")
        dialog.minsize(440, 500)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            dialog,
            text=invoice["invoice_number"],
            text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))
        ctk.CTkLabel(
            dialog,
            text=(
                f"{invoice['customer_name']}  ·  "
                f"Balance: {format_currency(invoice['balance'])}"
            ),
            text_color=SECONDARY,
            font=font(FONT_SIZE["body"]),
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 12))

        history_card = card(dialog)
        history_card.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 12))
        ctk.CTkLabel(
            history_card, text="Payment history", text_color=TEXT,
            font=font(FONT_SIZE["label"], "bold"),
        ).pack(anchor="w", padx=12, pady=(12, 4))
        history = ctk.CTkScrollableFrame(history_card, fg_color=SURFACE, height=120)
        history.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        payments = get_payments_for_invoice(invoice["invoice_id"])
        if payments:
            for payment in payments:
                details = f"{payment['payment_date']}  ·  {format_currency(payment['amount'])}"
                if payment["note"]:
                    details += f"\n{payment['note']}"
                ctk.CTkLabel(
                    history, text=details, text_color=SECONDARY, anchor="w",
                    justify="left", font=font(FONT_SIZE["small"]),
                ).pack(fill="x", padx=8, pady=6)
        else:
            ctk.CTkLabel(
                history, text="No payments recorded yet.", text_color=SECONDARY,
                font=font(FONT_SIZE["small"]),
            ).pack(anchor="w", padx=8, pady=8)

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.grid(row=3, column=0, sticky="ew", padx=20)
        amount_entry = labeled_entry(form, "Amount (R)")
        amount_entry.field_container.pack(fill="x", pady=(0, 10))
        amount_entry.insert(0, f"{invoice['balance']:.2f}")
        date_entry = labeled_entry(form, "Payment date", placeholder="YYYY-MM-DD")
        date_entry.field_container.pack(fill="x", pady=(0, 10))
        date_entry.insert(0, date.today().isoformat())
        note_entry = labeled_entry(form, "Note (optional)")
        note_entry.field_container.pack(fill="x", pady=(0, 8))

        actions = ctk.CTkFrame(dialog, fg_color="transparent")
        actions.grid(row=4, column=0, sticky="e", padx=20, pady=(8, 20))
        secondary_button(
            actions, "Cancel", command=dialog.destroy, width=90, height=36,
        ).pack(side="left", padx=(0, 8))

        def save_payment():
            try:
                amount = float(amount_entry.get())
            except ValueError:
                set_inline_error(amount_entry, "Enter a valid payment amount.")
                return
            if not math.isfinite(amount) or amount <= 0:
                set_inline_error(amount_entry, "Amount must be greater than zero.")
                return
            if amount > invoice["balance"] + 0.000001:
                set_inline_error(
                    amount_entry, "Payment cannot exceed the remaining balance."
                )
                return
            set_inline_error(amount_entry, "")

            payment_date = date_entry.get().strip()
            try:
                parsed_date = date.fromisoformat(payment_date)
                if parsed_date.isoformat() != payment_date:
                    raise ValueError("Use YYYY-MM-DD format.")
            except ValueError:
                set_inline_error(
                    date_entry, "Enter a valid date in YYYY-MM-DD format."
                )
                return
            set_inline_error(date_entry, "")

            try:
                add_payment(
                    invoice["invoice_id"], amount, payment_date,
                    note_entry.get().strip(),
                )
            except (ValueError, sqlite3.Error) as error:
                toast(dialog, f"Payment could not be saved: {error}", "error")
                return

            dialog.destroy()
            self.refresh()
            toast(self, "Payment recorded.", "success")

        secondary_button(
            actions, "Record payment", command=save_payment,
            width=140, height=36,
        ).pack(side="left")
