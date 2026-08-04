import customtkinter as ctk
from datetime import datetime
from app.database.database import get_all_customers, get_all_invoices, get_company_info

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"
CARD_BG = "#FDEFF3"
BORDER_COLOR = "#F5DDE6"


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=WHITE)
        self.controller = controller

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=WHITE)
        self.scroll.pack(fill="both", expand=True, padx=30, pady=25)

        # Welcome Section
        self.welcome_label = ctk.CTkLabel(
            self.scroll, 
            text="", 
            font=ctk.CTkFont(size=24, weight="bold"), 
            text_color=PINK_DARK
        )
        self.welcome_label.pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            self.scroll, 
            text="Here's what's happening with your invoices.", 
            font=ctk.CTkFont(size=13), 
            text_color=PINK_TEXT
        ).pack(anchor="w", pady=(0, 20))

        # Metrics Container
        self.cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.cards_frame.pack(fill="x", pady=(0, 25))

        # Quick Actions Section
        ctk.CTkLabel(
            self.scroll, 
            text="Quick Actions", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color=PINK_DARK
        ).pack(anchor="w", pady=(5, 10))

        actions_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(0, 25))

        ctk.CTkButton(
            actions_frame, text="+ New Invoice", height=42, width=170,
            command=lambda: controller.show_frame("invoices"),
            fg_color=PINK_DARK, hover_color="#E895B5", text_color=WHITE,
            corner_radius=10, font=ctk.CTkFont(size=13, weight="bold")
        ).pack(side="left", padx=(0, 12))

        for text, frame_key in [
            ("Manage Invoices", "manage_invoices"),
            ("Manage Customers", "customers"),
            ("View Reports", "reports"),
            ("Company Settings", "settings")
        ]:
            ctk.CTkButton(
                actions_frame, text=text, height=42, width=170,
                command=lambda k=frame_key: controller.show_frame(k),
                fg_color=CARD_BG, hover_color="#F5DDE6", text_color=PINK_TEXT,
                border_color=BORDER_COLOR, border_width=1, corner_radius=10,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(side="left", padx=(0, 12))

        # Recent Invoices Section
        ctk.CTkLabel(
            self.scroll, 
            text="Recent Invoices", 
            font=ctk.CTkFont(size=16, weight="bold"), 
            text_color=PINK_DARK
        ).pack(anchor="w", pady=(5, 10))

        self.recent_frame = ctk.CTkFrame(
            self.scroll, 
            fg_color=WHITE, 
            border_color=BORDER_COLOR, 
            border_width=1.5, 
            corner_radius=12
        )
        self.recent_frame.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        company = get_company_info()
        business_name = company["business_name"] if company else "Your Business"
        self.welcome_label.configure(text=f"Welcome back, {business_name}!")

        # Reset stat cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        stats = self._calculate_stats()
        self._add_stat_card(self.cards_frame, "Total Customers", str(stats["total_customers"]))
        self._add_stat_card(self.cards_frame, "Total Invoices", str(stats["total_invoices"]))
        self._add_stat_card(self.cards_frame, "Invoices This Month", str(stats["invoices_this_month"]))
        self._add_stat_card(self.cards_frame, "Revenue This Month", f"R{stats['revenue_this_month']:.2f}")

        # Reset recent invoices
        for widget in self.recent_frame.winfo_children():
            widget.destroy()

        invoices = get_all_invoices()[:8]

        if not invoices:
            ctk.CTkLabel(
                self.recent_frame, 
                text="No invoices yet. Create your first invoice to get started!", 
                text_color=PINK_TEXT,
                font=ctk.CTkFont(size=13)
            ).pack(pady=30)
        else:
            # Header
            header = ctk.CTkFrame(self.recent_frame, fg_color=CARD_BG, corner_radius=8)
            header.pack(fill="x", padx=6, pady=6)
            
            ctk.CTkLabel(header, text="Invoice #", text_color=PINK_DARK, width=140, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(header, text="Customer", text_color=PINK_DARK, width=250, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=12)
            ctk.CTkLabel(header, text="Date", text_color=PINK_DARK, width=120, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=12)
            ctk.CTkLabel(header, text="Total", text_color=PINK_DARK, width=100, anchor="e", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=12)

            # Rows
            for index, invoice in enumerate(invoices):
                bg = WHITE if index % 2 == 0 else CARD_BG
                row = ctk.CTkFrame(self.recent_frame, fg_color=bg, corner_radius=6)
                row.pack(fill="x", padx=6, pady=2)
                
                ctk.CTkLabel(row, text=invoice["invoice_number"], text_color=PINK_TEXT, width=140, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(row, text=invoice["customer_name"], text_color=PINK_TEXT, width=250, anchor="w").pack(side="left", padx=12)
                ctk.CTkLabel(row, text=invoice["invoice_date"], text_color=PINK_TEXT, width=120, anchor="w").pack(side="left", padx=12)
                ctk.CTkLabel(row, text=f"R{invoice['total']:.2f}", text_color=PINK_DARK, width=100, anchor="e", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=12)

    def _add_stat_card(self, parent, label_text, value_text):
        # Structured Card Container
        card = ctk.CTkFrame(
            parent, 
            fg_color=CARD_BG, 
            border_color=BORDER_COLOR, 
            border_width=1, 
            corner_radius=12, 
            width=200, 
            height=100
        )
        card.pack(side="left", padx=(0, 15))
        card.pack_propagate(False)

        # Center content cleanly inside card
        inner_frame = ctk.CTkFrame(card, fg_color="transparent")
        inner_frame.pack(expand=True, fill="both", pady=10)

        ctk.CTkLabel(
            inner_frame, 
            text=value_text, 
            font=ctk.CTkFont(size=22, weight="bold"), 
            text_color=PINK_DARK
        ).pack()
        
        ctk.CTkLabel(
            inner_frame, 
            text=label_text, 
            font=ctk.CTkFont(size=11), 
            text_color=PINK_TEXT
        ).pack(pady=(2, 0))

    def _calculate_stats(self):
        customers = get_all_customers()
        invoices = get_all_invoices()
        current_month = datetime.now().strftime("%Y-%m")
        invoices_this_month = [i for i in invoices if i["invoice_date"].startswith(current_month)]
        revenue_this_month = sum(i["total"] for i in invoices_this_month)
        return {
            "total_customers": len(customers),
            "total_invoices": len(invoices),
            "invoices_this_month": len(invoices_this_month),
            "revenue_this_month": revenue_this_month
        }