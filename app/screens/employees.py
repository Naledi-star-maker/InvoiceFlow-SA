import calendar
import math
import os
import shutil
import sqlite3
import sys
from datetime import date
from tkinter import filedialog

import customtkinter as ctk

from app.database.database import (
    UIF_MONTHLY_GROSS_CEILING,
    add_employee,
    add_salary_advance,
    delete_employee,
    get_all_employees,
    get_month_pay_record,
    get_month_pay_records,
    get_outstanding_advance,
    get_salary_advances,
    save_month_pay_record,
    update_employee,
    update_employee_document,
)
from app.services.payslip_generator import generate_payslip
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
    labeled_entry,
    page_header,
    primary_button,
    secondary_button,
    set_inline_error,
    toast,
)
from app.utils import format_currency


ALLOWED_DOCUMENT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class EmployeesFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        today = date.today()
        self.selected_employee = None
        self.hour_entries = {}

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.scroll.pack(fill="both", expand=True, padx=24, pady=24)
        self.scroll.grid_columnconfigure(0, weight=1)
        page_header(
            self.scroll,
            "Employees",
            "Manage employee details, hours, salary advances, and payslips.",
        ).pack(fill="x", pady=(0, 16))

        people_card = card(self.scroll)
        people_card.pack(fill="x", pady=(0, 16))
        heading = ctk.CTkFrame(people_card, fg_color="transparent")
        heading.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(
            heading, text="Employee list", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(side="left")
        primary_button(
            heading, "Add employee", command=self._open_employee_dialog,
            width=140, height=36,
        ).pack(side="right")
        self.employee_list = ctk.CTkScrollableFrame(
            people_card, fg_color=SURFACE, height=150,
        )
        self.employee_list.pack(fill="x", padx=8, pady=(0, 8))
        self.employee_detail = ctk.CTkFrame(people_card, fg_color="transparent")
        self.employee_detail.pack(fill="x", padx=16, pady=(0, 12))

        period_card = card(self.scroll)
        period_card.pack(fill="x", pady=(0, 16))
        period_row = ctk.CTkFrame(period_card, fg_color="transparent")
        period_row.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(
            period_row, text="Pay period", text_color=SECONDARY,
            font=font(FONT_SIZE["label"], "bold"),
        ).pack(side="left", padx=(0, 10))
        self.month_selector = ctk.CTkOptionMenu(
            period_row,
            values=[calendar.month_name[month] for month in range(1, 13)],
            command=lambda _value: self._load_month(),
        )
        self.month_selector.set(calendar.month_name[today.month])
        self.month_selector.pack(side="left", padx=(0, 10))
        self.year_selector = ctk.CTkOptionMenu(
            period_row,
            values=[str(year) for year in range(2000, today.year + 2)],
            command=lambda _value: self._load_month(),
        )
        self.year_selector.set(str(today.year))
        self.year_selector.pack(side="left", padx=(0, 16))
        secondary_button(
            period_row, "Generate payslips for this month",
            command=self._generate_all_payslips, height=36,
        ).pack(side="right")

        self.pay_section = card(self.scroll)
        self.pay_section.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            self.pay_section, text="Monthly salary", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.pay_content = ctk.CTkFrame(self.pay_section, fg_color="transparent")
        self.pay_content.pack(fill="x", padx=16, pady=(0, 16))

        advance_section = card(self.scroll)
        advance_section.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            advance_section, text="Salary advances", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.advance_balance_label = ctk.CTkLabel(
            advance_section, text="Select an employee to view advances.",
            text_color=SECONDARY, anchor="w", font=font(FONT_SIZE["body"]),
        )
        self.advance_balance_label.pack(fill="x", padx=16, pady=(0, 8))
        advance_form = ctk.CTkFrame(advance_section, fg_color="transparent")
        advance_form.pack(fill="x", padx=16, pady=(0, 8))
        advance_form.grid_columnconfigure((0, 1, 2), weight=1)
        self.advance_date = labeled_entry(
            advance_form, "Date", placeholder="YYYY-MM-DD"
        )
        self.advance_date.field_container.grid(
            row=0, column=0, sticky="ew", padx=(0, 10)
        )
        self.advance_date.insert(0, today.isoformat())
        self.advance_amount = labeled_entry(advance_form, "Amount (R)")
        self.advance_amount.field_container.grid(
            row=0, column=1, sticky="ew", padx=(0, 10)
        )
        self.advance_description = labeled_entry(
            advance_form, "Short description"
        )
        self.advance_description.field_container.grid(
            row=0, column=2, sticky="ew"
        )
        self.advance_error = ctk.CTkLabel(
            advance_section, text="", text_color=DANGER, anchor="w",
            font=font(FONT_SIZE["small"]),
        )
        self.advance_error.pack(fill="x", padx=16, pady=(0, 8))
        primary_button(
            advance_section, "Add advance", command=self._add_advance,
            width=130, height=36,
        ).pack(anchor="e", padx=16, pady=(0, 8))
        self.advance_history = ctk.CTkFrame(
            advance_section, fg_color="transparent"
        )
        self.advance_history.pack(fill="x", padx=16, pady=(0, 12))

        self.refresh()

    def _selected_month(self):
        month_number = list(calendar.month_name).index(self.month_selector.get())
        year = int(self.year_selector.get())
        return year, month_number, f"{year:04d}-{month_number:02d}"

    def refresh(self):
        employees = get_all_employees()
        for child in self.employee_list.winfo_children():
            child.destroy()
        if not employees:
            empty_state(self.employee_list, "No employees added yet.")
            self.selected_employee = None
        else:
            for employee in employees:
                row = ctk.CTkFrame(
                    self.employee_list, fg_color=SURFACE, corner_radius=8,
                )
                row.pack(fill="x", padx=4, pady=3)
                ctk.CTkLabel(
                    row,
                    text=(
                        f"{employee['employee_id']}  ·  "
                        f"{employee['name']} {employee['surname']}  ·  "
                        f"{employee['cell_number']}  ·  "
                        f"Advance balance: "
                        f"{format_currency(get_outstanding_advance(employee['id']))}"
                    ),
                    text_color=TEXT, anchor="w", font=font(FONT_SIZE["body"]),
                ).pack(side="left", fill="x", expand=True, padx=10, pady=9)
                secondary_button(
                    row, "Select", command=lambda item=employee: self._select_employee(item),
                    width=74, height=30,
                ).pack(side="right", padx=6, pady=4)
                secondary_button(
                    row, "Edit", command=lambda item=employee: self._open_employee_dialog(item),
                    width=60, height=30,
                ).pack(side="right", padx=6, pady=4)
                secondary_button(
                    row, "Delete", command=lambda item=employee: self._delete_employee(item),
                    width=70, height=30,
                ).pack(side="right", padx=6, pady=4)

            if self.selected_employee:
                refreshed = next(
                    (item for item in employees if item["id"] == self.selected_employee["id"]),
                    None,
                )
                self.selected_employee = refreshed
            if self.selected_employee is None:
                self.selected_employee = employees[0]

        self._render_employee_detail()
        self._load_month()
        self._render_advances()
        self.scroll.update_idletasks()
        self.scroll._parent_canvas.configure(
            scrollregion=self.scroll._parent_canvas.bbox("all")
        )

    def _select_employee(self, employee):
        self.selected_employee = employee
        self._render_employee_detail()
        self._load_month()
        self._render_advances()

    def _render_employee_detail(self):
        for child in self.employee_detail.winfo_children():
            child.destroy()
        employee = self.selected_employee
        if employee is None:
            return
        ctk.CTkLabel(
            self.employee_detail,
            text=(
                f"{employee['employee_id']}  ·  {employee['name']} "
                f"{employee['surname']}  ·  SA ID {employee['sa_id_number']}  "
                f"·  Started {employee['start_date']}"
            ),
            text_color=SECONDARY, anchor="w", font=font(FONT_SIZE["small"]),
        ).pack(side="left", fill="x", expand=True)
        for kind, title, path_key in (
            ("id_copy", "ID copy", "id_copy_path"),
            ("contract", "Contract", "contract_path"),
        ):
            if employee.get(path_key):
                secondary_button(
                    self.employee_detail, f"Open {title}",
                    command=lambda item=employee, key=path_key: self._open_document(item[key]),
                    width=110, height=32,
                ).pack(side="right", padx=(6, 0))
            secondary_button(
                self.employee_detail, f"Upload {title}",
                command=lambda item=employee, document_type=kind: self._upload_document(
                    item, document_type
                ),
                width=120, height=32,
            ).pack(side="right", padx=(6, 0))

    def _open_employee_dialog(self, employee=None):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit employee" if employee else "Add employee")
        dialog.geometry("440x460")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20, pady=20)
        fields = {}
        for key, label, placeholder in (
            ("name", "Name", ""),
            ("surname", "Surname", ""),
            ("cell_number", "Cell number", ""),
            ("sa_id_number", "SA ID number (13 digits)", ""),
            ("start_date", "Start date", "YYYY-MM-DD"),
        ):
            entry = labeled_entry(form, label, placeholder=placeholder)
            entry.field_container.pack(fill="x", pady=(0, 10))
            if employee:
                entry.insert(0, employee[key])
            fields[key] = entry
        error = ctk.CTkLabel(
            form, text="", text_color=DANGER, anchor="w",
            font=font(FONT_SIZE["small"]),
        )
        error.pack(fill="x")
        actions = ctk.CTkFrame(form, fg_color="transparent")
        actions.pack(fill="x", pady=(12, 0))
        secondary_button(
            actions, "Cancel", command=dialog.destroy, width=90,
        ).pack(side="right", padx=(8, 0))

        def save():
            values = {key: entry.get().strip() for key, entry in fields.items()}
            if not values["sa_id_number"].isdigit() or len(values["sa_id_number"]) != 13:
                set_inline_error(fields["sa_id_number"], "Enter exactly 13 digits.")
                return
            set_inline_error(fields["sa_id_number"], "")
            try:
                if employee:
                    update_employee(
                        employee["id"], values["name"], values["surname"],
                        values["cell_number"], values["sa_id_number"],
                        values["start_date"],
                    )
                else:
                    add_employee(
                        values["name"], values["surname"], values["cell_number"],
                        values["sa_id_number"], values["start_date"],
                    )
            except (ValueError, sqlite3.Error) as exception:
                error.configure(text=str(exception))
                return
            dialog.destroy()
            self.refresh()
            toast(self, "Employee saved.", "success")

        primary_button(
            actions, "Save employee", command=save, width=130, height=36,
        ).pack(side="right")

    def _delete_employee(self, employee):
        if not confirm_dialog(
            self,
            "Delete employee",
            f"Delete {employee['name']} {employee['surname']}?",
            confirm_text="Delete",
        ):
            return
        try:
            delete_employee(employee["id"])
        except (ValueError, sqlite3.Error) as error:
            toast(self, str(error), "error")
            return
        self.selected_employee = None
        self.refresh()
        toast(self, "Employee deleted.", "success")

    def _upload_document(self, employee, document_type):
        source = filedialog.askopenfilename(
            parent=self,
            title="Choose employee document",
            filetypes=[
                ("PDF, JPG, PNG files", "*.pdf *.jpg *.jpeg *.png"),
                ("All files", "*.*"),
            ],
        )
        if not source:
            return
        if os.path.splitext(source)[1].lower() not in ALLOWED_DOCUMENT_EXTENSIONS:
            toast(self, "Choose a PDF, JPG, or PNG file.", "error")
            return
        folder = os.path.join("employee_docs", employee["employee_id"])
        os.makedirs(folder, exist_ok=True)
        destination = os.path.join(folder, f"{document_type}{os.path.splitext(source)[1].lower()}")
        try:
            shutil.copy2(source, destination)
            update_employee_document(employee["id"], document_type, destination)
        except (OSError, sqlite3.Error, ValueError) as error:
            toast(self, f"Document could not be saved: {error}", "error")
            return
        self.refresh()
        toast(self, f"{document_type.replace('_', ' ').title()} uploaded.", "success")

    def _open_document(self, path):
        if not os.path.isfile(path):
            toast(self, "The employee document could not be found.", "error")
            return
        try:
            if sys.platform == "win32":
                os.startfile(os.path.abspath(path))
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", path])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", path])
        except OSError as error:
            toast(self, f"Document could not be opened: {error}", "error")

    def _load_month(self):
        if not hasattr(self, "pay_content"):
            return
        for child in self.pay_content.winfo_children():
            child.destroy()
        self.hour_entries = {}
        employee = self.selected_employee
        if employee is None:
            empty_state(self.pay_content, "Add an employee before entering monthly pay.")
            return
        year, month, month_key = self._selected_month()
        pay_record = get_month_pay_record(employee["id"], month_key)
        days = calendar.monthrange(year, month)[1]
        existing_hours = pay_record["hours"] if pay_record else {}

        rate_row = ctk.CTkFrame(self.pay_content, fg_color="transparent")
        rate_row.pack(fill="x", pady=(0, 10))
        self.hourly_rate_entry = labeled_entry(rate_row, "Hourly rate (R)")
        self.hourly_rate_entry.field_container.pack(
            side="left", fill="x", expand=True, padx=(0, 12)
        )
        self.hourly_rate_entry.insert(
            0, str(pay_record["hourly_rate"] if pay_record else employee["hourly_rate"])
        )
        self.gross_override_entry = labeled_entry(
            rate_row, "Gross override (optional)"
        )
        self.gross_override_entry.field_container.pack(
            side="left", fill="x", expand=True
        )
        if pay_record and pay_record["gross_override"] is not None:
            self.gross_override_entry.insert(0, str(pay_record["gross_override"]))

        ctk.CTkLabel(
            self.pay_content, text="Hours worked (Monday-Friday)",
            text_color=SECONDARY, anchor="w", font=font(FONT_SIZE["label"], "bold"),
        ).pack(fill="x", pady=(4, 8))
        grid = ctk.CTkFrame(self.pay_content, fg_color="transparent")
        grid.pack(fill="x")
        for column in range(5):
            grid.grid_columnconfigure(column, weight=1)
        weekdays = [
            day for day in range(1, days + 1)
            if date(year, month, day).weekday() < 5
        ]
        for index, day in enumerate(weekdays):
            row_index, column = divmod(index, 5)
            day_frame = ctk.CTkFrame(
                grid, fg_color=SURFACE, border_color=BORDER, border_width=1,
                corner_radius=8,
            )
            day_frame.grid(
                row=row_index, column=column, sticky="ew",
                padx=4, pady=4,
            )
            ctk.CTkLabel(
                day_frame,
                text=f"{calendar.day_abbr[date(year, month, day).weekday()]} {day:02d}",
                text_color=SECONDARY, font=font(FONT_SIZE["small"]),
            ).pack(padx=6, pady=(6, 2))
            entry = ctk.CTkEntry(
                day_frame, width=66, height=32, justify="center",
                border_color=BORDER, fg_color=SURFACE, text_color=TEXT,
            )
            entry.pack(padx=6, pady=(0, 6))
            entry.insert(0, str(existing_hours.get(date(year, month, day).isoformat(), "")))
            entry.bind("<KeyRelease>", lambda _event: self._update_pay_preview())
            self.hour_entries[date(year, month, day).isoformat()] = entry

        deductions = ctk.CTkFrame(self.pay_content, fg_color="transparent")
        deductions.pack(fill="x", pady=(12, 0))
        deductions.grid_columnconfigure((0, 1, 2), weight=1)
        self.paye_entry = labeled_entry(deductions, "PAYE (R)")
        self.paye_entry.field_container.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.paye_entry.insert(0, str(pay_record["paye"] if pay_record else 0))
        outstanding = get_outstanding_advance(employee["id"], month_key)
        self.advance_deduction_entry = labeled_entry(
            deductions, f"Deduct advance (R) — outstanding {format_currency(outstanding)}"
        )
        self.advance_deduction_entry.field_container.grid(
            row=0, column=1, sticky="ew", padx=(0, 10)
        )
        self.advance_deduction_entry.insert(
            0,
            str(
                pay_record["advance_deducted"]
                if pay_record else round(outstanding, 2)
            ),
        )
        self.pay_date_entry = labeled_entry(
            deductions, "Pay date", placeholder="YYYY-MM-DD"
        )
        self.pay_date_entry.field_container.grid(row=0, column=2, sticky="ew")
        self.pay_date_entry.insert(
            0, pay_record["pay_date"] if pay_record else date.today().isoformat()
        )
        for entry in (
            self.hourly_rate_entry, self.gross_override_entry, self.paye_entry,
            self.advance_deduction_entry,
        ):
            entry.bind("<KeyRelease>", lambda _event: self._update_pay_preview())

        self.pay_preview = ctk.CTkLabel(
            self.pay_content, text="", fg_color="#FDF2F8",
            text_color=TEXT, corner_radius=8,
            font=font(FONT_SIZE["body"], "bold"), anchor="w",
        )
        self.pay_preview.pack(fill="x", pady=(12, 8), padx=2, ipady=10)
        self._update_pay_preview()
        actions = ctk.CTkFrame(self.pay_content, fg_color="transparent")
        actions.pack(fill="x", pady=(4, 0))
        secondary_button(
            actions, "Generate this employee's payslip",
            command=self._generate_selected_payslip, height=36,
        ).pack(side="right", padx=(8, 0))
        primary_button(
            actions, "Save monthly pay", command=self._save_pay_record,
            height=36,
        ).pack(side="right")

    def _number_from_entry(self, entry):
        value = entry.get().strip()
        return float(value) if value else 0.0

    def _pay_calculation(self):
        hours = {}
        for day, entry in self.hour_entries.items():
            value = entry.get().strip()
            hours[day] = float(value) if value else 0.0
        hourly_rate = self._number_from_entry(self.hourly_rate_entry)
        gross_override_text = self.gross_override_entry.get().strip()
        gross_override = float(gross_override_text) if gross_override_text else None
        gross = gross_override if gross_override is not None else sum(hours.values()) * hourly_rate
        employee_uif = round(min(gross, UIF_MONTHLY_GROSS_CEILING) * 0.01, 2)
        employer_uif = employee_uif
        paye = self._number_from_entry(self.paye_entry)
        advance = self._number_from_entry(self.advance_deduction_entry)
        net = gross - employee_uif - paye
        return {
            "hours": hours, "hourly_rate": hourly_rate,
            "gross_override": gross_override, "gross": gross,
            "employee_uif": employee_uif, "employer_uif": employer_uif,
            "paye": paye, "advance": advance, "net": net,
            "cash": net - advance,
        }

    def _update_pay_preview(self):
        if not hasattr(self, "pay_preview"):
            return
        try:
            calculation = self._pay_calculation()
        except ValueError:
            self.pay_preview.configure(text="Enter valid numbers to calculate pay.")
            return
        self.pay_preview.configure(
            text=(
                f"Gross: {format_currency(calculation['gross'])}  |  "
                f"Employee UIF: {format_currency(calculation['employee_uif'])}  |  "
                f"Employer UIF: {format_currency(calculation['employer_uif'])}  |  "
                f"PAYE: {format_currency(calculation['paye'])}\n"
                f"Payslip net: {format_currency(calculation['net'])}  |  "
                f"Advance deducted: {format_currency(calculation['advance'])}  |  "
                f"Pay out now: {format_currency(calculation['cash'])}"
            )
        )

    def _save_pay_record(self):
        employee = self.selected_employee
        if employee is None:
            return
        try:
            calculation = self._pay_calculation()
        except ValueError:
            toast(self, "Enter valid numeric values for hours and pay.", "error")
            return
        if any(value < 0 or not math.isfinite(value) for value in calculation["hours"].values()):
            toast(self, "Hours must be valid non-negative numbers.", "error")
            return
        if any(
            not math.isfinite(calculation[key]) or calculation[key] < 0
            for key in ("hourly_rate", "gross", "paye", "advance")
        ):
            toast(self, "Pay values must be valid non-negative amounts.", "error")
            return
        _, _, month_key = self._selected_month()
        pay_date = self.pay_date_entry.get().strip()
        try:
            save_month_pay_record(
                employee["id"], month_key, calculation["hours"],
                calculation["hourly_rate"], calculation["gross_override"],
                calculation["paye"], calculation["advance"], pay_date,
            )
        except (ValueError, sqlite3.Error) as error:
            toast(self, f"Pay could not be saved: {error}", "error")
            return
        self._load_month()
        self._render_advances()
        toast(self, "Monthly pay saved.", "success")

    def _render_advances(self):
        for child in self.advance_history.winfo_children():
            child.destroy()
        employee = self.selected_employee
        if employee is None:
            self.advance_balance_label.configure(
                text="Select an employee to view advances."
            )
            return
        balance = get_outstanding_advance(employee["id"])
        self.advance_balance_label.configure(
            text=f"Outstanding advance balance: {format_currency(balance)}"
        )
        advances = get_salary_advances(employee["id"])
        if not advances:
            ctk.CTkLabel(
                self.advance_history, text="No advances recorded.",
                text_color=SECONDARY, font=font(FONT_SIZE["small"]),
            ).pack(anchor="w", pady=4)
            return
        for advance in advances:
            ctk.CTkLabel(
                self.advance_history,
                text=(
                    f"{advance['advance_date']}  ·  "
                    f"{format_currency(advance['amount'])}  ·  "
                    f"{advance['description']}"
                ),
                text_color=SECONDARY, anchor="w",
                font=font(FONT_SIZE["small"]),
            ).pack(fill="x", pady=3)

    def _add_advance(self):
        employee = self.selected_employee
        if employee is None:
            toast(self, "Select an employee first.", "error")
            return
        amount_text = self.advance_amount.get().strip()
        try:
            amount = float(amount_text)
        except ValueError:
            set_inline_error(self.advance_amount, "Enter a valid amount.")
            return
        set_inline_error(self.advance_amount, "")
        try:
            add_salary_advance(
                employee["id"], self.advance_date.get().strip(), amount,
                self.advance_description.get().strip(),
            )
        except (ValueError, sqlite3.Error) as error:
            self.advance_error.configure(text=str(error))
            return
        self.advance_error.configure(text="")
        self.advance_amount.delete(0, "end")
        self.advance_description.delete(0, "end")
        self._load_month()
        self._render_advances()
        toast(self, "Salary advance recorded.", "success")

    def _generate_selected_payslip(self):
        employee = self.selected_employee
        if employee is None:
            return
        _, _, month = self._selected_month()
        record = get_month_pay_record(employee["id"], month)
        if record is None:
            toast(self, "Save this employee's monthly pay first.", "error")
            return
        try:
            path = generate_payslip(employee["id"], month)
        except (OSError, ValueError, sqlite3.Error) as error:
            toast(self, f"Payslip could not be created: {error}", "error")
            return
        toast(self, f"Payslip saved to {path}.", "success")

    def _generate_all_payslips(self):
        _, _, month = self._selected_month()
        records = get_month_pay_records(month)
        if not records:
            toast(self, "Save monthly pay for employees first.", "error")
            return
        paths = []
        try:
            for record in records:
                paths.append(generate_payslip(record["employee_row_id"], month))
        except (OSError, ValueError, sqlite3.Error) as error:
            toast(self, f"Payslips could not be created: {error}", "error")
            return
        toast(self, f"Generated {len(paths)} payslip(s) in payslips/{month}.", "success")
