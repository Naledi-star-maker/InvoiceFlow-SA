import customtkinter as ctk
from tkinter import messagebox
from database import save_company_info, get_company_info, update_company_info

ctk.set_appearance_mode("light")

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"


class CompanySetupScreen(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("InvoiceFlow SA — Company Setup")
        self.geometry("650x750")
        self.configure(fg_color=WHITE)

        self.scroll_frame = ctk.CTkScrollableFrame(
            self, width=600, height=680, fg_color=WHITE
        )
        self.scroll_frame.pack(padx=20, pady=20, fill="both", expand=True)

        title_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Company Setup",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=PINK_DARK
        )
        title_label.pack(pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            self.scroll_frame,
            text="Enter your business details once. You won't need to type this again.",
            font=ctk.CTkFont(size=12),
            text_color=PINK_TEXT
        )
        subtitle_label.pack(pady=(0, 15))

        section1 = ctk.CTkLabel(
            self.scroll_frame,
            text="Business Information",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=PINK_DARK
        )
        section1.pack(anchor="w", pady=(10, 5))

        self.business_name = self._add_field("Business Name *")
        self.owner_name = self._add_field("Business Owner *")
        self.address = self._add_field("Business Address *")
        self.city = self._add_field("City *")
        self.province = self._add_field("Province *")
        self.postal_code = self._add_field("Postal Code *")
        self.phone = self._add_field("Phone Number *")
        self.email = self._add_field("Email Address *")

        section2 = ctk.CTkLabel(
            self.scroll_frame,
            text="Banking Details",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=PINK_DARK
        )
        section2.pack(anchor="w", pady=(20, 5))

        self.bank_name = self._add_field("Bank Name *")
        self.account_holder = self._add_field("Account Holder *")
        self.account_number = self._add_field("Account Number *")
        self.branch_code = self._add_field("Branch Code *")
        self.account_type = self._add_field("Account Type (e.g. Savings/Cheque) *")
        self.reference_prefix = self._add_field("Invoice Reference Prefix (e.g. INV)")

        self.save_button = ctk.CTkButton(
            self.scroll_frame,
            text="Save Company Details",
            command=self.handle_save,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=PINK,
            hover_color=PINK_DARK,
            text_color=PINK_TEXT
        )
        self.save_button.pack(pady=25)

        self._load_existing_data()

    def _add_field(self, label_text):
        label = ctk.CTkLabel(
            self.scroll_frame, text=label_text, anchor="w", text_color=PINK_TEXT
        )
        label.pack(fill="x", padx=5, pady=(8, 0))

        entry = ctk.CTkEntry(
            self.scroll_frame,
            width=550,
            fg_color=WHITE,
            border_color=PINK,
            text_color=PINK_TEXT
        )
        entry.pack(fill="x", padx=5, pady=(2, 0))

        return entry

    def _load_existing_data(self):
        company = get_company_info()
        if company is None:
            return

        self.business_name.insert(0, company["business_name"])
        self.owner_name.insert(0, company["owner_name"])
        self.address.insert(0, company["address"])
        self.city.insert(0, company["city"])
        self.province.insert(0, company["province"])
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
            "Province": self.province.get(),
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
            messagebox.showerror(
                "Missing Information",
                "Please fill in the following required fields:\n\n" + "\n".join(missing)
            )
            return

        data = {
            "business_name": self.business_name.get().strip(),
            "owner_name": self.owner_name.get().strip(),
            "address": self.address.get().strip(),
            "city": self.city.get().strip(),
            "province": self.province.get().strip(),
            "postal_code": self.postal_code.get().strip(),
            "phone": self.phone.get().strip(),
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


if __name__ == "__main__":
    app = CompanySetupScreen()
    app.mainloop()