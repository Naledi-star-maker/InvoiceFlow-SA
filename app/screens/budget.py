import calendar
import math
import sqlite3
from datetime import date

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from app.database.database import (
    DEFAULT_EXPENSE_CATEGORIES,
    add_expense,
    add_expense_category,
    delete_expense,
    get_expense_categories,
    get_month_summary,
    set_monthly_budget,
    update_expense,
)
from app.services.accounting_book import (
    generate_accounting_book,
    generate_accounting_insights,
)
from app.theme import (
    BG,
    BORDER,
    DANGER,
    FONT_SIZE,
    PINK,
    SECONDARY,
    SUCCESS,
    SURFACE,
    TEXT,
    card,
    confirm_dialog,
    data_table,
    empty_state,
    font,
    labeled_dropdown,
    labeled_entry,
    page_header,
    primary_button,
    secondary_button,
    set_inline_error,
    stat_card,
    toast,
)
from app.utils import format_currency


CHART_COLORS = (
    PINK, "#8B5CF6", "#0891B2", "#F59E0B", "#16A34A",
    "#EF4444", "#6366F1", "#14B8A6", "#D946EF", "#78716C",
)


class BudgetFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        today = date.today()
        self._summary = {}
        self._expense_rows = []
        self._chart_figure = None
        self._chart = None

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)
        self.scroll.grid_columnconfigure(0, weight=1)
        page_header(
            self.scroll,
            "Budget & Expenses",
            "Plan a monthly budget, record expenses, and see how your business is doing.",
            actions=self._add_export_button,
        ).pack(fill="x", pady=(0, 16))

        month_card = card(self.scroll)
        month_card.pack(fill="x", pady=(0, 16))
        month_row = ctk.CTkFrame(month_card, fg_color="transparent")
        month_row.pack(fill="x", padx=16, pady=14)
        ctk.CTkLabel(
            month_row, text="Viewing month", text_color=SECONDARY,
            font=font(FONT_SIZE["label"], "bold"),
        ).pack(side="left", padx=(0, 10))
        self.month_selector = ctk.CTkOptionMenu(
            month_row,
            values=[calendar.month_name[month] for month in range(1, 13)],
            command=lambda _value: self.refresh(),
        )
        self.month_selector.set(calendar.month_name[today.month])
        self.month_selector.pack(side="left", padx=(0, 12))
        self.year_selector = ctk.CTkOptionMenu(
            month_row,
            values=[str(year) for year in range(2000, today.year + 2)],
            command=lambda _value: self.refresh(),
        )
        self.year_selector.set(str(today.year))
        self.year_selector.pack(side="left")

        self._build_budget_section()
        self._build_expense_form()
        self._build_chart_section()
        self._build_budget_actual_section()
        self._build_month_summary_section()
        self._build_insights_section()
        self._build_expense_list_section()
        self.refresh()

    def _add_export_button(self, parent):
        primary_button(
            parent,
            "Download monthly accounting book",
            command=self._export_accounting_book,
            width=260,
            height=40,
        ).grid(row=0, column=0, sticky="e")

    def _build_budget_section(self):
        section = card(self.scroll)
        section.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            section, text="1. Set budget", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        row = ctk.CTkFrame(section, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 16))
        self.budget_category = labeled_dropdown(row, "Category", [])
        self.budget_category.field_container.grid(
            row=0, column=0, sticky="ew", padx=(0, 12)
        )
        row.grid_columnconfigure(0, weight=2)
        self.budget_amount = labeled_entry(row, "Monthly budget (R)")
        self.budget_amount.field_container.grid(
            row=0, column=1, sticky="ew", padx=(0, 12)
        )
        row.grid_columnconfigure(1, weight=1)
        self.save_budget_button = secondary_button(
            row, "Save budget", command=self._save_budget,
            width=120, height=38,
        )
        self.save_budget_button.grid(row=0, column=2, sticky="e", pady=(22, 0))

        custom_row = ctk.CTkFrame(section, fg_color="transparent")
        custom_row.pack(fill="x", padx=16, pady=(0, 16))
        self.new_category_entry = labeled_entry(
            custom_row, "Add your own category", placeholder="For example: Insurance"
        )
        self.new_category_entry.field_container.pack(
            side="left", fill="x", expand=True, padx=(0, 12)
        )
        secondary_button(
            custom_row, "Add category", command=self._add_category,
            width=130, height=38,
        ).pack(side="right", pady=(22, 0))

    def _build_expense_form(self):
        section = card(self.scroll)
        section.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            section, text="2. Add expense", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        row = ctk.CTkFrame(section, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 8))
        row.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.expense_date = labeled_entry(
            row, "Date", placeholder="YYYY-MM-DD"
        )
        self.expense_date.field_container.grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        self.expense_date.insert(0, date.today().isoformat())
        self.expense_category = labeled_dropdown(row, "Category", [])
        self.expense_category.field_container.grid(
            row=0, column=1, sticky="ew", padx=(0, 10)
        )
        self.expense_description = labeled_entry(row, "Description")
        self.expense_description.field_container.grid(
            row=0, column=2, sticky="ew", padx=(0, 10)
        )
        self.expense_amount = labeled_entry(row, "Amount (R)")
        self.expense_amount.field_container.grid(
            row=0, column=3, sticky="ew"
        )
        self.expense_error = ctk.CTkLabel(
            section, text="", text_color=DANGER, anchor="w",
            font=font(FONT_SIZE["small"]),
        )
        self.expense_error.pack(fill="x", padx=16, pady=(0, 8))
        primary_button(
            section, "Add expense", command=self._save_expense,
            width=130, height=38,
        ).pack(anchor="e", padx=16, pady=(0, 16))

    def _build_chart_section(self):
        section = card(self.scroll)
        section.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            section, text="3. Where your money goes", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.chart_container = ctk.CTkFrame(section, fg_color=SURFACE)
        self.chart_container.pack(fill="x", padx=12, pady=(0, 12))

    def _build_budget_actual_section(self):
        self.budget_actual_card = card(self.scroll)
        self.budget_actual_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            self.budget_actual_card, text="4. Budget vs actual",
            text_color=TEXT, font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.budget_actual_table_frame = ctk.CTkFrame(
            self.budget_actual_card, fg_color="transparent"
        )
        self.budget_actual_table_frame.pack(fill="x", padx=8, pady=(0, 8))

    def _build_month_summary_section(self):
        section = card(self.scroll)
        section.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            section, text="5. Month summary", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.summary_cards = ctk.CTkFrame(section, fg_color="transparent")
        self.summary_cards.pack(fill="x", padx=12, pady=(0, 12))
        for column in range(5):
            self.summary_cards.grid_columnconfigure(column, weight=1)

    def _build_insights_section(self):
        self.insights_card = card(self.scroll)
        self.insights_card.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            self.insights_card, text="6. Things to improve", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.insights_content = ctk.CTkFrame(
            self.insights_card, fg_color="transparent"
        )
        self.insights_content.pack(fill="x", padx=16, pady=(0, 12))

    def _build_expense_list_section(self):
        section = card(self.scroll)
        section.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            section, text="Expenses this month", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.expense_list = ctk.CTkScrollableFrame(
            section, fg_color=SURFACE, height=260
        )
        self.expense_list.pack(fill="x", padx=8, pady=(0, 8))

    def _selected_year_month(self):
        month = list(calendar.month_name).index(self.month_selector.get())
        return int(self.year_selector.get()), month

    def refresh(self):
        year, month = self._selected_year_month()
        self._summary = get_month_summary(year, month)
        categories = sorted(
            set(DEFAULT_EXPENSE_CATEGORIES) | set(get_expense_categories()),
            key=str.casefold,
        )
        for dropdown in (self.budget_category, self.expense_category):
            dropdown.configure(values=categories)
            if categories and dropdown.get() not in categories:
                dropdown.set(categories[0])
        self._render_chart()
        self._render_budget_actual()
        self._render_month_summary()
        self._render_insights()
        self._render_expense_list()
        self.scroll.update_idletasks()
        self.scroll._parent_canvas.configure(
            scrollregion=self.scroll._parent_canvas.bbox("all")
        )

    def _save_budget(self):
        category = self.budget_category.get()
        try:
            amount = float(self.budget_amount.get())
        except ValueError:
            set_inline_error(self.budget_amount, "Enter a valid budget amount.")
            return
        if not math.isfinite(amount) or amount < 0:
            set_inline_error(
                self.budget_amount, "Budget must be a non-negative amount."
            )
            return
        set_inline_error(self.budget_amount, "")
        year, month = self._selected_year_month()
        try:
            set_monthly_budget(f"{year:04d}-{month:02d}", category, amount)
        except (ValueError, sqlite3.Error) as error:
            toast(self, f"Budget could not be saved: {error}", "error")
            return
        self.budget_amount.delete(0, "end")
        self.refresh()
        toast(self, f"{category} budget saved.", "success")

    def _add_category(self):
        category = self.new_category_entry.get().strip()
        try:
            add_expense_category(category)
        except (ValueError, sqlite3.Error) as error:
            toast(self, f"Category could not be added: {error}", "error")
            return
        self.new_category_entry.delete(0, "end")
        self.refresh()
        self.expense_category.set(category)
        self.budget_category.set(category)
        toast(self, f"{category} category added.", "success")

    def _save_expense(self):
        expense_date = self.expense_date.get().strip()
        try:
            parsed_date = date.fromisoformat(expense_date)
            if parsed_date.isoformat() != expense_date:
                raise ValueError("Use YYYY-MM-DD format.")
        except ValueError:
            set_inline_error(
                self.expense_date, "Enter a valid date in YYYY-MM-DD format."
            )
            return
        set_inline_error(self.expense_date, "")
        description = self.expense_description.get().strip()
        if not description:
            set_inline_error(self.expense_description, "Enter a description.")
            return
        set_inline_error(self.expense_description, "")
        try:
            amount = float(self.expense_amount.get())
        except ValueError:
            set_inline_error(self.expense_amount, "Enter a valid amount.")
            return
        if not math.isfinite(amount) or amount <= 0:
            set_inline_error(
                self.expense_amount, "Amount must be greater than zero."
            )
            return
        set_inline_error(self.expense_amount, "")
        try:
            add_expense(
                expense_date, self.expense_category.get(), description, amount
            )
        except (ValueError, sqlite3.Error) as error:
            self.expense_error.configure(text=f"Expense could not be saved: {error}")
            return
        self.expense_error.configure(text="")
        self.expense_description.delete(0, "end")
        self.expense_amount.delete(0, "end")
        self.refresh()
        toast(self, "Expense added.", "success")

    def _render_chart(self):
        self.chart_container.unbind("<Configure>")
        for child in self.chart_container.winfo_children():
            child.destroy()
        spending = self._summary["spending_by_category"]
        total = self._summary["total_expenses"]
        if not spending or total <= 0:
            empty_state(self.chart_container, "Add an expense to see spending by category.")
            self._chart = None
            self._chart_figure = None
            return

        categories = list(spending)
        amounts = [spending[category] for category in categories]
        figure = Figure(figsize=(8, 3.2), dpi=100)
        figure.patch.set_facecolor(SURFACE)
        axis = figure.add_subplot(111)
        axis.pie(
            amounts,
            colors=[CHART_COLORS[index % len(CHART_COLORS)] for index in range(len(categories))],
            startangle=90,
            counterclock=False,
            wedgeprops={"width": 0.42, "edgecolor": SURFACE},
            autopct=lambda value: f"{value:.0f}%" if value >= 3 else "",
            pctdistance=0.78,
            textprops={"color": TEXT, "fontsize": 8},
        )
        axis.legend(
            [
                f"{category}: {format_currency(amount)} "
                f"({amount / total:.0%})"
                for category, amount in zip(categories, amounts)
            ],
            loc="center left",
            bbox_to_anchor=(0.95, 0.5),
            frameon=False,
            fontsize=8,
        )
        figure.tight_layout()
        chart = FigureCanvasTkAgg(figure, master=self.chart_container)
        chart.draw()
        chart_widget = chart.get_tk_widget()
        chart_widget.pack(fill="x")
        chart_widget.bind("<MouseWheel>", self._scroll_chart_wheel)

        def resize_chart(event):
            if event.width <= 0:
                return
            width = max(event.width / 100, 4)
            if abs(width - figure.get_figwidth()) >= 0.05:
                figure.set_size_inches(width, 3.2, forward=True)
                chart.draw_idle()

        self.chart_container.bind("<Configure>", resize_chart)
        self._chart_figure = figure
        self._chart = chart

    def _scroll_chart_wheel(self, event):
        self.scroll._parent_canvas.yview_scroll(int(-event.delta / 120), "units")
        return "break"

    def _render_budget_actual(self):
        for child in self.budget_actual_table_frame.winfo_children():
            child.destroy()
        categories = sorted(
            set(DEFAULT_EXPENSE_CATEGORIES)
            | set(get_expense_categories())
            | set(self._summary["categories"]),
            key=str.casefold,
        )
        rows = []
        percentages = []
        for category in categories:
            budget = self._summary["budgets"].get(category, 0)
            spent = self._summary["spending_by_category"].get(category, 0)
            remaining = budget - spent
            used = spent / budget * 100 if budget else (100 if spent else 0)
            percent_label = f"{used:.0f}%" if budget else ("Over budget" if spent else "—")
            rows.append((
                category, format_currency(budget), format_currency(spent),
                format_currency(remaining), percent_label,
            ))
            percentages.append(used if budget or spent else None)

        table = data_table(
            self.budget_actual_table_frame,
            [
                {"label": "Category", "weight": 2},
                {"label": "Budget", "weight": 1, "anchor": "e"},
                {"label": "Spent", "weight": 1, "anchor": "e"},
                {"label": "Remaining", "weight": 1, "anchor": "e"},
                {"label": "% used", "weight": 1, "anchor": "e"},
            ],
            rows,
            empty_text="Set a budget or add an expense to get started.",
        )
        table.pack(fill="x")
        row_index = 0
        for table_row in table.winfo_children()[1:]:
            labels = table_row.winfo_children()
            if len(labels) != len(rows[0]):
                continue
            percent = percentages[row_index]
            row_index += 1
            if percent is None:
                continue
            color = SUCCESS if percent < 80 else "#D97706" if percent <= 100 else DANGER
            labels[-1].configure(text_color=color)

    def _render_month_summary(self):
        for child in self.summary_cards.winfo_children():
            child.destroy()
        summary = self._summary
        profit = summary["income_received"] - summary["total_expenses"]
        previous = summary["previous_month_expenses"]
        current = summary["total_expenses"]
        if previous:
            change = (current - previous) / previous * 100
            change_text = f"{change:+.1f}% expenses vs previous month"
        elif current:
            change_text = "No expenses in previous month"
        else:
            change_text = "No expenses to compare"
        metrics = (
            ("Income invoiced", summary["income_invoiced"], "Invoices issued this month", TEXT),
            ("Income received", summary["income_received"], "Payments received this month", SUCCESS),
            ("Total expenses", current, "Expenses dated this month", DANGER),
            ("Profit", profit, "Received minus expenses", SUCCESS if profit >= 0 else DANGER),
            ("Month-over-month", change_text, "Expense change", PINK),
        )
        for column, (label, value, caption, accent) in enumerate(metrics):
            display = value if isinstance(value, str) else format_currency(value)
            stat_card(
                self.summary_cards, label, display, caption, accent=accent,
                width=150, height=112,
            ).grid(row=0, column=column, sticky="ew", padx=4, pady=4)

    def _generate_insights(self):
        return generate_accounting_insights(self._summary)

    def _render_insights(self):
        for child in self.insights_content.winfo_children():
            child.destroy()
        for insight in self._generate_insights():
            ctk.CTkLabel(
                self.insights_content,
                text=f"•  {insight}",
                text_color=SECONDARY,
                font=font(FONT_SIZE["body"]),
                anchor="w",
                justify="left",
                wraplength=900,
            ).pack(fill="x", pady=4)

    def _render_expense_list(self):
        for child in self.expense_list.winfo_children():
            child.destroy()
        expenses = self._summary["expenses"]
        if not expenses:
            empty_state(self.expense_list, "No expenses recorded for this month.")
            return

        header = ctk.CTkFrame(self.expense_list, fg_color=SURFACE)
        header.pack(fill="x")
        for column, (label, weight, anchor) in enumerate((
            ("Date", 1, "w"), ("Category", 1, "w"),
            ("Description", 3, "w"), ("Amount", 1, "e"),
        )):
            header.grid_columnconfigure(column, weight=weight)
            ctk.CTkLabel(
                header, text=label, text_color=SECONDARY, anchor=anchor,
                font=font(FONT_SIZE["small"], "bold"),
            ).grid(row=0, column=column, sticky="ew", padx=8, pady=10)
        header.grid_columnconfigure(4, weight=1)
        for expense in expenses:
            row = ctk.CTkFrame(self.expense_list, fg_color=SURFACE)
            row.pack(fill="x")
            values = (
                expense["expense_date"],
                expense["category"],
                expense["description"],
                format_currency(expense["amount"]),
            )
            for column, (value, anchor) in enumerate(zip(values, ("w", "w", "w", "e"))):
                row.grid_columnconfigure(column, weight=(3 if column == 2 else 1))
                ctk.CTkLabel(
                    row, text=value, text_color=TEXT, anchor=anchor,
                    font=font(FONT_SIZE["small"]),
                ).grid(row=0, column=column, sticky="ew", padx=8, pady=9)
            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.grid(row=0, column=4, padx=8, pady=4)
            secondary_button(
                actions, "Edit", command=lambda item=expense: self._edit_expense(item),
                width=62, height=30,
            ).pack(side="left", padx=(0, 6))
            secondary_button(
                actions, "Delete",
                command=lambda item=expense: self._delete_expense(item),
                width=72, height=30,
            ).pack(side="left")
            ctk.CTkFrame(self.expense_list, height=1, fg_color=BORDER).pack(fill="x")

    def _edit_expense(self, expense):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit expense")
        dialog.geometry("440x420")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        date_entry = labeled_entry(form, "Date", placeholder="YYYY-MM-DD")
        date_entry.field_container.pack(fill="x", pady=(0, 10))
        date_entry.insert(0, expense["expense_date"])
        category_entry = labeled_dropdown(
            form,
            "Category",
            sorted(
                set(DEFAULT_EXPENSE_CATEGORIES) | set(get_expense_categories()),
                key=str.casefold,
            ),
        )
        category_entry.field_container.pack(fill="x", pady=(0, 10))
        category_entry.set(expense["category"])
        description_entry = labeled_entry(form, "Description")
        description_entry.field_container.pack(fill="x", pady=(0, 10))
        description_entry.insert(0, expense["description"])
        amount_entry = labeled_entry(form, "Amount (R)")
        amount_entry.field_container.pack(fill="x", pady=(0, 10))
        amount_entry.insert(0, str(expense["amount"]))
        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.pack(fill="x", pady=(8, 0))
        secondary_button(
            actions, "Cancel", command=dialog.destroy, width=90,
        ).pack(side="right", padx=(8, 0))

        def save_changes():
            value = date_entry.get().strip()
            try:
                parsed = date.fromisoformat(value)
                if parsed.isoformat() != value:
                    raise ValueError("Invalid date format.")
            except ValueError:
                set_inline_error(date_entry, "Enter a valid YYYY-MM-DD date.")
                return
            description = description_entry.get().strip()
            if not description:
                set_inline_error(description_entry, "Enter a description.")
                return
            try:
                amount = float(amount_entry.get())
            except ValueError:
                set_inline_error(amount_entry, "Enter a valid amount.")
                return
            if not math.isfinite(amount) or amount <= 0:
                set_inline_error(amount_entry, "Amount must be greater than zero.")
                return
            try:
                update_expense(
                    expense["id"], value, category_entry.get(),
                    description, amount,
                )
            except (ValueError, sqlite3.Error) as error:
                toast(dialog, f"Expense could not be updated: {error}", "error")
                return
            dialog.destroy()
            self.refresh()
            toast(self, "Expense updated.", "success")

        primary_button(
            actions, "Save changes", command=save_changes,
            width=130, height=36,
        ).pack(side="right")

    def _delete_expense(self, expense):
        if not confirm_dialog(
            self,
            "Delete expense",
            f"Delete {expense['description']} ({format_currency(expense['amount'])})?",
            confirm_text="Delete",
        ):
            return
        try:
            delete_expense(expense["id"])
        except (ValueError, sqlite3.Error) as error:
            toast(self, f"Expense could not be deleted: {error}", "error")
            return
        self.refresh()
        toast(self, "Expense deleted.", "success")

    def _export_accounting_book(self):
        year, month = self._selected_year_month()
        try:
            path = generate_accounting_book(year, month)
        except (OSError, ValueError, sqlite3.Error) as error:
            toast(self, f"Accounting book could not be created: {error}", "error")
            return
        toast(self, f"Accounting book saved to {path}.", "success")
