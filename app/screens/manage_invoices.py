import sqlite3
import customtkinter as ctk
from tkinter import messagebox

from app.database.database import get_all_invoices, search_invoices, get_invoice_by_id, get_customer_by_id
from app.services.invoice_service import duplicate_invoice, calculate_totals
from app.services.pdf_generator import generate_invoice_pdf

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"
ROW_BG = "#FDEFF3"
BORDER_COLOR = "#F5DDE6"


class ManageInvoiceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=WHITE)
        self.controller = controller
        self.item_rows = []
        self.selected_invoice_id = None
        self.selected_customer_id = None

        ctk.CTkLabel(
            self, text="Manage Invoices", font=ctk.CTkFont(size=22, weight="bold"), text_color=PINK_DARK
        ).pack(anchor="w", padx=20, pady=(20, 5))

        ctk.CTkLabel(
            self,
            text="Pick a past invoice to reuse for a month-end resend. Edit the items or "
                 "prices if needed, then regenerate — a new invoice number, date and time "
                 "will be created automatically. The original invoice is left untouched.",
            font=ctk.CTkFont(size=11), text_color=PINK_TEXT, wraplength=900, justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        body = ctk.CTkFrame(self, fg_color=WHITE)
        body.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # ---------------- Left: invoice picker ----------------
        left_panel = ctk.CTkFrame(
            body, fg_color=WHITE, border_color=BORDER_COLOR, border_width=1,
            corner_radius=10, width=320
        )
        left_panel.pack(side="left", fill="y", padx=(0, 15))
        left_panel.pack_propagate(False)

        self.search_entry = ctk.CTkEntry(
            left_panel, placeholder_text="Search invoice # or customer...",
            border_color=PINK, text_color=PINK_TEXT
        )
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_invoice_list(self.search_entry.get()))

        self.list_scroll = ctk.CTkScrollableFrame(left_panel, fg_color=WHITE)
        self.list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ---------------- Right: editor ----------------
        right_panel = ctk.CTkFrame(body, fg_color=WHITE)
        right_panel.pack(side="left", fill="both", expand=True)

        self.selected_label = ctk.CTkLabel(
            right_panel, text="No invoice selected",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=PINK_DARK
        )
        self.selected_label.pack(anchor="w", pady=(0, 10))

        header_frame = ctk.CTkFrame(right_panel, fg_color=WHITE)
        header_frame.pack(fill="x")
        ctk.CTkLabel(header_frame, text="Description", text_color=PINK_TEXT, width=320, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Qty", text_color=PINK_TEXT, width=70, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Unit Price (R)", text_color=PINK_TEXT, width=110, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Line Total", text_color=PINK_TEXT, width=100, anchor="w").pack(side="left", padx=5)

        self.items_scroll = ctk.CTkScrollableFrame(right_panel, fg_color=WHITE, height=220)
        self.items_scroll.pack(fill="both", expand=True, pady=5)

        ctk.CTkButton(
            right_panel, text="+ Add Item", command=lambda: self.add_item_row(),
            fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT, width=150
        ).pack(anchor="w", pady=5)

        ctk.CTkLabel(right_panel, text="Notes (optional)", text_color=PINK_TEXT, anchor="w").pack(fill="x", pady=(10, 0))
        self.notes_entry = ctk.CTkEntry(right_panel, border_color=PINK, text_color=PINK_TEXT)
        self.notes_entry.pack(fill="x", pady=(2, 10))

        totals_frame = ctk.CTkFrame(right_panel, fg_color=WHITE)
        totals_frame.pack(fill="x", pady=5)

        self.totals_label = ctk.CTkLabel(
            totals_frame, text="Total: R0.00", font=ctk.CTkFont(size=16, weight="bold"), text_color=PINK_DARK
        )
        self.totals_label.pack(side="left")

        ctk.CTkButton(
            totals_frame, text="Recalculate Total", command=self.update_totals,
            fg_color=WHITE, hover_color="#F0F0F0", text_color=PINK_TEXT,
            border_color=PINK, border_width=1, width=160
        ).pack(side="right")

        self.regenerate_button = ctk.CTkButton(
            right_panel, text="Regenerate Invoice", command=self.handle_regenerate,
            height=45, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT, state="disabled"
        )
        self.regenerate_button.pack(pady=15, fill="x")

    # ------------------------------------------------------------
    def refresh(self):
        self.load_invoice_list()

    def load_invoice_list(self, keyword=""):
        for widget in self.list_scroll.winfo_children():
            widget.destroy()

        invoices = search_invoices(keyword) if keyword.strip() else get_all_invoices()

        if not invoices:
            ctk.CTkLabel(self.list_scroll, text="No invoices found.", text_color=PINK_TEXT).pack(pady=10)
            return

        for invoice in invoices:
            row = ctk.CTkFrame(self.list_scroll, fg_color=ROW_BG, corner_radius=8)
            row.pack(fill="x", pady=3)

            text = f"{invoice['invoice_number']}\n{invoice['customer_name']} — R{invoice['total']:.2f}"
            ctk.CTkLabel(row, text=text, text_color=PINK_TEXT, justify="left", anchor="w").pack(
                side="left", fill="x", expand=True, padx=10, pady=8
            )

            ctk.CTkButton(
                row, text="Load", width=60,
                command=lambda i=invoice["id"]: self.load_invoice_into_editor(i),
                fg_color=PINK_DARK, hover_color="#E895B5", text_color=WHITE
            ).pack(side="right", padx=8)

    def load_invoice_into_editor(self, invoice_id):
        invoice = get_invoice_by_id(invoice_id)
        if invoice is None:
            messagebox.showerror("Not Found", "That invoice could not be loaded.")
            return

        customer = get_customer_by_id(invoice["customer_id"])
        if customer is None:
            messagebox.showerror("Not Found", "The customer for this invoice no longer exists.")
            return

        self.selected_invoice_id = invoice_id
        self.selected_customer_id = customer["id"]
        self.selected_label.configure(
            text=f"Reusing {invoice['invoice_number']} — {customer['customer_name']} "
                 f"(originally {invoice['invoice_date']})"
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

    # ------------------------------------------------------------
    def add_item_row(self, description="", quantity=1, price=0):
        row_frame = ctk.CTkFrame(self.items_scroll, fg_color=ROW_BG)
        row_frame.pack(fill="x", pady=3, padx=3)

        description_entry = ctk.CTkEntry(row_frame, width=310, border_color=PINK, text_color=PINK_TEXT)
        description_entry.insert(0, description)
        description_entry.pack(side="left", padx=5, pady=6)

        quantity_entry = ctk.CTkEntry(row_frame, width=60, border_color=PINK, text_color=PINK_TEXT)
        quantity_entry.insert(0, str(quantity))
        quantity_entry.pack(side="left", padx=5)

        price_entry = ctk.CTkEntry(row_frame, width=100, border_color=PINK, text_color=PINK_TEXT)
        price_entry.insert(0, str(price))
        price_entry.pack(side="left", padx=5)

        line_total_label = ctk.CTkLabel(row_frame, text=f"R{quantity * price:.2f}", width=90, text_color=PINK_TEXT)
        line_total_label.pack(side="left", padx=5)

        remove_button = ctk.CTkButton(
            row_frame, text="Remove", width=70,
            fg_color="#E88BA3", hover_color="#D66E88", text_color=WHITE,
            command=lambda: self.remove_item_row(row_data)
        )
        remove_button.pack(side="left", padx=5)

        row_data = {
            "frame": row_frame, "description": description_entry,
            "quantity": quantity_entry, "price": price_entry,
            "line_total_label": line_total_label
        }

        quantity_entry.bind("<KeyRelease>", lambda e: self.update_totals())
        price_entry.bind("<KeyRelease>", lambda e: self.update_totals())

        self.item_rows.append(row_data)
        self.update_totals()

    def remove_item_row(self, row_data):
        if len(self.item_rows) == 1:
            messagebox.showwarning("Cannot Remove", "An invoice needs at least one item row.")
            return
        row_data["frame"].destroy()
        self.item_rows.remove(row_data)
        self.update_totals()

    def _collect_items(self):
        items = []
        for row in self.item_rows:
            description = row["description"].get().strip()
            if description == "":
                continue
            try:
                quantity = float(row["quantity"].get())
            except ValueError:
                quantity = 0
            try:
                price = float(row["price"].get())
            except ValueError:
                price = 0
            line_total = quantity * price
            row["line_total_label"].configure(text=f"R{line_total:.2f}")
            items.append({"description": description, "quantity": quantity, "unit_price": price})
        return items

    def update_totals(self):
        items = self._collect_items()
        totals = calculate_totals(items)
        self.totals_label.configure(text=f"Total: R{totals['total']:.2f}")

    # ------------------------------------------------------------
    def handle_regenerate(self):
        if self.selected_invoice_id is None:
            messagebox.showerror("No Invoice Selected", "Please load an invoice from the list first.")
            return

        items = self._collect_items()
        if not items:
            messagebox.showerror("No Items", "Please add at least one item with a description.")
            return

        notes = self.notes_entry.get().strip()

        try:
            new_invoice_id = duplicate_invoice(self.selected_invoice_id, items, notes)
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror("Invoice Not Created", f"The new invoice could not be saved:\n{error}")
            return

        new_invoice = get_invoice_by_id(new_invoice_id)
        try:
            pdf_path = generate_invoice_pdf(new_invoice_id)
        except (OSError, ValueError) as error:
            messagebox.showerror(
                "Invoice Saved, PDF Not Created",
                f"New invoice {new_invoice['invoice_number']} was saved, "
                f"but its PDF could not be generated:\n{error}"
            )
        else:
            messagebox.showinfo(
                "Invoice Regenerated",
                f"New invoice {new_invoice['invoice_number']} created "
                f"(dated {new_invoice['invoice_date']}) and PDF saved to:\n{pdf_path}"
            )

        self.selected_invoice_id = None
        self.selected_customer_id = None
        self.selected_label.configure(text="No invoice selected")
        for row in self.item_rows:
            row["frame"].destroy()
        self.item_rows = []
        self.notes_entry.delete(0, "end")
        self.update_totals()
        self.regenerate_button.configure(state="disabled")

        self.load_invoice_list(self.search_entry.get())
        self.controller.frames["dashboard"].refresh()