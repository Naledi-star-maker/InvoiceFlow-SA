import customtkinter as ctk


BG = "#FAFAFA"
SURFACE = "#FFFFFF"
TEXT = "#0A0A0B"
SECONDARY = "#52525B"
MUTED = "#8E8E99"
BORDER = "#E8E8EC"
PINK = "#DB2777"
PINK_HOVER = "#BE185D"
PINK_TINT = "#FDF2F8"
PINK_BORDER = "#FBCFE8"
DANGER = "#DC2626"
DANGER_HOVER = "#B91C1C"
SUCCESS = "#16A34A"
SIDEBAR = "#0A0A0B"
SIDEBAR_TEXT = "#A1A1AA"
SIDEBAR_HOVER = "#18181B"
SIDEBAR_ACTIVE = "#27272A"

FONT = "Segoe UI"
FONT_SIZE = {
    "small": 12,
    "label": 13,
    "body": 14,
    "heading": 16,
    "title": 20,
    "large": 28,
}
SPACE = (4, 8, 12, 16, 24, 32)
RADIUS_INPUT = 8
RADIUS_CARD = 12


def font(size=FONT_SIZE["body"], weight="normal"):
    return ctk.CTkFont(family=FONT, size=size, weight=weight)


def primary_button(parent, text, command=None, **kwargs):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=PINK,
        hover_color=PINK_HOVER,
        text_color=SURFACE,
        corner_radius=RADIUS_INPUT,
        font=font(FONT_SIZE["body"], "bold"),
        **kwargs,
    )


def secondary_button(parent, text, command=None, **kwargs):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=SURFACE,
        hover_color="#F4F4F5",
        text_color=TEXT,
        border_color=BORDER,
        border_width=1,
        corner_radius=RADIUS_INPUT,
        font=font(FONT_SIZE["body"]),
        **kwargs,
    )


def ghost_button(parent, text, command=None, **kwargs):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color="transparent",
        hover_color="#F4F4F5",
        text_color=SECONDARY,
        corner_radius=RADIUS_INPUT,
        font=font(FONT_SIZE["body"]),
        **kwargs,
    )


def danger_button(parent, text, command=None, **kwargs):
    return ctk.CTkButton(
        parent,
        text=text,
        command=command,
        fg_color=DANGER,
        hover_color=DANGER_HOVER,
        text_color=SURFACE,
        corner_radius=RADIUS_INPUT,
        font=font(FONT_SIZE["body"], "bold"),
        **kwargs,
    )


def labeled_entry(parent, label, *, placeholder="", helper="", show=None, **kwargs):
    field = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        field, text=label, text_color=SECONDARY, anchor="w",
        font=font(FONT_SIZE["label"], "bold"),
    ).pack(fill="x", pady=(0, 4))
    entry = ctk.CTkEntry(
        field,
        placeholder_text=placeholder,
        show=show,
        height=38,
        fg_color=SURFACE,
        text_color=TEXT,
        placeholder_text_color=SECONDARY,
        border_color=BORDER,
        corner_radius=RADIUS_INPUT,
        font=font(FONT_SIZE["body"]),
        **kwargs,
    )
    entry.pack(fill="x")
    if helper:
        ctk.CTkLabel(
            field, text=helper, text_color=SECONDARY, anchor="w",
            font=font(FONT_SIZE["small"]),
        ).pack(fill="x", pady=(4, 0))
    entry.field_container = field
    return entry


