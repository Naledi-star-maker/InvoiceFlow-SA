import customtkinter as ctk
from tkinter import messagebox
from app.database.database import get_all_customers
from app.services.invoice_service import create_invoice, calculate_totals

ctk.set_appearance_mode("light")

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"
ROW_BG = "#FDEFF3"


class InvoiceScreen(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("InvoiceFlow SA — New Invoice")
        self.geometry("950x700")
        self.configure(fg_color=WHITE)

        self.item_rows = []
        self.customers = get_all_customers()

        # ---------- Top ----------
        top_frame = ctk.CTkFrame(self, fg_color=WHITE)
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            top_frame, text="New Invoice", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PINK_DARK
        )
        title_label.pack(side="left")

        refresh_button = ctk.CTkButton(
            top_frame, text="Refresh Customers", width=140, command=self.refresh_customers,
            fg_color=WHITE, hover_color="#F0F0F0", text_color=PINK_TEXT,
            border_color=PINK, border_width=1
        )
        refresh_button.pack(side="right")

        # ---------- Customer selection ----------
        customer_frame = ctk.CTkFrame(self, fg_color=WHITE)
        customer_frame.pack(fill="x", padx=20, pady=5)

        customer_label = ctk.CTkLabel(
            customer_frame, text="Select Customer *", text_color=PINK_TEXT, anchor="w"
        )
        customer_label.pack(side="left", padx=(0, 10))

        customer_names = [c["customer_name"] for c in self.customers]
        if not customer_names:
            customer_names = ["No customers yet — add one first"]

        self.customer_dropdown = ctk.CTkOptionMenu(
            customer_frame, values=customer_names, width=300,
            fg_color=PINK, button_color=PINK_DARK, button_hover_color=PINK_DARK,
            text_color=PINK_TEXT
        )
        self.customer_dropdown.pack(side="left")

        # ---------- Items section ----------
        items_label = ctk.CTkLabel(
            self, text="Invoice Items", font=ctk.CTkFont(size=15, weight="bold"),
            text_color=PINK_DARK
        )
        items_label.pack(anchor="w", padx=20, pady=(15, 5))

        header_frame = ctk.CTkFrame(self, fg_color=WHITE)
        header_frame.pack(fill="x", padx=20)
        ctk.CTkLabel(header_frame, text="Description", text_color=PINK_TEXT, width=380, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Qty", text_color=PINK_TEXT, width=70, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Unit Price (R)", text_color=PINK_TEXT, width=110, anchor="w").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Line Total", text_color=PINK_TEXT, width=100, anchor="w").pack(side="left", padx=5)

        self.items_scroll = ctk.CTkScrollableFrame(self, fg_color=WHITE, height=250)
        self.items_scroll.pack(fill="both", expand=True, padx=20, pady=5)

        add_item_button = ctk.CTkButton(
            self, text="+ Add Item", command=self.add_item_row,
            fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT, width=150
        )
        add_item_button.pack(anchor="w", padx=20, pady=5)

        # ---------- Notes ----------
        notes_label = ctk.CTkLabel(self, text="Notes (optional)", text_color=PINK_TEXT, anchor="w")
        notes_label.pack(fill="x", padx=20, pady=(10, 0))

        self.notes_entry = ctk.CTkEntry(self, border_color=PINK, text_color=PINK_TEXT)
        self.notes_entry.pack(fill="x", padx=20, pady=(2, 10))

        # ---------- Totals ----------
        totals_frame = ctk.CTkFrame(self, fg_color=WHITE)
        totals_frame.pack(fill="x", padx=20, pady=5)

        self.totals_label = ctk.CTkLabel(
            totals_frame, text="Total: R0.00",
            font=ctk.CTkFont(size=16, weight="bold"), text_color=PINK_DARK
        )
        self.totals_label.pack(side="left")

        recalc_button = ctk.CTkButton(
            totals_frame, text="Recalculate Total", command=self.update_totals,
            fg_color=WHITE, hover_color="#F0F0F0", text_color=PINK_TEXT,
            border_color=PINK, border_width=1, width=160
        )
        recalc_button.pack(side="right")

        # ---------- Create button ----------
        create_button = ctk.CTkButton(
            self, text="Create Invoice", command=self.handle_create,
            height=45, font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT
        )
        create_button.pack(pady=15)

        self.add_item_row()

    # ------------------------------------------------------
    def refresh_customers(self):
        self.customers = get_all_customers()
        customer_names = [c["customer_name"] for c in self.customers]
        if not customer_names:
            customer_names = ["No customers yet — add one first"]
        self.customer_dropdown.configure(values=customer_names)
        self.customer_dropdown.set(customer_names[0])

    # ------------------------------------------------------
    def add_item_row(self):
        row_frame = ctk.CTkFrame(self.items_scroll, fg_color=ROW_BG)
        row_frame.pack(fill="x", pady=3, padx=3)

        description_entry = ctk.CTkEntry(row_frame, width=370, border_color=PINK, text_color=PINK_TEXT)
        description_entry.pack(side="left", padx=5, pady=6)

        quantity_entry = ctk.CTkEntry(row_frame, width=60, border_color=PINK, text_color=PINK_TEXT)
        quantity_entry.insert(0, "1")
        quantity_entry.pack(side="left", padx=5)

        price_entry = ctk.CTkEntry(row_frame, width=100, border_color=PINK, text_color=PINK_TEXT)
        price_entry.insert(0, "0")
        price_entry.pack(side="left", padx=5)

        line_total_label = ctk.CTkLabel(row_frame, text="R0.00", width=90, text_color=PINK_TEXT)
        line_total_label.pack(side="left", padx=5)

        remove_button = ctk.CTkButton(
            row_frame, text="Remove", width=70,
            fg_color="#E88BA3", hover_color="#D66E88", text_color=WHITE,
            command=lambda: self.remove_item_row(row_data)
        )
        remove_button.pack(side="left", padx=5)

        row_data = {
            "frame": row_frame,
            "description": description_entry,
            "quantity": quantity_entry,
            "price": price_entry,
            "line_total_label": line_total_label
        }

        quantity_entry.bind("<KeyRelease>", lambda e: self.update_totals())
        price_entry.bind("<KeyRelease>", lambda e: self.update_totals())

        self.item_rows.append(row_data)
        self.update_totals()

    # ------------------------------------------------------
    def remove_item_row(self, row_data):
        if len(self.item_rows) == 1:
            messagebox.showwarning("Cannot Remove", "An invoice needs at least one item row.")
            return
        row_data["frame"].destroy()
        self.item_rows.remove(row_data)
        self.update_totals()

    # ------------------------------------------------------
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

            items.append({
                "description": description,
                "quantity": quantity,
                "unit_price": price
            })

        return items

    # ------------------------------------------------------
    def update_totals(self):
        items = self._collect_items()
        totals = calculate_totals(items)
        self.totals_label.configure(text=f"Total: R{totals['total']:.2f}")

    # ------------------------------------------------------
    def handle_create(self):
        selected_name = self.customer_dropdown.get()
        customer = next((c for c in self.customers if c["customer_name"] == selected_name), None)

        if customer is None:
            messagebox.showerror("No Customer Selected", "Please select a valid customer. If none exist, add one in Customers first.")
            return

        items = self._collect_items()
        if not items:
            messagebox.showerror("No Items", "Please add at least one item with a description.")
            return

        invoice_id = create_invoice(customer["id"], items)

        messagebox.showinfo("Invoice Created", f"Invoice created successfully (ID: {invoice_id}).")

        for row in self.item_rows[1:]:
            row["frame"].destroy()
        self.item_rows = self.item_rows[:1]
        self.item_rows[0]["description"].delete(0, "end")
        self.item_rows[0]["quantity"].delete(0, "end")
        self.item_rows[0]["quantity"].insert(0, "1")
        self.item_rows[0]["price"].delete(0, "end")
        self.item_rows[0]["price"].insert(0, "0")
        self.notes_entry.delete(0, "end")
        self.update_totals()


if __name__ == "__main__":
    app = InvoiceScreen()
    app.mainloop()