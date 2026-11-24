import math
import os
import shutil
import sqlite3
from datetime import date, datetime

import customtkinter as ctk

from app.database.database import (
    DATABASE_PATH,
    delete_all_invoices,
    delete_invoice,
    get_all_customers,
    get_all_invoices,
    get_customer_by_id,
    get_invoice_count_and_total,
    get_invoice_by_id,
    search_invoices,
    update_invoice,
    update_invoice_pdf_path,
)
from app.services.invoice_service import calculate_totals, duplicate_invoice
from app.services.pdf_generator import generate_invoice_pdf, invoice_pdf_path
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
    danger_button,
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
from app.utils import format_currency


class ManageInvoiceFrame(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG)
        self.controller = controller
        self.item_rows = []
        self.selected_invoice_id = None
        self.selected_customer_id = None
        self.customers = []
        self._loaded_invoice = None

        page_header(
            self,
            "Manage invoices",
            "Edit existing invoices or create a new month-end resend from a past invoice.",
        ).pack(fill="x", padx=24, pady=(24, 16))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=1, minsize=280)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        self.left_panel = card(body)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ctk.CTkLabel(
            self.left_panel, text="Invoice history", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 8))
        self.search_entry = ctk.CTkEntry(
            self.left_panel,
            placeholder_text="Search number, customer, or date",
            height=38,
            border_color=BORDER,
            text_color=TEXT,
            placeholder_text_color=SECONDARY,
            corner_radius=8,
            font=font(FONT_SIZE["body"]),
        )
        self.search_entry.pack(fill="x", padx=12, pady=(0, 12))
        self.search_entry.bind(
            "<KeyRelease>", lambda _event: self.load_invoice_list(self.search_entry.get())
        )
        self.list_scroll = ctk.CTkScrollableFrame(
            self.left_panel, fg_color=SURFACE,
        )
        self.list_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        list_tools = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        list_tools.pack(fill="x", padx=12, pady=(0, 12))
        secondary_button(
            list_tools, "Organise existing PDFs",
            command=self.organise_existing_pdfs, height=34,
        ).pack(fill="x")

        self.right_panel = ctk.CTkScrollableFrame(body, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew")
        self.detail_card = card(self.right_panel)
        self.detail_card.pack(fill="x")
        self.selected_label = ctk.CTkLabel(
            self.detail_card, text="Select an invoice to edit",
            text_color=TEXT, font=font(FONT_SIZE["heading"], "bold"),
            anchor="w", wraplength=600,
        )
        self.selected_label.pack(fill="x", padx=16, pady=(16, 12))
        self.customer_dropdown = labeled_dropdown(
            self.detail_card, "Customer", ["No customers"]
        )
        self.customer_dropdown.field_container.pack(
            fill="x", padx=16, pady=(0, 8)
        )

        self.items_scroll = ctk.CTkScrollableFrame(
            self.detail_card, fg_color=SURFACE, height=260,
        )
        self.items_scroll.pack(fill="both", expand=True, padx=12, pady=4)
        self.status_label = ctk.CTkLabel(
            self.detail_card, text="", text_color=DANGER,
            font=font(FONT_SIZE["small"]), anchor="w", justify="left",
        )
        self.status_label.pack(fill="x", padx=16, pady=(4, 0))

        detail_footer = ctk.CTkFrame(self.detail_card, fg_color="transparent")
        detail_footer.pack(fill="x", padx=16, pady=12)
        secondary_button(
            detail_footer, "+ Add item", command=self.add_item_row,
            height=36,
        ).pack(side="left")
        self.totals_label = ctk.CTkLabel(
            detail_footer, text="Total: R 0.00", text_color=TEXT,
            font=font(FONT_SIZE["heading"], "bold"),
        )
        self.totals_label.pack(side="right", padx=(12, 0))

        notes_card = card(self.right_panel)
        notes_card.pack(fill="x", pady=(12, 0))
        self.notes_entry = labeled_entry(
            notes_card, "Notes", placeholder="Optional note for this invoice"
        )
        self.notes_entry.field_container.pack(fill="x", padx=16, pady=12)
        due_date_card = card(self.right_panel)
        due_date_card.pack(fill="x", pady=(12, 0))
        self.due_date_entry = labeled_entry(
            due_date_card, "Due date", placeholder="YYYY-MM-DD"
        )
        self.due_date_entry.field_container.pack(
            fill="x", padx=16, pady=12
        )
        actions = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        actions.pack(fill="x", pady=(12, 0))
        self.save_changes_button = primary_button(
            actions, "Save changes",
            command=self.handle_save_changes,
            height=42, state="disabled",
        )
        self.save_changes_button.pack(fill="x", pady=(0, 8))
        self.regenerate_button = secondary_button(
            actions, "Create as new invoice",
            command=self.handle_regenerate,
            height=42, state="disabled",
        )
        self.regenerate_button.pack(fill="x")

        danger_card = card(body)
        danger_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        body.grid_rowconfigure(1, weight=0)
        ctk.CTkLabel(
            danger_card, text="Danger zone", text_color=DANGER,
            font=font(FONT_SIZE["heading"], "bold"),
        ).pack(side="left", padx=16, pady=12)
        danger_button(
            danger_card, "Delete all invoices", command=self._open_delete_all_dialog,
            width=180, height=38,
        ).pack(side="right", padx=16, pady=8)
        self.refresh()

    def refresh(self):
        self.customers = get_all_customers()
        customer_names = [customer["customer_name"] for customer in self.customers]
        self.customer_dropdown.configure(values=customer_names or ["No customers"])
        if self.selected_customer_id is not None:
            selected = next(
                (customer for customer in self.customers if customer["id"] == self.selected_customer_id),
                None,
            )
            if selected:
                self.customer_dropdown.set(selected["customer_name"])
        self.load_invoice_list()

    def load_invoice_list(self, keyword=""):
        for widget in self.list_scroll.winfo_children():
            widget.destroy()
        invoices = search_invoices(keyword) if keyword.strip() else get_all_invoices()
        if not invoices:
            empty_state(self.list_scroll, "No invoices found.")
            return

        for invoice in invoices:
            row = ctk.CTkFrame(
                self.list_scroll, fg_color=SURFACE, corner_radius=8,
                border_color=BORDER, border_width=1,
            )
            row.pack(fill="x", pady=4, padx=2)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(fill="x", padx=12, pady=(10, 4))
            ctk.CTkLabel(
                info, text=invoice["invoice_number"], text_color=TEXT,
                font=font(FONT_SIZE["body"], "bold"), anchor="w",
            ).pack(fill="x")
            ctk.CTkLabel(
                info,
                text=f"{invoice['customer_name']}  ·  {invoice['invoice_date']}",
                text_color=SECONDARY, font=font(FONT_SIZE["small"]), anchor="w",
            ).pack(fill="x", pady=(3, 0))
            row_footer = ctk.CTkFrame(row, fg_color="transparent")
            row_footer.pack(fill="x", padx=12, pady=(0, 8))
            ctk.CTkLabel(
                row_footer, text=format_currency(invoice["total"]),
                text_color=TEXT, font=font(FONT_SIZE["body"], "bold"),
            ).pack(side="left")
            secondary_button(
                row_footer, "Edit",
                command=lambda selected_id=invoice["id"]: self.load_invoice_into_editor(selected_id),
                height=30, width=64,
            ).pack(side="right", padx=(6, 0))
            danger_button(
                row_footer, "Delete",
                command=lambda selected=dict(invoice): self._delete_single_invoice(selected),
                height=30, width=70,
            ).pack(side="right", padx=(6, 0))

    def load_invoice_into_editor(self, invoice_id):
        invoice = get_invoice_by_id(invoice_id)
        if invoice is None:
            self.status_label.configure(text="That invoice could not be loaded.")
            return
        customer = get_customer_by_id(invoice["customer_id"])
        if customer is None:
            self.status_label.configure(text="The customer for this invoice no longer exists.")
            return

        self.status_label.configure(text="")
        self.selected_invoice_id = invoice_id
        self._loaded_invoice = invoice
        self.selected_customer_id = customer["id"]
        self.selected_label.configure(
            text=f"Editing {invoice['invoice_number']}  ·  {customer['customer_name']}  ·  {invoice['invoice_date']}"
        )
        self.customer_dropdown.set(customer["customer_name"])
        for row in self.item_rows:
            row["frame"].destroy()
        self.item_rows = []
        for item in invoice["items"]:
            amount = item.get("line_total")
            if amount is None:
                amount = item["quantity"] * item["unit_price"]
            self.add_item_row(item["description"], amount)
        self.notes_entry.delete(0, "end")
        if invoice.get("notes"):
            self.notes_entry.insert(0, invoice["notes"])
        self.due_date_entry.delete(0, "end")
        if invoice.get("due_date"):
            self.due_date_entry.insert(0, invoice["due_date"])
        set_inline_error(self.due_date_entry, "")
        self.regenerate_button.configure(state="normal")
        self.save_changes_button.configure(state="normal")
        self.update_totals()

    def add_item_row(self, description="", amount=0):
        row_frame = ctk.CTkFrame(self.items_scroll, fg_color=SURFACE)
        row_frame.pack(fill="x", pady=4, padx=4)
        row_frame.grid_columnconfigure(0, weight=5)
        row_frame.grid_columnconfigure(1, weight=2)

        description_entry = labeled_entry(row_frame, "Description")
        description_entry.field_container.grid(
            row=0, column=0, sticky="ew", padx=8, pady=8
        )
        description_entry.insert(0, description)
        amount_entry = labeled_entry(row_frame, "Amount (R)")
        amount_entry.field_container.grid(
            row=0, column=1, sticky="ew", padx=(0, 8), pady=8
        )
        amount_entry.insert(0, str(amount))
        remove_button = ctk.CTkButton(
            row_frame, text="×", width=34, height=34,
            fg_color="transparent", hover_color="#F4F4F5",
            text_color=SECONDARY, corner_radius=8,
            command=lambda: self.remove_item_row(row_data),
        )
        remove_button.grid(row=0, column=2, padx=8, pady=(24, 8))
        row_data = {
            "frame": row_frame, "description": description_entry,
            "amount": amount_entry,
        }
        amount_entry.bind("<KeyRelease>", lambda _event: self.update_totals())
        self.item_rows.append(row_data)
        self.update_totals()

    def remove_item_row(self, row_data):
        if len(self.item_rows) == 1:
            self.status_label.configure(text="An invoice needs at least one item row.")
            return
        row_data["frame"].destroy()
        self.item_rows.remove(row_data)
        self.status_label.configure(text="")
        self.update_totals()

    def _collect_items(self):
        items = []
        for row in self.item_rows:
            description = row["description"].get().strip()
            if not description:
                continue
            try:
                amount = float(row["amount"].get())
            except ValueError:
                amount = 0
            items.append({
                "description": description,
                "quantity": 1,
                "unit_price": amount,
                "line_total": amount,
            })
        return items

    def update_totals(self):
        totals = calculate_totals(self._collect_items())
        self.totals_label.configure(text=f"Total: {format_currency(totals['total'])}")

    def _selected_customer_id(self):
        selected_name = self.customer_dropdown.get()
        customer = next(
            (entry for entry in self.customers if entry["customer_name"] == selected_name),
            None,
        )
        return customer["id"] if customer else None

    def _validated_editor_data(self):
        if self.selected_invoice_id is None:
            self.status_label.configure(text="Load an invoice from the list first.")
            return None
        customer_id = self._selected_customer_id()
        if customer_id is None:
            self.status_label.configure(text="Select a customer.")
            return None
        due_date = self.due_date_entry.get().strip()
        if due_date:
            try:
                parsed_due_date = date.fromisoformat(due_date)
            except ValueError:
                parsed_due_date = None
            if parsed_due_date is None or parsed_due_date.isoformat() != due_date:
                set_inline_error(
                    self.due_date_entry, "Enter a valid date in YYYY-MM-DD format."
                )
                return None
        set_inline_error(self.due_date_entry, "")

        items = []
        for row in self.item_rows:
            description = row["description"].get().strip()
            amount_text = row["amount"].get().strip()
            if not description and not amount_text:
                continue
            if not description:
                self.status_label.configure(text="Enter a description for each line item.")
                return None
            if not self._is_nonnegative_number(amount_text):
                self.status_label.configure(text="Enter a valid non-negative amount for each item.")
                return None
            amount = float(amount_text)
            items.append({
                "description": description,
                "quantity": 1,
                "unit_price": amount,
                "line_total": amount,
            })
        if not items:
            self.status_label.configure(text="Add at least one item with a description and amount.")
            return None

        totals = calculate_totals(items)
        self.status_label.configure(text="")
        return {
            "customer_id": customer_id,
            "due_date": due_date,
            "notes": self.notes_entry.get().strip(),
            "items": items,
            "totals": totals,
        }

    def handle_save_changes(self):
        data = self._validated_editor_data()
        if data is None:
            return
        invoice_id = self.selected_invoice_id
        old_pdf_path = (self._loaded_invoice or {}).get("pdf_path")
        try:
            update_invoice(invoice_id, {
                "customer_id": data["customer_id"],
                "subtotal": data["totals"]["subtotal"],
                "vat": 0,
                "total": data["totals"]["total"],
                "notes": data["notes"],
                "due_date": data["due_date"],
            }, data["items"])
        except (ValueError, sqlite3.Error) as error:
            self.status_label.configure(text=f"Invoice changes could not be saved: {error}")
            return

        try:
            pdf_path = generate_invoice_pdf(invoice_id)
        except (OSError, ValueError) as error:
            toast(self, f"Invoice saved, but its PDF could not be regenerated: {error}", "error")
        else:
            old_path_remains = (
                old_pdf_path
                and os.path.normcase(os.path.abspath(old_pdf_path))
                != os.path.normcase(os.path.abspath(pdf_path))
                and os.path.exists(old_pdf_path)
            )
            if old_path_remains:
                toast(
                    self,
                    f"Invoice saved to {pdf_path}, but the previous PDF could not be removed.",
                    "error",
                )
            else:
                toast(self, f"Invoice changes saved. PDF: {pdf_path}", "success")
        self._clear_editor()
        self._refresh_invoice_surfaces()

    def handle_regenerate(self):
        data = self._validated_editor_data()
        if data is None:
            return

        try:
            new_invoice_id = duplicate_invoice(
                self.selected_invoice_id, data["items"], data["notes"],
                data["due_date"], data["customer_id"],
            )
        except (ValueError, sqlite3.Error) as error:
            self.status_label.configure(text=f"The new invoice could not be saved: {error}")
            return

        new_invoice = get_invoice_by_id(new_invoice_id)
        try:
            pdf_path = generate_invoice_pdf(new_invoice_id)
        except (OSError, ValueError) as error:
            toast(
                self,
                f"Invoice {new_invoice['invoice_number']} saved, but PDF failed: {error}",
                "error",
            )
        else:
            toast(
                self,
                f"New invoice {new_invoice['invoice_number']} created. PDF saved to {pdf_path}.",
                "success",
            )

        self._clear_editor()
        self._refresh_invoice_surfaces()

    def _clear_editor(self):
        self.selected_invoice_id = None
        self.selected_customer_id = None
        self._loaded_invoice = None
        self.selected_label.configure(text="Select an invoice to edit")
        self.status_label.configure(text="")
        for row in self.item_rows:
            row["frame"].destroy()
        self.item_rows = []
        self.notes_entry.delete(0, "end")
        self.due_date_entry.delete(0, "end")
        set_inline_error(self.due_date_entry, "")
        self.update_totals()
        self.regenerate_button.configure(state="disabled")
        self.save_changes_button.configure(state="disabled")
        if self.customers:
            self.customer_dropdown.set(self.customers[0]["customer_name"])

    def _refresh_invoice_surfaces(self):
        self.refresh()
        for key in ("dashboard", "reports", "payments", "budget"):
            frame = self.controller.frames.get(key)
            if frame is not None and hasattr(frame, "refresh"):
                frame.refresh()

    def _delete_single_invoice(self, invoice):
        customer_name = invoice["customer_name"]
        if not confirm_dialog(
            self, "Delete invoice",
            f"Delete {invoice['invoice_number']} for {customer_name} "
            f"({format_currency(invoice['total'])})? This cannot be undone.",
            confirm_text="Delete",
        ):
            return
        try:
            stored_path = delete_invoice(invoice["id"])
        except (ValueError, sqlite3.Error) as error:
            toast(self, f"Invoice could not be deleted: {error}", "error")
            return

        failed_files = self._remove_invoice_pdfs(invoice, stored_path)
        self._clear_editor_if(invoice["id"])
        if failed_files:
            toast(self, f"Invoice deleted, but {failed_files} PDF file(s) could not be removed.", "error")
        else:
            toast(self, f"Invoice {invoice['invoice_number']} deleted.", "success")
        self._refresh_invoice_surfaces()

    def _clear_editor_if(self, invoice_id):
        if self.selected_invoice_id == invoice_id:
            self._clear_editor()

    @staticmethod
    def _path_is_in_invoice_folder(path):
        if not path:
            return False
        invoice_root = os.path.abspath("invoices")
        candidate = os.path.abspath(path)
        try:
            return os.path.commonpath((invoice_root, candidate)) == invoice_root
        except ValueError:
            return False

    def _remove_invoice_pdfs(self, invoice, stored_path=None):
        candidates = set()
        if stored_path and self._path_is_in_invoice_folder(stored_path):
            candidates.add(os.path.abspath(stored_path))
        invoice_number = invoice.get("invoice_number", "")
        invoice_root = os.path.abspath("invoices")
        if os.path.isdir(invoice_root):
            for root, _directories, files in os.walk(invoice_root):
                for file_name in files:
                    if self._matches_invoice_pdf(file_name, invoice_number):
                        candidates.add(os.path.join(root, file_name))
        failures = 0
        for path in candidates:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    failures += 1
        return failures

    @staticmethod
    def _matches_invoice_pdf(file_name, invoice_number):
        if not file_name.lower().endswith(".pdf"):
            return False
        stem = file_name[:-4]
        number = invoice_number.casefold()
        stem = stem.casefold()
        return stem == number or (
            stem.startswith(number) and stem[len(number):len(number) + 1] in (" ", "-", "_")
        )

    def _open_delete_all_dialog(self):
        count, total = get_invoice_count_and_total()
        if count == 0:
            toast(self, "There are no invoices to delete.", "info")
            return
        dialog = ctk.CTkToplevel(self)
        dialog.title("Delete all invoices")
        dialog.geometry("520x370")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        dialog.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            dialog, text="Delete all invoices?", text_color=DANGER,
            font=font(FONT_SIZE["title"], "bold"),
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 10))
        ctk.CTkLabel(
            dialog,
            text=(
                f"This will permanently delete {count} invoice(s), "
                f"totalling {format_currency(total)}, and their PDFs.\n\n"
                "Customers, company details, expenses and budgets will be kept. "
                "This cannot be undone."
            ),
            text_color=SECONDARY, font=font(FONT_SIZE["body"]),
            justify="left", wraplength=460,
        ).grid(row=1, column=0, sticky="w", padx=24)
        reset_numbering = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            dialog, text="Also restart invoice numbering at 00001",
            variable=reset_numbering, font=font(FONT_SIZE["body"]),
        ).grid(row=2, column=0, sticky="w", padx=24, pady=(16, 8))
        confirm_entry = ctk.CTkEntry(dialog, placeholder_text="Type DELETE to enable")
        confirm_entry.grid(row=3, column=0, sticky="ew", padx=24, pady=(4, 12))
        buttons = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons.grid(row=4, column=0, sticky="e", padx=24, pady=(0, 20))
        delete_button = danger_button(
            buttons, "Delete everything", state="disabled", width=150,
        )
        secondary_button(
            buttons, "Cancel", command=dialog.destroy, width=96,
        ).pack(side="left", padx=(0, 8))
        delete_button.pack(side="left")
        confirm_entry.bind(
            "<KeyRelease>",
            lambda _event: delete_button.configure(
                state="normal" if confirm_entry.get() == "DELETE" else "disabled"
            ),
        )
        delete_button.configure(command=lambda: self._delete_all_invoices(
            dialog, reset_numbering.get()
        ))

    def _delete_all_invoices(self, dialog, reset_numbering):
        backup_path = os.path.join(
            "backups", f"invoiceflow-before-delete-{datetime.now():%Y%m%d-%H%M%S}.db"
        )
        try:
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            shutil.copy2(DATABASE_PATH, backup_path)
        except OSError as error:
            toast(self, f"Backup failed; no invoices were deleted: {error}", "error")
            return

        try:
            delete_all_invoices(reset_numbering=reset_numbering)
        except (ValueError, sqlite3.Error) as error:
            toast(self, f"Invoices could not be deleted: {error}", "error")
            return
        dialog.destroy()
        failed = 0
        invoice_root = os.path.abspath("invoices")
        if os.path.isdir(invoice_root):
            for root, _directories, files in os.walk(invoice_root):
                for file_name in files:
                    if file_name.lower().endswith(".pdf"):
                        try:
                            os.remove(os.path.join(root, file_name))
                        except OSError:
                            failed += 1
        self._clear_editor()
        self._refresh_invoice_surfaces()
        if failed:
            toast(self, f"All invoices deleted; {failed} PDF file(s) could not be removed.", "error")
        else:
            toast(self, f"All invoices deleted. Backup saved to {backup_path}.", "success")

    def organise_existing_pdfs(self):
        moved = 0
        missing = 0
        invoices = get_all_invoices()
        invoice_root = os.path.abspath("invoices")
        files_by_prefix = {}
        if os.path.isdir(invoice_root):
            for root, _directories, files in os.walk(invoice_root):
                for file_name in files:
                    if file_name.lower().endswith(".pdf"):
                        files_by_prefix.setdefault(file_name, os.path.join(root, file_name))
        for invoice in invoices:
            detail = get_invoice_by_id(invoice["id"])
            if detail is None:
                missing += 1
                continue
            customer = get_customer_by_id(detail["customer_id"])
            if customer is None:
                missing += 1
                continue
            expected_path = invoice_pdf_path(detail, customer)
            source = detail.get("pdf_path")
            if (
                not source or not self._path_is_in_invoice_folder(source)
                or not os.path.isfile(source)
            ):
                matching = next(
                    (
                        path for name, path in files_by_prefix.items()
                        if self._matches_invoice_pdf(name, detail["invoice_number"])
                    ),
                    None,
                )
                source = matching
            if not source or not os.path.isfile(source):
                missing += 1
                continue
            try:
                os.makedirs(os.path.dirname(expected_path), exist_ok=True)
                if os.path.normcase(os.path.abspath(source)) == os.path.normcase(
                    os.path.abspath(expected_path)
                ):
                    update_invoice_pdf_path(detail["id"], expected_path)
                    continue
                if os.path.exists(expected_path):
                    missing += 1
                    continue
                shutil.move(source, expected_path)
                update_invoice_pdf_path(detail["id"], expected_path)
                moved += 1
            except (OSError, sqlite3.Error):
                missing += 1
        toast(
            self,
            f"Organised {moved} PDF(s); skipped {missing} missing or unavailable invoice PDF(s).",
            "success" if not missing else "info",
        )
        self.refresh()

    @staticmethod
    def _is_nonnegative_number(value):
        try:
            number = float(value)
            return math.isfinite(number) and number >= 0
        except ValueError:
            return False
