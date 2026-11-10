import customtkinter as ctk

from app.database.database import (
    CustomerHasInvoicesError,
    add_customer,
    create_customers_table,
    delete_customer,
    get_all_customers,
    search_customers,
    update_customer,
)
from app.theme import (
    BG,
    BORDER,
    DANGER,
    FONT_SIZE,
    SECONDARY,
    SURFACE,
    TEXT,
    card,
    confirm_dialog,
    empty_state,
    font,
    labeled_dropdown,
    labeled_entry,
    page_header,
    primary_button,
    secondary_button,
    set_inline_error,
    toast,
)


PROVINCES = [
    "Eastern Cape", "Free State", "Gauteng", "KwaZulu-Natal",
    "Limpopo", "Mpumalanga", "Northern Cape", "North West", "Western Cape",
]


class CustomerFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        create_customers_table()
        self.selected_customer_id = None

        page_header(
            self, "Customers", "Manage your customer contact details.",
        ).pack(fill="x", padx=24, pady=(24, 16))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        content.grid_columnconfigure(0, weight=3)
        content.grid_columnconfigure(1, weight=2, minsize=300)
        content.grid_rowconfigure(0, weight=1)

        list_card = card(content)
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        search_row = ctk.CTkFrame(list_card, fg_color="transparent")
        search_row.pack(fill="x", padx=16, pady=16)
        search_row.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(
            search_row, placeholder_text="Search name, business, phone, or email",
            height=38, border_color=BORDER, text_color=TEXT,
            placeholder_text_color=SECONDARY, corner_radius=8,
            font=font(FONT_SIZE["body"]),
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind(
            "<KeyRelease>", lambda _event: self.handle_search()
        )
        secondary_button(
            search_row, "Clear", command=self.load_customers,
            height=38, width=76,
        ).grid(row=0, column=1)
        self.customer_list_frame = ctk.CTkScrollableFrame(
            list_card, fg_color=SURFACE,
        )
        self.customer_list_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.form_card = card(content)
        self.form_card.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(
            self.form_card, text="Customer details", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.form_scroll = ctk.CTkScrollableFrame(
            self.form_card, fg_color=SURFACE,
        )
        self.form_scroll.pack(fill="both", expand=True, padx=8)

        self.customer_name = self._add_field("Customer name *")
        self.business_name = self._add_field("Business name")
        self.phone = self._add_field("Phone number")
        self.email = self._add_field("Email")
        self.address = self._add_field("Physical address")
        self.city = self._add_field("City")
        self.province = self._add_dropdown("Province", PROVINCES)
        self.postal_code = self._add_field("Postal code")
        self.notes = self._add_field("Notes")

        self.form_error = ctk.CTkLabel(
            self.form_card, text="", text_color=DANGER, anchor="w",
            justify="left", font=font(FONT_SIZE["small"]),
        )
        self.form_error.pack(fill="x", padx=16, pady=(4, 0))
        button_frame = ctk.CTkFrame(self.form_card, fg_color="transparent")
        button_frame.pack(fill="x", padx=12, pady=12)
        primary_button(
            button_frame, "Save new customer", command=self.handle_save,
            height=38,
        ).pack(fill="x", pady=3)
        secondary_button(
            button_frame, "Update selected", command=self.handle_update,
            height=38,
        ).pack(fill="x", pady=3)
        ctk.CTkButton(
            button_frame, text="Delete selected", command=self.handle_delete,
            height=38, fg_color="#DC2626", hover_color="#B91C1C",
            text_color=SURFACE, corner_radius=8, font=font(FONT_SIZE["body"]),
        ).pack(fill="x", pady=3)
        secondary_button(
            button_frame, "Clear form", command=self.clear_form,
            height=38,
        ).pack(fill="x", pady=3)
        self.load_customers()

    def refresh(self):
        self.load_customers()

    def _add_field(self, label_text):
        entry = labeled_entry(self.form_scroll, label_text)
        entry.field_container.pack(fill="x", padx=8, pady=(4, 8))
        return entry

    def _add_dropdown(self, label_text, options):
        dropdown = labeled_dropdown(self.form_scroll, label_text, options)
        dropdown.set(options[0])
        dropdown.field_container.pack(fill="x", padx=8, pady=(4, 8))
        return dropdown

    def load_customers(self):
        self.search_entry.delete(0, "end")
        self._render_customer_list(get_all_customers())

    def handle_search(self):
        keyword = self.search_entry.get().strip()
        customers = search_customers(keyword) if keyword else get_all_customers()
        self._render_customer_list(customers)

    def _render_customer_list(self, customers):
        for widget in self.customer_list_frame.winfo_children():
            widget.destroy()
        if not customers:
            empty_state(
                self.customer_list_frame,
                "No customers found. Add your first customer to get started.",
                "Add customer",
                self.clear_form,
            )
            return

        for customer in customers:
            row = ctk.CTkFrame(
                self.customer_list_frame, fg_color=SURFACE,
                corner_radius=8, border_color=BORDER, border_width=1,
            )
            row.pack(fill="x", padx=4, pady=4)
            initials = "".join(
                part[0] for part in customer["customer_name"].split()[:2]
            ).upper() or "?"
            ctk.CTkLabel(
                row, text=initials, width=38, height=38, corner_radius=19,
                fg_color="#F4F4F5", text_color=SECONDARY,
                font=font(FONT_SIZE["small"], "bold"),
            ).pack(side="left", padx=(12, 10), pady=12)
            details = ctk.CTkFrame(row, fg_color="transparent")
            details.pack(side="left", fill="x", expand=True, pady=10)
            ctk.CTkLabel(
                details, text=customer["customer_name"], text_color=TEXT,
                font=font(FONT_SIZE["body"], "bold"), anchor="w",
            ).pack(fill="x")
            business = customer.get("business_name") or "Individual customer"
            contact = customer.get("phone") or customer.get("email") or ""
            ctk.CTkLabel(
                details, text=f"{business}  ·  {contact}" if contact else business,
                text_color=SECONDARY, font=font(FONT_SIZE["small"]), anchor="w",
            ).pack(fill="x", pady=(3, 0))
            secondary_button(
                row, "Select", command=lambda record=customer: self.select_customer(record),
                height=32, width=72,
            ).pack(side="right", padx=12)

    def select_customer(self, customer):
        self.selected_customer_id = customer["id"]
        self._set_entry(self.customer_name, customer["customer_name"])
        self._set_entry(self.business_name, customer["business_name"])
        self._set_entry(self.phone, customer["phone"])
        self._set_entry(self.email, customer["email"])
        self._set_entry(self.address, customer["address"])
        self._set_entry(self.city, customer["city"])
        self.province.set(
            customer["province"] if customer["province"] in PROVINCES else PROVINCES[0]
        )
        self._set_entry(self.postal_code, customer["postal_code"])
        self._set_entry(self.notes, customer["notes"])
        self.form_error.configure(text="")

    @staticmethod
    def _set_entry(entry, value):
        entry.delete(0, "end")
        entry.insert(0, value or "")

    def clear_form(self):
        self.selected_customer_id = None
        for field in (
            self.customer_name, self.business_name, self.phone, self.email,
            self.address, self.city, self.postal_code, self.notes,
        ):
            field.delete(0, "end")
            set_inline_error(field, "")
        self.province.set(PROVINCES[0])
        self.form_error.configure(text="")

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
        for field in (
            self.customer_name, self.city, self.phone, self.postal_code,
        ):
            set_inline_error(field, "")
        self.form_error.configure(text="")
        if not data["customer_name"]:
            set_inline_error(self.customer_name, "Customer name is required.")
            return False
        if data["city"] and any(char.isdigit() for char in data["city"]):
            set_inline_error(self.city, "City should not contain numbers.")
            return False
        if data["phone"]:
            phone_digits = data["phone"].replace(" ", "").replace("+", "").replace("-", "")
            if not phone_digits.isdigit():
                set_inline_error(
                    self.phone,
                    "Use digits, spaces, +, or - for the phone number.",
                )
                return False
        if data["postal_code"] and not data["postal_code"].isdigit():
            set_inline_error(self.postal_code, "Postal code should contain numbers only.")
            return False
        return True

    def handle_save(self):
        data = self._get_form_data()
        if not self._validate(data):
            return
        add_customer(data)
        toast(self, "Customer added successfully.", "success")
        self.clear_form()
        self._render_customer_list(get_all_customers())
        self.controller.frames["dashboard"].refresh()

    def handle_update(self):
        if self.selected_customer_id is None:
            self.form_error.configure(text="Select a customer to update.")
            return
        data = self._get_form_data()
        if not self._validate(data):
            return
        update_customer(self.selected_customer_id, data)
        toast(self, "Customer updated successfully.", "success")
        self.clear_form()
        self._render_customer_list(get_all_customers())
        self.controller.frames["dashboard"].refresh()

    def handle_delete(self):
        if self.selected_customer_id is None:
            self.form_error.configure(text="Select a customer to delete.")
            return
        if not confirm_dialog(
            self,
            "Delete customer?",
            "Are you sure you want to delete this customer? Customers with existing invoices cannot be deleted.",
            confirm_text="Delete customer",
        ):
            return
        try:
            delete_customer(self.selected_customer_id)
        except CustomerHasInvoicesError as error:
            self.form_error.configure(text=str(error))
            return
        toast(self, "Customer deleted successfully.", "success")
        self.clear_form()
        self._render_customer_list(get_all_customers())
        self.controller.frames["dashboard"].refresh()
