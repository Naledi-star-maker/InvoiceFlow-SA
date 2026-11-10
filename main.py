import os

import customtkinter as ctk
from PIL import Image

from app.database.database import (
    create_customers_table,
    create_invoice_items_table,
    create_invoices_table,
    create_tables,
    get_company_info,
)
from app.screens.customers import CustomerFrame
from app.screens.dashboard import DashboardFrame
from app.screens.invoices import InvoiceFrame
from app.screens.manage_invoices import ManageInvoiceFrame
from app.screens.reports import ReportsFrame
from app.screens.settings import SettingsFrame
from app.theme import (
    BG,
    FONT_SIZE,
    MUTED,
    SIDEBAR,
    SIDEBAR_ACTIVE,
    SIDEBAR_HOVER,
    SIDEBAR_TEXT,
    SURFACE,
    TEXT,
    font,
)


LOGO_PATH = os.path.join("company_logo", "logo.png")


class MainApp(ctk.CTk):
    NAV_GROUPS = (
        ("OVERVIEW", (("▦", "Dashboard", "dashboard"), ("▤", "Reports", "reports"))),
        ("BILLING", (("＋", "New Invoice", "invoices"), ("≡", "Manage Invoices", "manage_invoices"))),
        ("PEOPLE", (("◉", "Customers", "customers"),)),
    )

    def __init__(self):
        super().__init__()
        self.title("InvoiceFlow SA")
        self.geometry("1180x720")
        self.minsize(900, 600)
        self.configure(fg_color=BG)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        ctk.set_appearance_mode("light")

        self.sidebar = ctk.CTkFrame(self, width=232, fg_color=SIDEBAR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(1, weight=1)

        self._build_brand()
        self.nav_area = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_area.grid(row=1, column=0, sticky="nsew", padx=12, pady=(16, 8))
        self.nav_area.grid_columnconfigure(0, weight=1)
        self.nav_button_widgets = {}
        self.nav_indicators = {}
        self._build_navigation()
        self._build_sidebar_footer()

        self.container = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

        self.frames = {}
        for frame_class, key in (
            (DashboardFrame, "dashboard"),
            (InvoiceFrame, "invoices"),
            (ManageInvoiceFrame, "manage_invoices"),
            (CustomerFrame, "customers"),
            (ReportsFrame, "reports"),
            (SettingsFrame, "settings"),
        ):
            frame = frame_class(self.container, self)
            self.frames[key] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("dashboard")

    def _build_brand(self):
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=20, pady=(24, 8))
        if os.path.exists(LOGO_PATH):
            logo = ctk.CTkImage(light_image=Image.open(LOGO_PATH), size=(40, 40))
            ctk.CTkLabel(brand, image=logo, text="").pack(side="left", padx=(0, 10))
            self._logo_image = logo
        ctk.CTkLabel(
            brand,
            text="InvoiceFlow SA",
            text_color=SURFACE,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(side="left", anchor="center")

    def _build_navigation(self):
        row = 0
        for section, items in self.NAV_GROUPS:
            ctk.CTkLabel(
                self.nav_area,
                text=section,
                text_color=MUTED,
                font=font(FONT_SIZE["small"], "bold"),
                anchor="w",
            ).grid(row=row, column=0, sticky="ew", padx=12, pady=(16, 6))
            row += 1
            for icon, label, key in items:
                self._add_nav_item(self.nav_area, row, icon, label, key)
                row += 1

    def _add_nav_item(self, parent, row, icon, label, key):
        item = ctk.CTkFrame(parent, height=40, fg_color="transparent", corner_radius=8)
        item.grid(row=row, column=0, sticky="ew", pady=2)
        item.grid_columnconfigure(1, weight=1)
        item.grid_propagate(False)
        indicator = ctk.CTkFrame(
            item, width=3, height=40, fg_color="transparent", corner_radius=0
        )
        indicator.grid(row=0, column=0, sticky="nsw")
        button = ctk.CTkButton(
            item,
            text=f"{icon}   {label}",
            anchor="w",
            height=40,
            fg_color="transparent",
            hover_color=SIDEBAR_HOVER,
            text_color=SIDEBAR_TEXT,
            corner_radius=8,
            font=font(FONT_SIZE["body"]),
            command=lambda nav_key=key: self.show_frame(nav_key),
        )
        button.grid(row=0, column=1, sticky="ew", padx=(5, 6))
        self.nav_button_widgets[key] = button
        self.nav_indicators[key] = (item, indicator)

    def _build_sidebar_footer(self):
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="sew", padx=12, pady=(8, 16))
        footer.grid_columnconfigure(0, weight=1)

        settings_row = ctk.CTkFrame(footer, height=40, fg_color="transparent", corner_radius=8)
        settings_row.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        settings_row.grid_columnconfigure(1, weight=1)
        settings_row.grid_propagate(False)
        indicator = ctk.CTkFrame(
            settings_row, width=3, height=40,
            fg_color="transparent", corner_radius=0,
        )
        indicator.grid(row=0, column=0, sticky="nsw")
        settings_button = ctk.CTkButton(
            settings_row,
            text="⚙   Company Settings",
            anchor="w",
            height=40,
            fg_color="transparent",
            hover_color=SIDEBAR_HOVER,
            text_color=SIDEBAR_TEXT,
            corner_radius=8,
            font=font(FONT_SIZE["body"]),
            command=lambda: self.show_frame("settings"),
        )
        settings_button.grid(row=0, column=1, sticky="ew", padx=(5, 6))
        self.nav_button_widgets["settings"] = settings_button
        self.nav_indicators["settings"] = (settings_row, indicator)

        account = ctk.CTkFrame(footer, fg_color=SIDEBAR_ACTIVE, corner_radius=8)
        account.grid(row=1, column=0, sticky="ew")
        account.grid_columnconfigure(1, weight=1)
        self.avatar = ctk.CTkLabel(
            account, text="?", width=34, height=34, corner_radius=17,
            fg_color="#3F3F46", text_color=SURFACE,
            font=font(FONT_SIZE["small"], "bold"),
        )
        self.avatar.grid(row=0, column=0, padx=10, pady=10)
        self.business_label = ctk.CTkLabel(
            account, text="Your Business", text_color=SURFACE,
            font=font(FONT_SIZE["small"], "bold"), anchor="w",
        )
        self.business_label.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self._refresh_business_identity()

    def _refresh_business_identity(self):
        company = get_company_info()
        business_name = company["business_name"].strip() if company else "Your Business"
        initials = "".join(part[0] for part in business_name.split()[:2]) or "?"
        self.business_label.configure(text=business_name)
        self.avatar.configure(text=initials.upper())

    def show_frame(self, key):
        frame = self.frames[key]
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()
        self._refresh_business_identity()

        for nav_key, button in self.nav_button_widgets.items():
            active = nav_key == key
            item, indicator = self.nav_indicators[nav_key]
            button.configure(
                text_color=SURFACE if active else SIDEBAR_TEXT,
                fg_color=SIDEBAR_ACTIVE if active else "transparent",
            )
            item.configure(fg_color=SIDEBAR_ACTIVE if active else "transparent")
            indicator.configure(fg_color="#DB2777" if active else "transparent")


if __name__ == "__main__":
    create_tables()
    create_customers_table()
    create_invoices_table()
    create_invoice_items_table()
    app = MainApp()
    app.mainloop()
