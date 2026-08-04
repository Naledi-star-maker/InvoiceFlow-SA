import customtkinter as ctk
from tkinter import messagebox
from app.database.database import save_company_info, get_company_info, update_company_info

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"

PROVINCES = [
    "Eastern Cape", "Free State", "Gauteng", "KwaZulu-Natal",
    "Limpopo", "Mpumalanga", "Northern Cape", "North West", "Western Cape"
]


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=WHITE)
        self.controller = controller

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=WHITE)
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(self.scroll_frame, text="Company Setup", font=ctk.CTkFont(size=22, weight="bold"), text_color=PINK_DARK).pack(pady=(0, 5))
        ctk.CTkLabel(self.scroll_frame, text="Enter your business details once. You won't need to type this again.", font=ctk.CTkFont(size=12), text_color=PINK_TEXT).pack(pady=(0, 15))

        ctk.CTkLabel(self.scroll_frame, text="Business Information", font=ctk.CTkFont(size=15, weight="bold"), text_color=PINK_DARK).pack(anchor="w", pady=(10, 5))

        self.business_name = self._add_field("Business Name *")
        self.owner_name = self._add_field("Business Owner *")
        self.address = self._add_field("Business Address *")
        self.city = self._add_field("City *")
        self.province = self._add_dropdown("Province *", PROVINCES)
        self.postal_code = self._add_field("Postal Code *")
        self.phone = self._add_field("Phone Number *")
        self.email = self._add_field("Email Address *")

        ctk.CTkLabel(self.scroll_frame, text="Banking Details", font=ctk.CTkFont(size=15, weight="bold"), text_color=PINK_DARK).pack(anchor="w", pady=(20, 5))

        self.bank_name = self._add_field("Bank Name *")
        self.account_holder = self._add_field("Account Holder *")
        self.account_number = self._add_field("Account Number *")
        self.branch_code = self._add_field("Branch Code *")
        self.account_type = self._add_field("Account Type (e.g. Savings/Cheque) *")
        self.reference_prefix = self._add_field("Invoice Reference Prefix (e.g. INV)")

        ctk.CTkButton(
            self.scroll_frame, text="Save Company Details", command=self.handle_save,
            height=40, font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=PINK, hover_color=PINK_DARK, text_color=PINK_TEXT
        ).pack(pady=25)

        self._load_existing_data()

    def refresh(self):
        pass

    def _add_field(self, label_text):
        ctk.CTkLabel(self.scroll_frame, text=label_text, anchor="w", text_color=PINK_TEXT).pack(fill="x", padx=5, pady=(8, 0))
        entry = ctk.CTkEntry(self.scroll_frame, width=550, fg_color=WHITE, border_color=PINK, text_color=PINK_TEXT)
        entry.pack(fill="x", padx=5, pady=(2, 0))
        return entry

    def _add_dropdown(self, label_text, options):
        ctk.CTkLabel(self.scroll_frame, text=label_text, anchor="w", text_color=PINK_TEXT).pack(fill="x", padx=5, pady=(8, 0))
        dropdown = ctk.CTkOptionMenu(
            self.scroll_frame, values=options, width=550,
            fg_color=PINK, button_color=PINK_DARK, button_hover_color=PINK_DARK,
            text_color=PINK_TEXT
        )
        dropdown.set(options[0])
        dropdown.pack(fill="x", padx=5, pady=(2, 0))
        return dropdown

    def _load_existing_data(self):
        company = get_company_info()
        if company is None:
            return
        self.business_name.insert(0, company["business_name"])
        self.owner_name.insert(0, company["owner_name"])
        self.address.insert(0, company["address"])
        self.city.insert(0, company["city"])
        if company["province"] in PROVINCES:
            self.province.set(company["province"])
        self.postal_code.insert(0, company["postal_code"])
        self.phone.insert(0, company["phone"])
        self.email.insert(0, company["email"])
        self.bank_name.insert(0, company["bank_name"])
        self.account_holder.insert(0, company["account_holder"])
        self.account_number.insert(0, company["account_number"])
        self.branch_code.insert(0, company["branch_code"])
        self.account_type.insert(0, company["account_type"])
        self.reference_prefix.insert(0, company["reference_prefix"] or "")

    def handle_save(self):
        required_fields = {
            "Business Name": self.business_name.get(),
            "Business Owner": self.owner_name.get(),
            "Business Address": self.address.get(),
            "City": self.city.get(),
            "Postal Code": self.postal_code.get(),
            "Phone Number": self.phone.get(),
            "Email Address": self.email.get(),
            "Bank Name": self.bank_name.get(),
            "Account Holder": self.account_holder.get(),
            "Account Number": self.account_number.get(),
            "Branch Code": self.branch_code.get(),
            "Account Type": self.account_type.get(),
        }

        missing = [name for name, value in required_fields.items() if value.strip() == ""]
        if missing:
            messagebox.showerror("Missing Information", "Please fill in the following required fields:\n\n" + "\n".join(missing))
            return

        city_value = self.city.get().strip()
        if any(char.isdigit() for char in city_value):
            messagebox.showerror("Invalid City", "City should not contain numbers.")
            return

        phone_value = self.phone.get().strip()
        phone_digits = phone_value.replace(" ", "").replace("+", "").replace("-", "")
        if not phone_digits.isdigit():
            messagebox.showerror("Invalid Phone Number", "Phone number should contain only digits, spaces, + or -.")
            return

        postal_value = self.postal_code.get().strip()
        if not postal_value.isdigit():
            messagebox.showerror("Invalid Postal Code", "Postal code should contain only numbers.")
            return

        data = {
            "business_name": self.business_name.get().strip(),
            "owner_name": self.owner_name.get().strip(),
            "address": self.address.get().strip(),
            "city": city_value,
            "province": self.province.get(),
            "postal_code": postal_value,
            "phone": phone_value,
            "email": self.email.get().strip(),
            "logo_path": "",
            "bank_name": self.bank_name.get().strip(),
            "account_holder": self.account_holder.get().strip(),
            "account_number": self.account_number.get().strip(),
            "branch_code": self.branch_code.get().strip(),
            "account_type": self.account_type.get().strip(),
            "reference_prefix": self.reference_prefix.get().strip() or "INV",
            "signature_path": ""
        }

        existing = get_company_info()
        if existing is None:
            save_company_info(data)
        else:
            update_company_info(data)

        messagebox.showinfo("Saved", "Company details saved successfully.")
        self.controller.frames["dashboard"].refresh()