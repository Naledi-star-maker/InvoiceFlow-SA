import calendar
import math
import sqlite3
from datetime import date

import customtkinter as ctk

from app.database.database import get_all_customers
from app.services.invoice_service import calculate_totals, create_invoice
from app.services.pdf_generator import generate_invoice_pdf
from app.theme import (
    BG,
    BORDER,
    DANGER,
    FONT_SIZE,
    SECONDARY,
    SURFACE,
    TEXT,
    card,
    labeled_dropdown,
    labeled_entry,
    page_header,
    primary_button,
    secondary_button,
    set_inline_error,
    toast,
    font,
)


class _DatePickerDialog(ctk.CTkToplevel):
    def __init__(self, parent, initial_date, on_select):
        super().__init__(parent)
        self.on_select = on_select
        self.title("Choose invoice date")
        self.geometry("360x410")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)
        ctk.CTkLabel(
            content, text="Choose invoice date", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", pady=(0, 12))

        selectors = ctk.CTkFrame(content, fg_color="transparent")
        selectors.pack(fill="x", pady=(0, 10))
        selectors.grid_columnconfigure((0, 1), weight=1)
        self.month_selector = ctk.CTkOptionMenu(
            selectors,
            values=[calendar.month_name[month] for month in range(1, 13)],
            command=lambda _value: self._render_days(),
        )
        self.month_selector.set(calendar.month_name[initial_date.month])
        self.month_selector.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.year_selector = ctk.CTkOptionMenu(
            selectors,
            values=[str(year) for year in range(1900, 2101)],
            command=lambda _value: self._render_days(),
        )
        self.year_selector.set(str(initial_date.year))
        self.year_selector.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.day_grid = ctk.CTkFrame(content, fg_color="transparent")
        self.day_grid.pack(fill="both", expand=True)
        for column, weekday in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")):
            self.day_grid.grid_columnconfigure(column, weight=1)
            ctk.CTkLabel(
                self.day_grid, text=weekday, text_color=SECONDARY,
                font=font(FONT_SIZE["small"], "bold"),
            ).grid(row=0, column=column, pady=(0, 4))

        secondary_button(
            content, "Cancel", command=self.destroy, width=90, height=32,
        ).pack(anchor="e", pady=(8, 0))
        self._render_days()

    def _render_days(self):
        for child in self.day_grid.winfo_children():
            if int(child.grid_info().get("row", 0)) > 0:
                child.destroy()

        month = list(calendar.month_name).index(self.month_selector.get())
        year = int(self.year_selector.get())
        for week_index, week in enumerate(calendar.monthcalendar(year, month), start=1):
            for weekday, day in enumerate(week):
                if day:
                    secondary_button(
                        self.day_grid,
                        str(day),
                        command=lambda selected_day=day: self._select_day(
                            year, month, selected_day
                        ),
                        width=34,
                        height=32,
                    ).grid(
                        row=week_index, column=weekday, padx=2, pady=2,
                        sticky="nsew",
                    )

    def _select_day(self, year, month, day):
        self.on_select(date(year, month, day).isoformat())
        self.destroy()


class InvoiceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        self.item_rows = []
        self.customers = []

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=(24, 0))
        self.scroll.grid_columnconfigure(0, weight=1)
        page_header(
            self.scroll,
            "New invoice",
            "Create an invoice with a customer and one or more line items.",
        ).pack(fill="x", pady=(0, 20))

        customer_card = card(self.scroll)
        customer_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            customer_card, text="Customer", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        customer_row = ctk.CTkFrame(customer_card, fg_color="transparent")
        customer_row.pack(fill="x", padx=16, pady=(0, 16))
        customer_row.grid_columnconfigure(0, weight=1)
        self.customer_dropdown = labeled_dropdown(
            customer_row, "Select a customer *", ["No customers yet"]
        )
        self.customer_dropdown.field_container.grid(
            row=0, column=0, sticky="ew", padx=(0, 12)
        )
        secondary_button(
            customer_row, "Refresh customers", command=self.refresh_customers,
            width=150, height=38,
        ).grid(row=0, column=1, sticky="e", pady=(22, 0))
        self.customer_error = ctk.CTkLabel(
            customer_card, text="", text_color=DANGER, font=font(FONT_SIZE["small"])
        )
        self.customer_error.pack(anchor="w", padx=16, pady=(0, 12))

        items_card = card(self.scroll)
        items_card.pack(fill="x", pady=(0, 16))
        section_header = ctk.CTkFrame(items_card, fg_color="transparent")
        section_header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            section_header, text="Line items", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(side="left")
        secondary_button(
            section_header, "+ Add item", command=self.add_item_row,
            height=34,
        ).pack(side="right")

        self.items_scroll = ctk.CTkScrollableFrame(
            items_card, fg_color=SURFACE, height=220,
        )
        self.items_scroll.pack(fill="x", padx=12, pady=(0, 4))
        self.items_error = ctk.CTkLabel(
            items_card, text="", text_color=DANGER, font=font(FONT_SIZE["small"])
        )
        self.items_error.pack(anchor="w", padx=16, pady=(0, 8))

        notes_card = card(self.scroll)
        notes_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            notes_card, text="Notes", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.notes_entry = labeled_entry(
            notes_card, "Optional note for this invoice",
            placeholder="Add a short note",
        )
        self.notes_entry.field_container.pack(fill="x", padx=16, pady=(0, 16))

        invoice_date_card = card(self.scroll)
        invoice_date_card.pack(fill="x", pady=(0, 16))
        self.invoice_date_entry = labeled_entry(
            invoice_date_card, "Invoice date *", placeholder="Choose a date",
            state="readonly",
        )
        self.invoice_date_entry.field_container.pack(
            fill="x", padx=16, pady=16
        )
        secondary_button(
            self.invoice_date_entry.field_container, "Choose date",
            command=self._open_invoice_date_picker, width=120, height=32,
        ).pack(anchor="e", pady=(8, 0))

        self.footer = ctk.CTkFrame(self, fg_color=SURFACE, border_color=BORDER, border_width=1)
        self.footer.pack(fill="x", side="bottom")
        footer_inner = ctk.CTkFrame(self.footer, fg_color="transparent")
        footer_inner.pack(fill="x", padx=24, pady=12)
        self.totals_label = ctk.CTkLabel(
            footer_inner, text="Total: R 0.00", text_color=TEXT,
            font=font(FONT_SIZE["title"], "bold"),
        )
        self.totals_label.pack(side="left")
        self.subtotal_label = ctk.CTkLabel(
            footer_inner, text="Subtotal: R 0.00  ·  VAT: R 0.00",
            text_color=SECONDARY, font=font(FONT_SIZE["small"]),
        )
        self.subtotal_label.pack(side="left", padx=16)
        self.create_button = primary_button(
            footer_inner, "Create invoice", command=self.handle_create,
            width=160, height=42,
        )
        self.create_button.pack(side="right")

        self.add_item_row()
        self.refresh()

    def refresh(self):
        self.refresh_customers()

    def refresh_customers(self):
        self.customers = get_all_customers()
        customer_names = [customer["customer_name"] for customer in self.customers]
        self.customer_dropdown.configure(
            values=customer_names or ["No customers yet — add one first"]
        )
        self.customer_dropdown.set(
            customer_names[0] if customer_names else "No customers yet — add one first"
        )

    def _open_invoice_date_picker(self):
        try:
            initial_date = date.fromisoformat(self.invoice_date_entry.get())
        except ValueError:
            initial_date = date.today()
        _DatePickerDialog(self, initial_date, self._set_invoice_date)

    def _set_invoice_date(self, value):
        self.invoice_date_entry.configure(state="normal")
        self.invoice_date_entry.delete(0, "end")
        if value:
            self.invoice_date_entry.insert(0, value)
        self.invoice_date_entry.configure(state="readonly")
        set_inline_error(self.invoice_date_entry, "")

    def add_item_row(self):
        row_frame = ctk.CTkFrame(self.items_scroll, fg_color=SURFACE)
        row_frame.pack(fill="x", pady=4, padx=4)
        row_frame.grid_columnconfigure(0, weight=5)
        row_frame.grid_columnconfigure(1, weight=2)

        description = labeled_entry(row_frame, "Description")
        description.field_container.grid(
            row=0, column=0, sticky="ew", padx=(8, 8), pady=8
        )
        price = labeled_entry(row_frame, "Amount (R)")
        price.field_container.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
        price.insert(0, "0")
        line_total_label = ctk.CTkLabel(
            row_frame, text="R 0.00", text_color=TEXT,
            font=font(FONT_SIZE["body"], "bold"), anchor="e",
        )
        line_total_label.grid(row=0, column=2, padx=8, pady=(28, 8), sticky="e")
        remove_button = ctk.CTkButton(
            row_frame, text="×", width=34, height=34,
            fg_color="transparent", hover_color="#F4F4F5",
            text_color=SECONDARY, corner_radius=8,
            command=lambda: self.remove_item_row(row_data),
        )
        remove_button.grid(row=0, column=3, padx=8, pady=(24, 8))

        row_data = {
            "frame": row_frame,
            "description": description,
            "price": price,
            "line_total_label": line_total_label,
        }
        price.bind("<KeyRelease>", lambda _event: self.update_totals())
        self.item_rows.append(row_data)
        self.update_totals()

    def remove_item_row(self, row_data):
        if len(self.item_rows) == 1:
            self.items_error.configure(text="An invoice needs at least one item row.")
            return
        row_data["frame"].destroy()
        self.item_rows.remove(row_data)
        self.items_error.configure(text="")
        self.update_totals()

    def _collect_items(self):
        items = []
        for row in self.item_rows:
            description = row["description"].get().strip()
            if not description:
                continue
            try:
                price = float(row["price"].get())
            except ValueError:
                price = 0
            row["line_total_label"].configure(text=f"R {price:,.2f}")
            items.append(
                {"description": description, "quantity": 1, "unit_price": price}
            )
        return items

    def update_totals(self):
        items = self._collect_items()
        totals = calculate_totals(items)
        self.subtotal_label.configure(
            text=f"Subtotal: R {totals['subtotal']:,.2f}  ·  VAT: R 0.00"
        )
        self.totals_label.configure(text=f"Total: R {totals['total']:,.2f}")

    def handle_create(self):
        invoice_date = self.invoice_date_entry.get().strip()
        try:
            parsed_invoice_date = date.fromisoformat(invoice_date)
        except ValueError:
            parsed_invoice_date = None
        if parsed_invoice_date is None or parsed_invoice_date.isoformat() != invoice_date:
            set_inline_error(self.invoice_date_entry, "Choose a valid invoice date.")
            return
        set_inline_error(self.invoice_date_entry, "")

        selected_name = self.customer_dropdown.get()
        customer = next(
            (item for item in self.customers if item["customer_name"] == selected_name),
            None,
        )
        if customer is None:
            self.customer_error.configure(text="Select a valid customer to continue.")
            return
        self.customer_error.configure(text="")

        items = self._collect_items()
        if not items:
            self.items_error.configure(text="Add at least one item with a description.")
            return
        invalid_row = next(
            (
                row for row in self.item_rows
                if row["description"].get().strip()
                and not self._is_nonnegative_number(row["price"].get())
            ),
            None,
        )
        if invalid_row is not None:
            self.items_error.configure(
                text="Enter a valid non-negative amount."
            )
            set_inline_error(invalid_row["price"], "Enter a valid non-negative amount.")
            return
        self.items_error.configure(text="")

        try:
            invoice_id = create_invoice(
                customer["id"], items, self.notes_entry.get().strip(),
                invoice_date=invoice_date,
            )
        except (ValueError, sqlite3.Error) as error:
            self.items_error.configure(text=f"Invoice could not be saved: {error}")
            return

        try:
            pdf_path = generate_invoice_pdf(invoice_id)
        except (OSError, ValueError) as error:
            toast(
                self, f"Invoice saved, but PDF could not be created: {error}", "error"
            )
        else:
            toast(self, f"Invoice created. PDF saved to {pdf_path}.", "success")

        self._reset_form()
        self._refresh_invoice_surfaces()

    @staticmethod
    def _is_nonnegative_number(value):
        try:
            number = float(value)
            return math.isfinite(number) and number >= 0
        except ValueError:
            return False

    def _reset_form(self):
        for row in self.item_rows[1:]:
            row["frame"].destroy()
        self.item_rows = self.item_rows[:1]
        for key in ("description", "price"):
            self.item_rows[0][key].delete(0, "end")
        self.item_rows[0]["price"].insert(0, "0")
        self.notes_entry.delete(0, "end")
        self._set_invoice_date("")
        self.customer_error.configure(text="")
        self.items_error.configure(text="")
        self.update_totals()

    def _refresh_invoice_surfaces(self):
        for key in (
            "dashboard", "reports", "manage_invoices", "payments", "budget",
        ):
            frame = self.controller.frames.get(key)
            if frame is not None and hasattr(frame, "refresh"):
                frame.refresh()
