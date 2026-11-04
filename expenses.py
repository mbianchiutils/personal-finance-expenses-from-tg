import re
import sys

try:
    import tkinter as tk
    from tkinter import font as tkfont, ttk
except ImportError:
    print("ERROR: tkinter is not available.")
    print("Please install it for your Python version:")
    print("  macOS:        brew install python-tk@3.x")
    print("  Debian/Ubuntu: sudo apt-get install python3-tk")
    print("  Fedora:       sudo dnf install python3-tkinter")
    print("\nOr run 'bash setup.sh' which will handle this automatically.")
    sys.exit(1)

# Check if running in a virtual environment
if not hasattr(sys, 'real_prefix') and not sys.base_prefix != sys.prefix:
    print("WARNING: It looks like you're not running this script in a virtual "
          "environment.")
    print("You might encounter errors with dependencies like 'pyperclip'.")
    print("\nTo set up a virtual environment:")
    print("1. Run: bash setup.sh")
    print("2. Activate the environment: source venv/bin/activate")
    print("3. Run this script again: python expenses.py\n")

try:
    import pyperclip  # type: ignore # For clipboard functionality
except ImportError:
    print("ERROR: The 'pyperclip' module is not installed.")
    print("Please run 'bash setup.sh' to set up the virtual environment and "
          "dependencies.")
    sys.exit(1)


def format_amount(amount):
    """Convert decimal points to commas in amount strings."""
    if '.' in amount and ',' not in amount:
        return amount.replace('.', ',')
    return amount


def get_currency_symbol(currency):
    """Map currency code to symbol, default to €."""
    symbols = {
        'USD': '$', 'GBP': '£', 'JPY': '¥', 'CHF': 'CHF',
        'CAD': 'CA$', 'AUD': 'A$', 'EUR': '€',
    }
    return symbols.get(currency, '€')


def process_input(input_str):
    # Match different format patterns:
    # 1. Standard format: Name, [DD/MM/YYYY HH:MM]\n<amount> <desc>
    # 2. Bracket format: [DD/MM/YYYY HH:MM] Name: <amount> [currency] <desc>
    # 3. Simple format: <amount> <expense name>
    # Process each message block separately
    message_blocks = re.split(
        r'\n(?=\w+[^,\n]+, \[|\[\d{1,2}/\d{1,2}/\d{4})', input_str)

    result_str = ""
    elaborated = 0
    skipped = 0
    for block in message_blocks:
        block = block.strip()
        if not block:
            continue

        # Try different patterns
        # Pattern 1: Name, [DD/MM/YYYY HH:MM]
        # Pattern 2: Name, [M/D/YYYY HH:MM AM/PM]
        patterns = [
            (r'(?:.+), \[(?:\d{1,2}/\d{1,2}/\d{4} '
             r'\d{1,2}:\d{1,2}(?:\s?[AP]M)?)\]\s*\n([\d,\.]+)\s+(.+)'),
            (r'(?:.+), \[(?:\d{1,2}/\d{1,2}/\d{4} '
             r'\d{1,2}:\d{1,2}(?:\s?[AP]M)?)\]\s*\n([\d,\.]+)\s+(.+)')
        ]

        matched = False
        for pattern in patterns:
            match = re.search(pattern, block)
            if match:
                amount = format_amount(match.group(1).strip())
                description = match.group(2).strip()
                result_str += f"{description}\t€ {amount}\n"
                elaborated += 1
                matched = True
                break

        # Pattern for: [DD/MM/YYYY HH:MM] Name: amount [currency] desc
        if not matched:
            bracket_match = re.search(
                r'\[\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\]\s+'
                r'.+?:\s+(\d+(?:[,\.]\d+)?)\s+'
                r'(?:(USD|EUR|GBP|CHF|JPY|CAD|AUD)\s+)?(.+)',
                block
            )
            if bracket_match:
                amount = format_amount(bracket_match.group(1).strip())
                currency = bracket_match.group(2)
                description = bracket_match.group(3).strip()
                symbol = get_currency_symbol(currency)
                result_str += f"{description}\t{symbol} {amount}\n"
                elaborated += 1
                matched = True

        # If no match was found, try a more relaxed pattern
        if not matched and re.search(r'\d+[,\.]?\d*', block):
            # Look for amount and description in the text
            # following the timestamp
            after_timestamp = re.split(r'\]\s*\n', block)
            if len(after_timestamp) > 1:
                content = after_timestamp[1].strip()
                # Extract amount and description
                amount_match = re.match(r'([\d,\.]+)\s+(.+)', content)
                if amount_match:
                    amount = format_amount(amount_match.group(1).strip())
                    description = amount_match.group(2).strip()
                    result_str += f"{description}\t€ {amount}\n"
                    elaborated += 1
                    matched = True

        # If still no match, try simple format: <amount> <description>
        # (Telegram web copy-paste format without timestamp)
        # Handle each line separately for this format since multiple simple
        # lines can be in one block (unlike timestamp-based formats)
        if not matched:
            for line in block.split('\n'):
                line = line.strip()
                if not line:
                    continue
                simple_match = re.match(r'^(\d+(?:[,\.]\d+)?)\s+(.+)$', line)
                if simple_match:
                    amount = format_amount(simple_match.group(1).strip())
                    description = simple_match.group(2).strip()
                    result_str += f"{description}\t€ {amount}\n"
                    elaborated += 1

        if not matched and not any(
            re.match(r'^(\d+(?:[,\.]\d+)?)\s+(.+)$', l.strip())
            for l in block.split('\n') if l.strip()
        ):
            skipped += 1

    return result_str.strip(), elaborated, skipped


