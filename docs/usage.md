# Usage

Run the setup script for your platform as described in the [README](../README.md).
The app still uses Tkinter and pyperclip; no additional app dependencies are needed.

Paste Telegram messages into **Telegram messages**, then select **Process**.
The **Formatted expenses** pane contains tab-separated descriptions and amounts
that you can paste into a spreadsheet. The elaborated and skipped counts show
how many messages were recognized.

Select **Copy Output** to copy the formatted text. A green **Copied** label with
a checkmark confirms a successful copy for two seconds. Changing the output
clears that confirmation. Clipboard failures appear below the editors and are
also logged to stderr.

**Reverse Order** reverses the output rows. **Clear Input** and **Clear Output**
clear only their respective panes. Both panes remain editable and scrollable.

## Messages without timestamps

Repeated `Expenses:` headings and blank lines are supported:

```text
Expenses:
14,25 Sample ride

Expenses:
9 Sample dinner (42 number for order)
```

Each expense starts with an amount followed by a description. Amounts can be
whole numbers or use decimal commas or points; points become commas in the
output. The headings and blank lines do not create output rows or count as
skipped messages when included with expenses. Numbers inside descriptions stay
in the description, so the second example has an amount of `9`, not `42`.

## Development checks

With the virtual environment activated and Tkinter available:

```bash
python -m unittest discover -s tests -v
python -m compileall -q expenses.py tests
```

The GUI tests create Tkinter windows and mock clipboard contents. On a headless
Linux machine, run the tests under Xvfb:

```bash
xvfb-run -a python -m unittest discover -s tests -v
```
