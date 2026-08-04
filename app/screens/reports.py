import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.database.database import (
    get_total_customers, get_total_invoices, get_total_revenue, get_monthly_revenue
)

PINK = "#F8C8DC"
PINK_DARK = "#F4A6C6"
PINK_TEXT = "#C38699"
WHITE = "#FFFFFF"


class ReportsFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=WHITE)
        self.controller = controller

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=WHITE)
        self.scroll.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        for widget in self.scroll.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.scroll, text="Business Reports", font=ctk.CTkFont(size=26, weight="bold"), text_color=PINK_DARK).pack(pady=20)

        cards = ctk.CTkFrame(self.scroll, fg_color=WHITE)
        cards.pack(fill="x", padx=20)

        self.create_card(cards, "Customers", get_total_customers())
        self.create_card(cards, "Invoices", get_total_invoices())
        self.create_card(cards, "Revenue", f"R {get_total_revenue():,.2f}")

        revenue = get_monthly_revenue()

        ctk.CTkLabel(self.scroll, text="Monthly Revenue Chart", font=ctk.CTkFont(size=18, weight="bold"), text_color=PINK_DARK).pack(anchor="w", padx=20, pady=(30, 10))

        chart_frame = ctk.CTkFrame(self.scroll, fg_color=WHITE)
        chart_frame.pack(fill="x", padx=20, pady=(0, 10))

        if len(revenue) == 0:
            ctk.CTkLabel(chart_frame, text="No invoices yet — chart will appear once you have data.", text_color=PINK_TEXT).pack(pady=20)
        else:
            months = [r["month"] for r in revenue]
            values = [r["revenue"] for r in revenue]

            fig = Figure(figsize=(8, 3.2), dpi=100)
            fig.patch.set_facecolor("#FFFFFF")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#FFFFFF")

            bars = ax.bar(months, values, color="#F4A6C6", edgecolor="#C38699")
            ax.set_ylabel("Revenue (R)", color="#C38699", fontsize=9)
            ax.tick_params(axis="x", colors="#C38699", labelsize=8)
            ax.tick_params(axis="y", colors="#C38699", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#F4A6C6")

            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"R{value:,.0f}", ha="center", va="bottom", fontsize=8, color="#3A2A30")

            fig.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x")

        ctk.CTkLabel(self.scroll, text="Monthly Revenue Breakdown", font=ctk.CTkFont(size=18, weight="bold"), text_color=PINK_DARK).pack(anchor="w", padx=20, pady=(20, 10))

        if len(revenue) == 0:
            ctk.CTkLabel(self.scroll, text="No invoices yet.", text_color=PINK_TEXT).pack(pady=20)
        else:
            for month in revenue:
                row = ctk.CTkFrame(self.scroll, fg_color="#FDEFF3")
                row.pack(fill="x", padx=20, pady=5)
                ctk.CTkLabel(row, text=month["month"], text_color=PINK_TEXT).pack(side="left", padx=15, pady=10)
                ctk.CTkLabel(row, text=f"R {month['revenue']:,.2f}", text_color=PINK_DARK, font=ctk.CTkFont(weight="bold")).pack(side="right", padx=15)

    def create_card(self, parent, title, value):
        card = ctk.CTkFrame(parent, width=220, height=100, fg_color="#FDEFF3")
        card.pack(side="left", padx=10)
        card.pack_propagate(False)
        ctk.CTkLabel(card, text=title, text_color=PINK_TEXT).pack(pady=(18, 5))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=22, weight="bold"), text_color=PINK_DARK).pack()