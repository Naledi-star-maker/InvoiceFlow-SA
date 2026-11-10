import math
import sqlite3

import customtkinter as ctk

from app.database.database import (
    get_all_invoices,
    get_customer_by_id,
    get_invoice_by_id,
    search_invoices,
)
from app.services.invoice_service import calculate_totals, duplicate_invoice
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
    empty_state,
    font,
    labeled_entry,
    page_header,
    primary_button,
    secondary_button,
    toast,
)
from app.utils import format_currency


class ManageInvoiceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        self.item_rows = []
        self.selected_invoice_id = None
        self.selected_customer_id = None

        page_header(
            self,
            "Manage invoices",
            "Reuse a past invoice as a starting point. Regenerating creates a new invoice; the original stays unchanged.",
        ).pack(fill="x", padx=24, pady=(24, 16))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=1, minsize=250)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        self.left_panel = card(body)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ctk.CTkLabel(
            self.left_panel, text="Invoice history", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.search_entry = ctk.CTkEntry(
            self.left_panel,
            placeholder_text="Search number, customer, or date",
            height=38,
            border_color=BORDER,
            text_color=TEXT,
            placeholder_text_color=SECONDARY,
            corner_radius=8,
            font=font(FONT_SIZE["body"]),
        )
        self.search_entry.pack(fill="x", padx=12, pady=(0, 12))
        self.search_entry.bind(
            "<KeyRelease>", lambda _event: self.load_invoice_list(self.search_entry.get())
        )
        self.list_scroll = ctk.CTkScrollableFrame(
            self.left_panel, fg_color=SURFACE,
        )
        self.list_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.right_panel = ctk.CTkFrame(body, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.detail_card = card(self.right_panel)
        self.detail_card.pack(fill="both", expand=True)
        self.selected_label = ctk.CTkLabel(
            self.detail_card, text="Select an invoice to reuse",
            text_color=TEXT, font=font(FONT_SIZE["heading"], "bold"),
            anchor="w", wraplength=600,
        )
        self.selected_label.pack(fill="x", padx=16, pady=(16, 12))

        self.items_scroll = ctk.CTkScrollableFrame(
            self.detail_card, fg_color=SURFACE, height=260,
        )
        self.items_scroll.pack(fill="both", expand=True, padx=12, pady=4)
        self.status_label = ctk.CTkLabel(
            self.detail_card, text="", text_color=DANGER,
            font=font(FONT_SIZE["small"]), anchor="w", justify="left",
        )
        self.status_label.pack(fill="x", padx=16, pady=(4, 0))

        detail_footer = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        detail_footer.pack(fill="x", padx=16, pady=12)
        secondary_button(
            detail_footer, "+ Add item", command=self.add_item_row,
            height=36,
        ).pack(side="left")
        self.totals_label = ctk.CTkLabel(
            detail_footer, text="Total: R 0.00", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        )
        self.totals_label.pack(side="right", padx=(12, 0))

        notes_card = card(self.right_panel)
        notes_card.pack(fill="x", pady=(12, 0))
        self.notes_entry = labeled_entry(
            notes_card, "Notes", placeholder="Optional note for this invoice"
        )
        self.notes_entry.field_container.pack(fill="x", padx=16, pady=12)
        self.regenerate_button = primary_button(
            self.right_panel, "Regenerate invoice",
            command=self.handle_regenerate,
            height=42, state="disabled",
        )
        self.regenerate_button.pack(fill="x", pady=(12, 0))
        self.refresh()

    def refresh(self):
        self.load_invoice_list()

    def load_invoice_list(self, keyword=""):
        for widget in self.list_scroll.winfo_children():
            widget.destroy()
        invoices = search_invoices(keyword) if keyword.strip() else get_all_invoices()
        if not invoices:
            empty_state(self.list_scroll, "No invoices found.")
            return

        for invoice in invoices:
            row = ctk.CTkFrame(
                self.list_scroll, fg_color=SURFACE, corner_radius=8,
                border_color=BORDER, border_width=1,
            )
            row.pack(fill="x", pady=4, padx=2)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(fill="x", padx=12, pady=(10, 4))
            ctk.CTkLabel(
                info, text=invoice["invoice_number"], text_color=TEXT,
                font=font(FONT_SIZE["body"], "bold"), anchor="w",
            ).pack(fill="x")
            ctk.CTkLabel(
                info,
                text=f"{invoice['customer_name']}  ·  {invoice['invoice_date']}",
                text_color=SECONDARY, font=font(FONT_SIZE["small"]), anchor="w",
            ).pack(fill="x", pady=(3, 0))
            row_footer = ctk.CTkFrame(row, fg_color="transparent")
            row_footer.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(
                row_footer, text=format_currency(invoice["total"]),
                text_color=TEXT, font=font(FONT_SIZE["body"], "bold"),
            ).pack(side="left")
            secondary_button(
                row_footer, "Load",
                command=lambda selected_id=invoice["id"]: self.load_invoice_into_editor(selected_id),
                height=30, width=72,
            ).pack(side="right")

    def load_invoice_into_editor(self, invoice_id):
        invoice = get_invoice_by_id(invoice_id)
        if invoice is None:
            self.status_label.configure(text="That invoice could not be loaded.")
            return
        customer = get_customer_by_id(invoice["customer_id"])
        if customer is None:
            self.status_label.configure(text="The customer for this invoice no longer exists.")
            return

        self.status_label.configure(text="")
        self.selected_invoice_id = invoice_id
        self.selected_customer_id = customer["id"]
        self.selected_label.configure(
            text=f"Reusing {invoice['invoice_number']}  ·  {customer['customer_name']}  ·  {invoice['invoice_date']}"
        )
        for row in self.item_rows:
            row["frame"].destroy()
        self.item_rows = []
        for item in invoice["items"]:
            self.add_item_row(item["description"], item["quantity"], item["unit_price"])
        self.notes_entry.delete(0, "end")
        if invoice.get("notes"):
            self.notes_entry.insert(0, invoice["notes"])
        self.regenerate_button.configure(state="normal")
        self.update_totals()

    def add_item_row(self, description="", quantity=1, price=0):
        row_frame = ctk.CTkFrame(self.items_scroll, fg_color=SURFACE)
        row_frame.pack(fill="x", pady=4, padx=4)
        row_frame.grid_columnconfigure(0, weight=5)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_columnconfigure(2, weight=2)

        description_entry = labeled_entry(row_frame, "Description")
        description_entry.field_container.grid(
            row=0, column=0, sticky="ew", padx=8, pady=8
        )
        description_entry.insert(0, description)
        quantity_entry = labeled_entry(row_frame, "Qty")
        quantity_entry.field_container.grid(
            row=0, column=1, sticky="ew", padx=(0, 8), pady=8
        )
        quantity_entry.insert(0, str(quantity))
        price_entry = labeled_entry(row_frame, "Unit price (R)")
        price_entry.field_container.grid(
            row=0, column=2, sticky="ew", padx=(0, 8), pady=8
        )
        price_entry.insert(0, str(price))
        line_total_label = ctk.CTkLabel(
            row_frame, text=format_currency(float(quantity) * float(price)),
            text_color=TEXT, font=font(FONT_SIZE["small"], "bold"),
        )
        line_total_label.grid(row=0, column=3, padx=8, pady=(28, 8), sticky="e")
        remove_button = ctk.CTkButton(
            row_frame, text="×", width=34, height=34,
            fg_color="transparent", hover_color="#F4F4F5",
            text_color=SECONDARY, corner_radius=8,
            command=lambda: self.remove_item_row(row_data),
        )
        remove_button.grid(row=0, column=4, padx=8, pady=(24, 8))
        row_data = {
            "frame": row_frame, "description": description_entry,
            "quantity": quantity_entry, "price": price_entry,
            "line_total_label": line_total_label,
        }
        quantity_entry.bind("<KeyRelease>", lambda _event: self.update_totals())
        price_entry.bind("<KeyRelease>", lambda _event: self.update_totals())
        self.item_rows.append(row_data)
        self.update_totals()

    def remove_item_row(self, row_data):
        if len(self.item_rows) == 1:
            self.status_label.configure(text="An invoice needs at least one item row.")
            return
        row_data["frame"].destroy()
        self.item_rows.remove(row_data)
        self.status_label.configure(text="")
        self.update_totals()

    def _collect_items(self):
        items = []
        for row in self.item_rows:
            description = row["description"].get().strip()
            if not description:
                continue
            try:
                quantity = float(row["quantity"].get())
                price = float(row["price"].get())
            except ValueError:
                quantity = 0
                price = 0
            row["line_total_label"].configure(
                text=format_currency(quantity * price)
            )
            items.append(
                {"description": description, "quantity": quantity, "unit_price": price}
            )
        return items

    def update_totals(self):
        totals = calculate_totals(self._collect_items())
        self.totals_label.configure(text=f"Total: {format_currency(totals['total'])}")

    def handle_regenerate(self):
        if self.selected_invoice_id is None:
            self.status_label.configure(text="Load an invoice from the list first.")
            return
        items = self._collect_items()
        if not items:
            self.status_label.configure(text="Add at least one item with a description.")
            return
        invalid_row = next(
            (
                row for row in self.item_rows
                if row["description"].get().strip()
                and (
                    not self._is_positive_number(row["quantity"].get())
                    or not self._is_nonnegative_number(row["price"].get())
                )
            ),
            None,
        )
        if invalid_row:
            self.status_label.configure(
                text="Enter a quantity greater than zero and a valid non-negative unit price."
            )
            return

        notes = self.notes_entry.get().strip()
        try:
            new_invoice_id = duplicate_invoice(
                self.selected_invoice_id, items, notes
            )
        except (ValueError, sqlite3.Error) as error:
            self.status_label.configure(text=f"The new invoice could not be saved: {error}")
            return

        new_invoice = get_invoice_by_id(new_invoice_id)
        try:
            pdf_path = generate_invoice_pdf(new_invoice_id)
        except (OSError, ValueError) as error:
            toast(
                self,
                f"Invoice {new_invoice['invoice_number']} saved, but PDF failed: {error}",
                "error",
            )
        else:
            toast(
                self,
                f"New invoice {new_invoice['invoice_number']} created. PDF saved to {pdf_path}.",
                "success",
            )

        self.selected_invoice_id = None
        self.selected_customer_id = None
        self.selected_label.configure(text="Select an invoice to reuse")
        self.status_label.configure(text="")
        for row in self.item_rows:
            row["frame"].destroy()
        self.item_rows = []
        self.notes_entry.delete(0, "end")
        self.update_totals()
        self.regenerate_button.configure(state="disabled")
        self.load_invoice_list(self.search_entry.get())
        self.controller.frames["dashboard"].refresh()

    @staticmethod
    def _is_positive_number(value):
        try:
            number = float(value)
            return math.isfinite(number) and number > 0
        except ValueError:
            return False

    @staticmethod
    def _is_nonnegative_number(value):
        try:
            number = float(value)
            return math.isfinite(number) and number >= 0
        except ValueError:
            return False