def create_gui():
    root = tk.Tk()
    root.title("Telegram Expenses Parser")
    root.geometry("800x600")

    colors = {
        "background": "#F4F7FB",
        "surface": "#FFFFFF",
        "ink": "#182C48",
        "muted": "#52647D",
        "accent": "#2467DC",
        "success": "#167347",
        "border": "#DCE4EF",
        "hover": "#EDF2F9",
        "accent_hover": "#1D57BF",
        "success_hover": "#115B38",
        "error": "#A32837",
    }
    root.configure(background=colors["background"])

    families = set(tkfont.families(root))

    def choose_font(candidates, fallback):
        return next(
            (family for family in candidates if family in families),
            tkfont.nametofont(fallback, root=root).actual("family"),
        )

    body_family = choose_font(
        ("Segoe UI", "Helvetica Neue", "DejaVu Sans"), "TkDefaultFont"
    )
    display_family = choose_font(
        ("Avenir Next", "Segoe UI", "DejaVu Sans"), "TkDefaultFont"
    )
    mono_family = choose_font(
        ("Menlo", "Consolas", "DejaVu Sans Mono"), "TkFixedFont"
    )

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure(
        ".", background=colors["background"], foreground=colors["ink"],
        font=(body_family, 10),
    )
    style.configure("Card.TFrame", background=colors["surface"])
    style.configure(
        "Title.TLabel", font=(display_family, 22, "bold")
    )
    style.configure("Muted.TLabel", foreground=colors["muted"])
    style.configure(
        "PanelTitle.TLabel", background=colors["surface"],
        font=(body_family, 12, "bold"),
    )
    style.configure(
        "PanelHint.TLabel", background=colors["surface"],
        foreground=colors["muted"],
    )
    style.configure("Error.TLabel", foreground=colors["error"])
    style.configure(
        "TButton", padding=(12, 10), font=(body_family, 10, "bold"),
        background=colors["surface"], foreground=colors["ink"],
        bordercolor=colors["border"], lightcolor=colors["surface"],
        darkcolor=colors["surface"], focuscolor=colors["accent"],
        borderwidth=1, relief="flat", width=0,
    )
    style.map(
        "TButton",
        background=[("pressed", colors["border"]), ("active", colors["hover"])],
        bordercolor=[("focus", colors["accent"])],
    )
    for name, color, hover in (
        ("Primary", colors["accent"], colors["accent_hover"]),
        ("Success", colors["success"], colors["success_hover"]),
    ):
        style.configure(
            f"{name}.TButton", background=color, foreground=colors["surface"],
            bordercolor=color, lightcolor=color, darkcolor=color,
            focuscolor=colors["surface"],
        )
        style.map(
            f"{name}.TButton",
            background=[("pressed", hover), ("active", hover)],
            bordercolor=[("focus", colors["ink"]), ("!focus", color)],
        )
    style.configure(
        "Editor.Vertical.TScrollbar", background=colors["border"],
        troughcolor=colors["surface"], borderwidth=0,
        lightcolor=colors["border"], darkcolor=colors["border"],
        bordercolor=colors["border"], arrowsize=12, gripcount=0,
    )
    style.layout("Editor.Vertical.TScrollbar", [
        ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"sticky": "nswe"}),
        ]}),
    ])
    style.map(
        "Editor.Vertical.TScrollbar",
        background=[("active", colors["muted"])],
    )

    content = ttk.Frame(root, padding=24)
    content.pack(fill=tk.BOTH, expand=True)
    content.columnconfigure(0, weight=1)
    content.rowconfigure(1, weight=1)

    header = ttk.Frame(content)
    header.grid(row=0, column=0, sticky=tk.EW, pady=(0, 20))
    mark = tk.Canvas(
        header, width=44, height=44, background=colors["background"],
        highlightthickness=0,
    )
    mark.create_polygon(
        5, 19, 39, 6, 28, 39, 21, 26, 13, 30, 15, 23,
        fill=colors["accent"], outline="",
    )
    mark.create_line(
        15, 23, 32, 13, fill=colors["surface"], width=2,
        capstyle=tk.ROUND,
    )
    mark.pack(side=tk.LEFT, padx=(0, 12))
    heading = ttk.Frame(header)
    heading.pack(side=tk.LEFT)
    ttk.Label(
        heading, text="Telegram expenses", style="Title.TLabel"
    ).pack(anchor=tk.W)
    ttk.Label(
        heading, text="Copy your Telegram messages below.", style="Muted.TLabel"
    ).pack(anchor=tk.W, pady=(4, 0))

    text_frame = ttk.Frame(content)
    text_frame.grid(row=1, column=0, sticky=tk.NSEW)
    text_frame.columnconfigure((0, 1), weight=1, uniform="editors")
    text_frame.rowconfigure(0, weight=1)

    def create_editor(column, title, hint, family):
        card = tk.Frame(
            text_frame, background=colors["surface"], borderwidth=0,
            highlightthickness=1, highlightbackground=colors["border"],
        )
        card.grid(
            row=0, column=column, sticky=tk.NSEW,
            padx=(0, 8) if column == 0 else (8, 0),
        )
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)
        labels = ttk.Frame(card, style="Card.TFrame", padding=(16, 16, 16, 8))
        labels.grid(row=0, column=0, sticky=tk.EW)
        ttk.Label(
            labels, text=title, style="PanelTitle.TLabel"
        ).pack(anchor=tk.W)
        ttk.Label(
            labels, text=hint, style="PanelHint.TLabel"
        ).pack(anchor=tk.W, pady=(4, 0))

        editor_frame = ttk.Frame(
            card, style="Card.TFrame", padding=(14, 0, 14, 14)
        )
        editor_frame.grid(row=1, column=0, sticky=tk.NSEW)
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=1)
        editor = tk.Text(
            editor_frame, wrap=tk.WORD, width=1, height=12,
            font=(family, 11), background=colors["surface"],
            foreground=colors["ink"], insertbackground=colors["accent"],
            selectbackground=colors["accent"],
            selectforeground=colors["surface"],
            relief=tk.FLAT, borderwidth=0, highlightthickness=2,
            highlightbackground=colors["surface"],
            highlightcolor=colors["accent"], padx=8, pady=8,
            spacing1=2, spacing3=3,
        )
        editor.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar = ttk.Scrollbar(
            editor_frame, orient=tk.VERTICAL, command=editor.yview,
            style="Editor.Vertical.TScrollbar",
        )
        scrollbar.grid(row=0, column=1, sticky=tk.NS, padx=(6, 0))
        editor.configure(yscrollcommand=scrollbar.set)
        return editor

    input_text = create_editor(
        0, "Telegram messages", "Input: paste your messages here", body_family
    )
    output_text = create_editor(
        1, "Formatted expenses", "Output: ready for your spreadsheet", mono_family
    )

    footer = ttk.Frame(content)
    footer.grid(row=2, column=0, sticky=tk.EW, pady=(16, 0))
    status_frame = ttk.Frame(footer)
    status_frame.pack(fill=tk.X)
    stats_label = ttk.Label(
        status_frame, text="Elaborated: 0 | Skipped: 0", style="Muted.TLabel"
    )
    stats_label.pack(side=tk.LEFT)
    copy_status = ttk.Label(status_frame, style="Error.TLabel")
    copy_status.pack(side=tk.RIGHT)
    button_frame = ttk.Frame(footer)
    button_frame.pack(fill=tk.X, pady=(12, 0))
    copy_reset_id = None

    def reset_copy_feedback():
        nonlocal copy_reset_id
        if copy_reset_id is not None:
            root.after_cancel(copy_reset_id)
            copy_reset_id = None
        copy_button.configure(text="Copy Output", style="TButton")
        copy_status.configure(text="")

    def on_process():
        reset_copy_feedback()
        input_content = input_text.get("1.0", tk.END)
        output_content, elaborated, skipped = process_input(input_content)
        output_text.delete("1.0", tk.END)
        output_text.insert("1.0", output_content)
        stats_label.config(
            text=f"Elaborated: {elaborated} | Skipped: {skipped}"
        )

    def on_copy():
        nonlocal copy_reset_id
        reset_copy_feedback()
        output_content = output_text.get("1.0", tk.END).strip()
        try:
            pyperclip.copy(output_content)
        except (pyperclip.PyperclipException, OSError) as error:
            print(f"ERROR: Could not copy output: {error}", file=sys.stderr)
            copy_status.configure(
                text="Could not copy. Check your clipboard setup."
            )
            return
        copy_button.configure(text="\u2713 Copied", style="Success.TButton")
        copy_reset_id = root.after(2000, reset_copy_feedback)

    def on_clear_input():
        input_text.delete("1.0", tk.END)

    def on_clear_output():
        reset_copy_feedback()
        output_text.delete("1.0", tk.END)

    def on_reverse():
        content = output_text.get("1.0", tk.END).strip()
        if content:
            reset_copy_feedback()
            lines = content.split('\n')
            lines.reverse()
            output_text.delete("1.0", tk.END)
            output_text.insert("1.0", '\n'.join(lines))

    process_button = ttk.Button(
        button_frame, text="Process", command=on_process, style="Primary.TButton"
    )
    process_button.pack(side=tk.LEFT, padx=(0, 8))
    copy_button = ttk.Button(
        button_frame, text="Copy Output", command=on_copy, width=12
    )
    copy_button.pack(side=tk.LEFT, padx=(0, 8))
    for text, command in (
        ("Clear Input", on_clear_input),
        ("Clear Output", on_clear_output),
        ("Reverse Order", on_reverse),
    ):
        ttk.Button(
            button_frame, text=text, command=command
        ).pack(side=tk.LEFT, padx=(0, 8))

    def on_output_modified(event):
        if output_text.edit_modified():
            reset_copy_feedback()
            output_text.edit_modified(False)

    def on_destroy(event):
        nonlocal copy_reset_id
        if event.widget is root and copy_reset_id is not None:
            root.after_cancel(copy_reset_id)
            copy_reset_id = None

    output_text.bind("<<Modified>>", on_output_modified)
    root.bind("<Destroy>", on_destroy, add=True)
    root.update_idletasks()
    root.minsize(max(760, content.winfo_reqwidth()), 520)
    input_text.focus_set()
    root.mainloop()


if __name__ == "__main__":
    create_gui()
