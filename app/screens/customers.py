import customtkinter as ctk
from tkinter import messagebox
from app.database.database import (
    create_customers_table, add_customer, get_all_customers,
    update_customer, delete_customer, search_customers,
    CustomerHasInvoicesError
)

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"

PROVINCES = [
    "Eastern Cape", "Free State", "Gauteng", "KwaZulu-Natal",
    "Limpopo", "Mpumalanga", "Northern Cape", "North West", "Western Cape"
]


class CustomerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=WHITE)
        self.controller = controller
        create_customers_table()
        self.selected_customer_id = None

        top_frame = ctk.CTkFrame(self, fg_color=WHITE)
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(top_frame, text="Customers", font=ctk.CTkFont(size=22, weight="bold"), text_color=PINK_DARK).pack(side="left")

        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="Search customers...", width=250, border_color=PINK, text_color=PINK_TEXT)
        self.search_entry.pack(side="right", padx=(5, 0))

        ctk.CTkButton(top_frame, text="Search", width=80, command=self.handle_search, fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT).pack(side="right", padx=5)
        ctk.CTkButton(top_frame, text="Clear", width=80, command=self.load_customers, fg_color=WHITE, hover_color="#F0F0F0", text_color=PINK_TEXT, border_color=PINK, border_width=1).pack(side="right", padx=5)

        content_frame = ctk.CTkFrame(self, fg_color=WHITE)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        list_frame = ctk.CTkFrame(content_frame, fg_color=WHITE, border_color=PINK, border_width=1)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.customer_list_frame = ctk.CTkScrollableFrame(list_frame, fg_color=WHITE)
        self.customer_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        form_frame = ctk.CTkFrame(content_frame, fg_color=WHITE, width=300)
        form_frame.pack(side="right", fill="y")

        ctk.CTkLabel(form_frame, text="Customer Details", font=ctk.CTkFont(size=16, weight="bold"), text_color=PINK_DARK).pack(pady=(5, 10))

        self.customer_name = self._add_field(form_frame, "Customer Name *")
        self.business_name = self._add_field(form_frame, "Business Name")
        self.phone = self._add_field(form_frame, "Phone Number")
        self.email = self._add_field(form_frame, "Email")
        self.address = self._add_field(form_frame, "Physical Address")
        self.city = self._add_field(form_frame, "City")
        self.province = self._add_dropdown(form_frame, "Province", PROVINCES)
        self.postal_code = self._add_field(form_frame, "Postal Code")
        self.notes = self._add_field(form_frame, "Notes")

        button_frame = ctk.CTkFrame(form_frame, fg_color=WHITE)
        button_frame.pack(pady=15, fill="x")

        ctk.CTkButton(button_frame, text="Save New", command=self.handle_save, fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT).pack(fill="x", pady=3)
        ctk.CTkButton(button_frame, text="Update Selected", command=self.handle_update, fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT).pack(fill="x", pady=3)
        ctk.CTkButton(button_frame, text="Delete Selected", command=self.handle_delete, fg_color="#E88BA3", hover_color="#D66E88", text_color=WHITE).pack(fill="x", pady=3)
        ctk.CTkButton(button_frame, text="Clear Form", command=self.clear_form, fg_color=WHITE, hover_color="#F0F0F0", text_color=PINK_TEXT, border_color=PINK, border_width=1).pack(fill="x", pady=3)

        self.load_customers()

    def refresh(self):
        self.load_customers()

    def _add_field(self, parent, label_text):
        ctk.CTkLabel(parent, text=label_text, anchor="w", text_color=PINK_TEXT).pack(fill="x", padx=5, pady=(5, 0))
        entry = ctk.CTkEntry(parent, width=260, border_color=PINK, text_color=PINK_TEXT)
        entry.pack(fill="x", padx=5, pady=(2, 0))
        return entry

    def _add_dropdown(self, parent, label_text, options):
        ctk.CTkLabel(parent, text=label_text, anchor="w", text_color=PINK_TEXT).pack(fill="x", padx=5, pady=(5, 0))
        dropdown = ctk.CTkOptionMenu(
            parent, values=options, width=260,
            fg_color=PINK, button_color=PINK_DARK, button_hover_color=PINK_DARK,
            text_color=PINK_TEXT
        )
        dropdown.set(options[0])
        dropdown.pack(fill="x", padx=5, pady=(2, 0))
        return dropdown

    def load_customers(self):
        self.search_entry.delete(0, "end")
        customers = get_all_customers()
        self._render_customer_list(customers)

    def handle_search(self):
        keyword = self.search_entry.get().strip()
        if keyword == "":
            self.load_customers()
            return
        customers = search_customers(keyword)
        self._render_customer_list(customers)

    def _render_customer_list(self, customers):
        for widget in self.customer_list_frame.winfo_children():
            widget.destroy()

        if not customers:
            ctk.CTkLabel(self.customer_list_frame, text="No customers found.", text_color=PINK_TEXT).pack(pady=10)
            return

        for customer in customers:
            row = ctk.CTkFrame(self.customer_list_frame, fg_color="#FDEFF3")
            row.pack(fill="x", pady=3, padx=3)

            name_text = customer["customer_name"]
            if customer["business_name"]:
                name_text += f"  ({customer['business_name']})"

            ctk.CTkLabel(row, text=name_text, anchor="w", text_color=PINK_TEXT).pack(side="left", padx=10, pady=8, fill="x", expand=True)

            ctk.CTkButton(
                row, text="Select", width=70,
                fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT,
                command=lambda c=customer: self.select_customer(c)
            ).pack(side="right", padx=10, pady=5)

    def select_customer(self, customer):
        self.selected_customer_id = customer["id"]
        self.customer_name.delete(0, "end"); self.customer_name.insert(0, customer["customer_name"])
        self.business_name.delete(0, "end"); self.business_name.insert(0, customer["business_name"] or "")
        self.phone.delete(0, "end"); self.phone.insert(0, customer["phone"] or "")
        self.email.delete(0, "end"); self.email.insert(0, customer["email"] or "")
        self.address.delete(0, "end"); self.address.insert(0, customer["address"] or "")
        self.city.delete(0, "end"); self.city.insert(0, customer["city"] or "")
        if customer["province"] in PROVINCES:
            self.province.set(customer["province"])
        else:
            self.province.set(PROVINCES[0])
        self.postal_code.delete(0, "end"); self.postal_code.insert(0, customer["postal_code"] or "")
        self.notes.delete(0, "end"); self.notes.insert(0, customer["notes"] or "")

    def clear_form(self):
        self.selected_customer_id = None
        for field in [self.customer_name, self.business_name, self.phone, self.email,
                      self.address, self.city, self.postal_code, self.notes]:
            field.delete(0, "end")
        self.province.set(PROVINCES[0])

    def _get_form_data(self):
        return {
            "customer_name": self.customer_name.get().strip(),
            "business_name": self.business_name.get().strip(),
            "phone": self.phone.get().strip(),
            "email": self.email.get().strip(),
            "address": self.address.get().strip(),
            "city": self.city.get().strip(),
            "province": self.province.get(),
            "postal_code": self.postal_code.get().strip(),
            "notes": self.notes.get().strip(),
        }

    def _validate(self, data):
        if data["customer_name"] == "":
            messagebox.showerror("Missing Information", "Customer Name is required.")
            return False

        if data["city"] and any(char.isdigit() for char in data["city"]):
            messagebox.showerror("Invalid City", "City should not contain numbers.")
            return False

        if data["phone"]:
            phone_digits = data["phone"].replace(" ", "").replace("+", "").replace("-", "")
            if not phone_digits.isdigit():
                messagebox.showerror("Invalid Phone Number", "Phone number should contain only digits, spaces, + or -.")
                return False

        if data["postal_code"] and not data["postal_code"].isdigit():
            messagebox.showerror("Invalid Postal Code", "Postal code should contain only numbers.")
            return False

        return True

    def handle_save(self):
        data = self._get_form_data()
        if not self._validate(data):
            return
        add_customer(data)
        messagebox.showinfo("Saved", "Customer added successfully.")
        self.clear_form()
        self.load_customers()
        self.controller.frames["dashboard"].refresh()

    def handle_update(self):
        if self.selected_customer_id is None:
            messagebox.showerror("No Customer Selected", "Please select a customer to update.")
            return
        data = self._get_form_data()
        if not self._validate(data):
            return
        update_customer(self.selected_customer_id, data)
        messagebox.showinfo("Updated", "Customer updated successfully.")
        self.clear_form()
        self.load_customers()

    def handle_delete(self):
        if self.selected_customer_id is None:
            messagebox.showerror("No Customer Selected", "Please select a customer to delete.")
            return
        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this customer? "
            "Customers with existing invoices cannot be deleted."
        )
        if confirm:
            try:
                delete_customer(self.selected_customer_id)
            except CustomerHasInvoicesError as error:
                messagebox.showerror("Customer Not Deleted", str(error))
                return
            messagebox.showinfo("Deleted", "Customer deleted successfully.")
            self.clear_form()
            self.load_customers()
            self.controller.frames["dashboard"].refresh()