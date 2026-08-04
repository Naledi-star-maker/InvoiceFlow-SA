import os
import customtkinter as ctk
from PIL import Image

from app.database.database import (
    create_tables, create_customers_table,
    create_invoices_table, create_invoice_items_table
)

from app.screens.dashboard import DashboardFrame
from app.screens.invoices import InvoiceFrame
from app.screens.customers import CustomerFrame
from app.screens.settings import SettingsFrame
from app.screens.reports import ReportsFrame

ctk.set_appearance_mode("light")

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"
SIDEBAR_BG = "#FDEFF3"
BORDER_COLOR = "#F5DDE6"
LOGO_PATH = "company_logo/logo.png"


class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("InvoiceFlow SA")
        self.geometry("1180x720")
        self.configure(fg_color=WHITE)

        # Main Sidebar
        sidebar = ctk.CTkFrame(self, fg_color=SIDEBAR_BG, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        if os.path.exists(LOGO_PATH):
            logo_image = ctk.CTkImage(light_image=Image.open(LOGO_PATH), size=(90, 90))
            ctk.CTkLabel(sidebar, image=logo_image, text="").pack(pady=(20, 10))

        ctk.CTkLabel(
            sidebar, 
            text="InvoiceFlow SA", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color=PINK_DARK
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            sidebar, 
            text="Making small\nbusiness invoicing\na breeze!", 
            font=ctk.CTkFont(size=11), 
            text_color=PINK_TEXT, 
            justify="center"
        ).pack(pady=(0, 20))

        nav_buttons = [
            ("Dashboard", "dashboard"),
            ("New Invoice", "invoices"),
            ("Customers", "customers"),
            ("Reports", "reports"),
            ("Company Settings", "settings"),
        ]

        self.nav_button_widgets = {}
        for label, key in nav_buttons:
            btn = ctk.CTkButton(
                sidebar, text=label, width=160, height=38,
                fg_color=WHITE, hover_color="#F5DDE6", text_color=PINK_TEXT,
                border_color=BORDER_COLOR, border_width=1, corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda k=key: self.show_frame(k)
            )
            btn.pack(pady=4)
            self.nav_button_widgets[key] = btn

        self.container = ctk.CTkFrame(self, fg_color=WHITE)
        self.container.pack(side="left", fill="both", expand=True)

        self.frames = {}
        for FrameClass, key in [
            (DashboardFrame, "dashboard"),
            (InvoiceFrame, "invoices"),
            (CustomerFrame, "customers"),
            (ReportsFrame, "reports"),
            (SettingsFrame, "settings"),
        ]:
            frame = FrameClass(self.container, self)
            self.frames[key] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_frame("dashboard")

    def show_frame(self, key):
        frame = self.frames[key]
        if hasattr(frame, "refresh"):
            frame.refresh()
        frame.tkraise()

        # Update button highlights for current active tab
        for k, btn in self.nav_button_widgets.items():
            if k == key:
                btn.configure(fg_color=PINK, text_color=PINK_DARK, border_width=0)
            else:
                btn.configure(fg_color=WHITE, text_color=PINK_TEXT, border_width=1)


if __name__ == "__main__":
    create_tables()
    create_customers_table()
    create_invoices_table()
    create_invoice_items_table()

    app = MainApp()
    app.mainloop()