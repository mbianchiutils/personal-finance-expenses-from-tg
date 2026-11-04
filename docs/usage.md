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
