import customtkinter as ctk
from tkinter import messagebox
from database import (
    create_customers_table, add_customer, get_all_customers,
    update_customer, delete_customer, search_customers
)

ctk.set_appearance_mode("light")

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"


class CustomerScreen(ctk.CTk):
    def __init__(self):
        super().__init__()

        create_customers_table()

        self.title("InvoiceFlow SA — Customers")
        self.geometry("900x650")
        self.configure(fg_color=WHITE)

        self.selected_customer_id = None

        # Top bar: search
        top_frame = ctk.CTkFrame(self, fg_color=WHITE)
        top_frame.pack(fill="x", padx=20, pady=(20, 10))

        title_label = ctk.CTkLabel(
            top_frame, text="Customers", font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PINK_DARK
        )
        title_label.pack(side="left")

        self.search_entry = ctk.CTkEntry(
            top_frame, placeholder_text="Search customers...", width=250,
            border_color=PINK, text_color=PINK_TEXT
        )
        self.search_entry.pack(side="right", padx=(5, 0))

        search_button = ctk.CTkButton(
            top_frame, text="Search", width=80, command=self.handle_search,
            fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT
        )
        search_button.pack(side="right", padx=5)

        clear_button = ctk.CTkButton(
            top_frame, text="Clear", width=80, command=self.load_customers,
            fg_color=WHITE, hover_color="#F0F0F0", text_color=PINK_TEXT,
            border_color=PINK, border_width=1
        )
        clear_button.pack(side="right", padx=5)

        # Main content: list on left, form on right
        main_frame = ctk.CTkFrame(self, fg_color=WHITE)
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Left: customer list
        list_frame = ctk.CTkFrame(main_frame, fg_color=WHITE, border_color=PINK, border_width=1)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        self.customer_list_frame = ctk.CTkScrollableFrame(list_frame, fg_color=WHITE)
        self.customer_list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Right: form
        form_frame = ctk.CTkFrame(main_frame, fg_color=WHITE, width=300)
        form_frame.pack(side="right", fill="y")

        form_title = ctk.CTkLabel(
            form_frame, text="Customer Details", font=ctk.CTkFont(size=16, weight="bold"),
            text_color=PINK_DARK
        )
        form_title.pack(pady=(5, 10))

        self.customer_name = self._add_field(form_frame, "Customer Name *")
        self.business_name = self._add_field(form_frame, "Business Name")
        self.phone = self._add_field(form_frame, "Phone Number")
        self.email = self._add_field(form_frame, "Email")
        self.address = self._add_field(form_frame, "Physical Address")
        self.city = self._add_field(form_frame, "City")
        self.province = self._add_field(form_frame, "Province")
        self.postal_code = self._add_field(form_frame, "Postal Code")
        self.notes = self._add_field(form_frame, "Notes")

        button_frame = ctk.CTkFrame(form_frame, fg_color=WHITE)
        button_frame.pack(pady=15, fill="x")

        self.save_button = ctk.CTkButton(
            button_frame, text="Save New", command=self.handle_save,
            fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT
        )
        self.save_button.pack(fill="x", pady=3)

        self.update_button = ctk.CTkButton(
            button_frame, text="Update Selected", command=self.handle_update,
            fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT
        )
        self.update_button.pack(fill="x", pady=3)

        self.delete_button = ctk.CTkButton(
            button_frame, text="Delete Selected", command=self.handle_delete,
            fg_color="#E88BA3", hover_color="#D66E88", text_color=WHITE
        )
        self.delete_button.pack(fill="x", pady=3)

        self.clear_form_button = ctk.CTkButton(
            button_frame, text="Clear Form", command=self.clear_form,
            fg_color=WHITE, hover_color="#F0F0F0", text_color=PINK_TEXT,
            border_color=PINK, border_width=1
        )
        self.clear_form_button.pack(fill="x", pady=3)

        self.load_customers()

    def _add_field(self, parent, label_text):
        label = ctk.CTkLabel(parent, text=label_text, anchor="w", text_color=PINK_TEXT)
        label.pack(fill="x", padx=5, pady=(5, 0))

        entry = ctk.CTkEntry(parent, width=260, border_color=PINK, text_color=PINK_TEXT)
        entry.pack(fill="x", padx=5, pady=(2, 0))

        return entry

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
            empty_label = ctk.CTkLabel(
                self.customer_list_frame, text="No customers found.", text_color=PINK_TEXT
            )
            empty_label.pack(pady=10)
            return

        for customer in customers:
            row = ctk.CTkFrame(self.customer_list_frame, fg_color="#FDEFF3")
            row.pack(fill="x", pady=3, padx=3)

            name_text = customer["customer_name"]
            if customer["business_name"]:
                name_text += f"  ({customer['business_name']})"

            label = ctk.CTkLabel(row, text=name_text, anchor="w", text_color=PINK_TEXT)
            label.pack(side="left", padx=10, pady=8, fill="x", expand=True)

            select_button = ctk.CTkButton(
                row, text="Select", width=70,
                fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT,
                command=lambda c=customer: self.select_customer(c)
            )
            select_button.pack(side="right", padx=10, pady=5)

    def select_customer(self, customer):
        self.selected_customer_id = customer["id"]
        self.customer_name.delete(0, "end")
        self.customer_name.insert(0, customer["customer_name"])
        self.business_name.delete(0, "end")
        self.business_name.insert(0, customer["business_name"] or "")
        self.phone.delete(0, "end")
        self.phone.insert(0, customer["phone"] or "")
        self.email.delete(0, "end")
        self.email.insert(0, customer["email"] or "")
        self.address.delete(0, "end")
        self.address.insert(0, customer["address"] or "")
        self.city.delete(0, "end")
        self.city.insert(0, customer["city"] or "")
        self.province.delete(0, "end")
        self.province.insert(0, customer["province"] or "")
        self.postal_code.delete(0, "end")
        self.postal_code.insert(0, customer["postal_code"] or "")
        self.notes.delete(0, "end")
        self.notes.insert(0, customer["notes"] or "")

    def clear_form(self):
        self.selected_customer_id = None
        for field in [self.customer_name, self.business_name, self.phone,
                      self.email, self.address, self.city, self.province,
                      self.postal_code, self.notes]:
            field.delete(0, "end")

    def _get_form_data(self):
        return {
            "customer_name": self.customer_name.get().strip(),
            "business_name": self.business_name.get().strip(),
            "phone": self.phone.get().strip(),
            "email": self.email.get().strip(),
            "address": self.address.get().strip(),
            "city": self.city.get().strip(),
            "province": self.province.get().strip(),
            "postal_code": self.postal_code.get().strip(),
            "notes": self.notes.get().strip(),
        }

    def handle_save(self):
        data = self._get_form_data()
        if data["customer_name"] == "":
            messagebox.showerror("Missing Information", "Customer Name is required.")
            return

        add_customer(data)
        messagebox.showinfo("Saved", "Customer added successfully.")
        self.clear_form()
        self.load_customers()

    def handle_update(self):
        if self.selected_customer_id is None:
            messagebox.showerror("No Customer Selected", "Please select a customer to update.")
            return

        data = self._get_form_data()
        if data["customer_name"] == "":
            messagebox.showerror("Missing Information", "Customer Name is required.")
            return

        update_customer(self.selected_customer_id, data)
        messagebox.showinfo("Updated", "Customer updated successfully.")
        self.clear_form()
        self.load_customers()

    def handle_delete(self):
        if self.selected_customer_id is None:
            messagebox.showerror("No Customer Selected", "Please select a customer to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this customer?")
        if confirm:
            delete_customer(self.selected_customer_id)
            messagebox.showinfo("Deleted", "Customer deleted successfully.")
            self.clear_form()
            self.load_customers()


if __name__ == "__main__":
    app = CustomerScreen()
    app.mainloop()