def labeled_dropdown(parent, label, values, *, helper="", **kwargs):
    field = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        field, text=label, text_color=SECONDARY, anchor="w",
        font=font(FONT_SIZE["label"], "bold"),
    ).pack(fill="x", pady=(0, 4))
    dropdown = ctk.CTkOptionMenu(
        field,
        values=values,
        height=38,
        fg_color=SURFACE,
        button_color=SURFACE,
        button_hover_color="#F4F4F5",
        text_color=TEXT,
        dropdown_fg_color=SURFACE,
        dropdown_text_color=TEXT,
        dropdown_hover_color="#F4F4F5",
        corner_radius=RADIUS_INPUT,
        font=font(FONT_SIZE["body"]),
        **kwargs,
    )
    dropdown.pack(fill="x")
    if helper:
        ctk.CTkLabel(
            field, text=helper, text_color=SECONDARY, anchor="w",
            font=font(FONT_SIZE["small"]),
        ).pack(fill="x", pady=(4, 0))
    dropdown.field_container = field
    return dropdown


def card(parent, **kwargs):
    return ctk.CTkFrame(
        parent,
        fg_color=SURFACE,
        border_color=BORDER,
        border_width=1,
        corner_radius=RADIUS_CARD,
        **kwargs,
    )


def page_header(parent, title, subtitle="", actions=None):
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.grid_columnconfigure(0, weight=1)
    title_block = ctk.CTkFrame(header, fg_color="transparent")
    title_block.grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(
        title_block, text=title, text_color=TEXT,
        font=font(FONT_SIZE["title"], "bold"), anchor="w",
    ).pack(anchor="w")
    if subtitle:
        ctk.CTkLabel(
            title_block, text=subtitle, text_color=SECONDARY,
            font=font(FONT_SIZE["body"]), anchor="w", justify="left",
        ).pack(anchor="w", pady=(4, 0))
    if actions is not None:
        action_frame = ctk.CTkFrame(header, fg_color="transparent")
        action_frame.grid(row=0, column=1, sticky="e", padx=(16, 0))
        actions(action_frame)
    return header


def stat_card(parent, label, value, caption="", accent=None, **kwargs):
    stat = card(parent, **kwargs)
    inner = ctk.CTkFrame(stat, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=16, pady=16)
    ctk.CTkLabel(
        inner, text=label, text_color=SECONDARY, anchor="w",
        font=font(FONT_SIZE["label"]),
    ).pack(fill="x")
    ctk.CTkLabel(
        inner, text=value, text_color=accent or TEXT, anchor="w",
        font=font(FONT_SIZE["title"], "bold"),
    ).pack(fill="x", pady=(8, 0))
    if caption:
        ctk.CTkLabel(
            inner, text=caption, text_color=SECONDARY, anchor="w",
            font=font(FONT_SIZE["small"]),
        ).pack(fill="x", pady=(4, 0))
    return stat


def data_table(parent, columns, rows, *, empty_text="No records yet.", row_command=None):
    table = ctk.CTkFrame(parent, fg_color=SURFACE)
    header = ctk.CTkFrame(table, fg_color=SURFACE, corner_radius=0)
    header.pack(fill="x")
    for index, column in enumerate(columns):
        header.grid_columnconfigure(index, weight=column.get("weight", 1))
        ctk.CTkLabel(
            header, text=column["label"], text_color=SECONDARY,
            anchor=column.get("anchor", "w"),
            font=font(FONT_SIZE["small"], "bold"),
        ).grid(row=0, column=index, sticky="ew", padx=12, pady=12)

    if not rows:
        empty_state(table, empty_text)
        return table

    for row_index, values in enumerate(rows):
        row = ctk.CTkFrame(table, fg_color=SURFACE, corner_radius=0)
        row.pack(fill="x")
        for column_index, column in enumerate(columns):
            row.grid_columnconfigure(column_index, weight=column.get("weight", 1))
            ctk.CTkLabel(
                row,
                text=str(values[column_index]),
                text_color=TEXT,
                anchor=column.get("anchor", "w"),
                font=font(FONT_SIZE["body"]),
            ).grid(row=0, column=column_index, sticky="ew", padx=12, pady=12)
        if row_index < len(rows) - 1:
            ctk.CTkFrame(table, height=1, fg_color=BORDER).pack(fill="x")
        if row_command is not None:
            row.bind("<Button-1>", lambda _event, i=row_index: row_command(i))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda _event, i=row_index: row_command(i))
        row.bind("<Enter>", lambda _event, widget=row: widget.configure(fg_color="#FAFAFA"))
        row.bind("<Leave>", lambda _event, widget=row: widget.configure(fg_color=SURFACE))
    return table


