from tkinter import filedialog

import customtkinter as ctk

from app.database.database import save_company_info, get_company_info, update_company_info
from app.theme import (
    BG,
    DANGER,
    FONT_SIZE,
    TEXT,
    card,
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


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        self.existing_data = None

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll_frame.pack(fill="both", expand=True, padx=24, pady=24)
        self.scroll_frame.grid_columnconfigure(0, weight=1)
        self.scroll_frame.grid_columnconfigure(1, weight=1)
        page_header(
            self.scroll_frame,
            "Company settings",
            "Business details appear on invoices and reports.",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))

        self.business_card = self._group_card(
            "Business details",
            (
                ("business_name", "Business name *"),
                ("owner_name", "Business owner *"),
                ("address", "Business address *"),
                ("city", "City *"),
                ("province", "Province *"),
                ("postal_code", "Postal code *"),
                ("phone", "Phone number *"),
                ("email", "Email address *"),
            ),
        )
        self.business_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 16))
        self.banking_card = self._group_card(
            "Banking details",
            (
                ("bank_name", "Bank name *"),
                ("account_holder", "Account holder *"),
                ("account_number", "Account number *"),
                ("branch_code", "Branch code *"),
                ("account_type", "Account type *"),
                ("reference_prefix", "Invoice reference prefix"),
            ),
        )
        self.banking_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 16))

        self.logo_card = card(self.scroll_frame)
        self.logo_card.grid(row=2, column=0, columnspan=2, sticky="ew")
        ctk.CTkLabel(
            self.logo_card, text="Logo", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        logo_row = ctk.CTkFrame(self.logo_card, fg_color="transparent")
        logo_row.pack(fill="x", padx=16, pady=(0, 16))
        logo_row.grid_columnconfigure(0, weight=1)
        self.logo_path = labeled_entry(
            logo_row, "Optional image path",
            placeholder="Choose a logo image for generated invoices",
        )
        self.logo_path.field_container.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        secondary_button(
            logo_row, "Choose file", command=self._choose_logo,
            height=38, width=110,
        ).grid(row=0, column=1, sticky="e", pady=(22, 0))

        self.error_label = ctk.CTkLabel(
            self.scroll_frame, text="", text_color=DANGER, anchor="w",
            font=font(FONT_SIZE["small"]),
        )
        self.error_label.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.save_button = primary_button(
            self.scroll_frame, "Save company details", command=self.handle_save,
            height=42, width=190,
        )
        self.save_button.grid(row=4, column=0, columnspan=2, pady=(12, 8))
        self._load_existing_data()

    def _group_card(self, title, fields):
        group = card(self.scroll_frame)
        ctk.CTkLabel(
            group, text=title, text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        field_frame = ctk.CTkFrame(group, fg_color="transparent")
        field_frame.pack(fill="x", padx=12, pady=(0, 12))
        field_frame.grid_columnconfigure(0, weight=1)
        field_frame.grid_columnconfigure(1, weight=1)
        for index, (key, label) in enumerate(fields):
            row, column = divmod(index, 2)
            if key == "province":
                widget = labeled_dropdown(field_frame, label, PROVINCES)
                widget.set(PROVINCES[0])
            else:
                widget = labeled_entry(field_frame, label)
            widget.field_container.grid(
                row=row, column=column, sticky="ew", padx=4, pady=6
            )
            setattr(self, key, widget)
        return group

    def refresh(self):
        return

    def _choose_logo(self):
        selected = filedialog.askopenfilename(
            parent=self,
            title="Choose company logo",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if selected:
            self.logo_path.delete(0, "end")
            self.logo_path.insert(0, selected)

    def _load_existing_data(self):
        company = get_company_info()
        self.existing_data = company
        if company is None:
            return
        for name in (
            "business_name", "owner_name", "address", "city", "postal_code",
            "phone", "email", "bank_name", "account_holder", "account_number",
            "branch_code", "account_type", "reference_prefix",
        ):
            getattr(self, name).insert(0, company.get(name) or "")
        if company.get("province") in PROVINCES:
            self.province.set(company["province"])
        self.logo_path.insert(0, company.get("logo_path") or "")

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
        missing = [name for name, value in required_fields.items() if not value.strip()]
        if missing:
            self.error_label.configure(
                text="Please complete: " + ", ".join(missing) + "."
            )
            return
        self.error_label.configure(text="")

        city_value = self.city.get().strip()
        if any(char.isdigit() for char in city_value):
            set_inline_error(self.city, "City should not contain numbers.")
            return
        set_inline_error(self.city, "")

        phone_value = self.phone.get().strip()
        phone_digits = phone_value.replace(" ", "").replace("+", "").replace("-", "")
        if not phone_digits.isdigit():
            set_inline_error(
                self.phone, "Use digits, spaces, +, or - for the phone number."
            )
            return
        set_inline_error(self.phone, "")

        postal_value = self.postal_code.get().strip()
        if not postal_value.isdigit():
            set_inline_error(self.postal_code, "Postal code should contain numbers only.")
            return
        set_inline_error(self.postal_code, "")

        data = {
            "business_name": self.business_name.get().strip(),
            "owner_name": self.owner_name.get().strip(),
            "address": self.address.get().strip(),
            "city": city_value,
            "province": self.province.get(),
            "postal_code": postal_value,
            "phone": phone_value,
            "email": self.email.get().strip(),
            "logo_path": self.logo_path.get().strip(),
            "bank_name": self.bank_name.get().strip(),
            "account_holder": self.account_holder.get().strip(),
            "account_number": self.account_number.get().strip(),
            "branch_code": self.branch_code.get().strip(),
            "account_type": self.account_type.get().strip(),
            "reference_prefix": self.reference_prefix.get().strip() or "INV",
            "signature_path": (
                self.existing_data.get("signature_path", "")
                if self.existing_data else ""
            ),
        }

        if self.existing_data is None:
            save_company_info(data)
        else:
            update_company_info(data)
        self.existing_data = get_company_info()
        self.controller._refresh_business_identity()
        self.controller.frames["dashboard"].refresh()
        toast(self, "Company details saved successfully.", "success")