def empty_state(parent, text, action_text=None, command=None):
    state = ctk.CTkFrame(parent, fg_color="transparent")
    state.pack(fill="x", padx=16, pady=24)
    ctk.CTkLabel(
        state, text=text, text_color=SECONDARY,
        font=font(FONT_SIZE["body"]), justify="center",
    ).pack(pady=(0, 12))
    if action_text:
        primary_button(state, action_text, command, width=150, height=38).pack()
    return state


def toast(parent, message, kind="success", duration=3000):
    colors = {"success": SUCCESS, "error": DANGER, "info": TEXT}
    toast_window = ctk.CTkToplevel(parent)
    toast_window.withdraw()
    toast_window.overrideredirect(True)
    toast_window.attributes("-topmost", True)
    toast_window.configure(fg_color=colors.get(kind, TEXT))
    ctk.CTkLabel(
        toast_window, text=message, text_color=SURFACE,
        font=font(FONT_SIZE["body"], "bold"), padx=18, pady=12,
    ).pack()
    parent.update_idletasks()
    x = parent.winfo_rootx() + max(16, parent.winfo_width() - 360)
    y = parent.winfo_rooty() + 24
    toast_window.geometry(f"+{x}+{y}")
    toast_window.deiconify()
    toast_window.after(duration, toast_window.destroy)
    return toast_window


def confirm_dialog(parent, title, message, confirm_text="Confirm"):
    result = {"confirmed": False}
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("420x220")
    dialog.resizable(False, False)
    dialog.transient(parent.winfo_toplevel())
    dialog.grab_set()
    dialog.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        dialog, text=title, text_color=TEXT,
        font=font(FONT_SIZE["title"], "bold"),
    ).grid(row=0, column=0, sticky="w", padx=24, pady=(24, 8))
    ctk.CTkLabel(
        dialog, text=message, text_color=SECONDARY,
        font=font(FONT_SIZE["body"]), justify="left", wraplength=372,
    ).grid(row=1, column=0, sticky="w", padx=24)
    buttons = ctk.CTkFrame(dialog, fg_color="transparent")
    buttons.grid(row=2, column=0, sticky="e", padx=24, pady=24)

    def finish(confirmed):
        result["confirmed"] = confirmed
        dialog.destroy()

    secondary_button(buttons, "Cancel", command=lambda: finish(False), width=96).pack(
        side="left", padx=(0, 8)
    )
    danger_button(buttons, confirm_text, command=lambda: finish(True), width=112).pack(
        side="left"
    )
    dialog.protocol("WM_DELETE_WINDOW", lambda: finish(False))
    parent.wait_window(dialog)
    return result["confirmed"]


def loading_placeholder(parent, rows=4):
    placeholder = ctk.CTkFrame(parent, fg_color="transparent")
    for _ in range(rows):
        ctk.CTkFrame(
            placeholder, height=40, fg_color="#F4F4F5", corner_radius=RADIUS_INPUT
        ).pack(fill="x", pady=4)
    return placeholder


def set_inline_error(entry, message):
    field = getattr(entry, "field_container", None)
    if field is None:
        return
    for child in field.winfo_children():
        if getattr(child, "_inline_error", False):
            child.destroy()
    if message:
        error = ctk.CTkLabel(
            field, text=message, text_color=DANGER, anchor="w",
            font=font(FONT_SIZE["small"]),
        )
        error._inline_error = True
        error.pack(fill="x", pady=(4, 0))
        entry.configure(border_color=DANGER)
    else:
        entry.configure(border_color=BORDER)


def set_search_focus(widget):
    widget.configure(border_color=PINK)
    widget.bind("<FocusOut>", lambda _event: widget.configure(border_color=BORDER))
