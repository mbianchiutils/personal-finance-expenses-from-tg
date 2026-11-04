import io
import tkinter as tk
import unittest
from tkinter import ttk
from unittest import mock

import expenses


def walk_widgets(widget):
    for child in widget.winfo_children():
        yield child
        yield from walk_widgets(child)


class ParserTests(unittest.TestCase):
    def test_decimal_and_currency_formatting(self):
        self.assertEqual(expenses.format_amount("12.50"), "12,50")
        self.assertEqual(expenses.format_amount("12,50"), "12,50")
        self.assertEqual(expenses.get_currency_symbol("USD"), "$")
        self.assertEqual(expenses.get_currency_symbol(None), "\u20ac")

    def test_simple_expenses(self):
        self.assertEqual(
            expenses.process_input("12.50 Sample groceries\n3 Sample coffee"),
            ("Sample groceries\t\u20ac 12,50\nSample coffee\t\u20ac 3", 2, 0),
        )

    def test_telegram_messages(self):
        self.assertEqual(
            expenses.process_input(
                "Example User, [01/01/2025 10:00]\n12.50 Sample groceries\n"
                "Example User, [01/01/2025 11:00]\n3 Sample coffee"
            ),
            ("Sample groceries\t\u20ac 12,50\nSample coffee\t\u20ac 3", 2, 0),
        )

    def test_bracket_messages_keep_their_currency(self):
        self.assertEqual(
            expenses.process_input(
                "[01/01/2025 10:00] Example User: 12.50 USD Sample groceries\n"
                "[01/01/2025 11:00] Example User: 3 GBP Sample coffee"
            ),
            ("Sample groceries\t$ 12,50\nSample coffee\t\u00a3 3", 2, 0),
        )

    def test_empty_and_unrecognized_messages(self):
        self.assertEqual(expenses.process_input(""), ("", 0, 0))
        self.assertEqual(
            expenses.process_input("Not an expense\nStill not an expense"),
            ("", 0, 1),
        )


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.addCleanup(self.destroy_root)
        with mock.patch("expenses.tk.Tk", return_value=self.root):
            with mock.patch.object(self.root, "mainloop"):
                expenses.create_gui()
        self.root.withdraw()
        self.root.update()

        widgets = list(walk_widgets(self.root))
        self.input_text, self.output_text = [
            widget for widget in widgets if isinstance(widget, tk.Text)
        ]
        self.buttons = {
            widget.cget("text"): widget
            for widget in widgets
            if isinstance(widget, (tk.Button, ttk.Button))
        }
        self.labels = [
            widget for widget in widgets
            if isinstance(widget, (tk.Label, ttk.Label))
        ]
        clipboard = mock.patch("expenses.pyperclip.copy")
        self.copy = clipboard.start()
        self.addCleanup(clipboard.stop)

    def destroy_root(self):
        if self.root is not None:
            self.root.destroy()
        self.root = None

    def set_output(self, text="Sample groceries\t\u20ac 12,50"):
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.root.update()

    def label_texts(self):
        return [label.cget("text") for label in self.labels]

    def test_existing_actions_are_present(self):
        self.assertEqual(
            list(self.buttons),
            ["Process", "Copy Output", "Clear Input", "Clear Output",
             "Reverse Order"],
        )

    def test_processing_keeps_output_and_counts(self):
        self.input_text.insert("1.0", "12.50 Sample groceries\n3 Sample coffee")
        self.buttons["Process"].invoke()
        self.root.update()
        self.assertEqual(
            self.output_text.get("1.0", tk.END).strip(),
            "Sample groceries\t\u20ac 12,50\nSample coffee\t\u20ac 3",
        )
        self.assertIn("Elaborated: 2 | Skipped: 0", self.label_texts())

    def test_actions_fit_at_the_minimum_window_size(self):
        self.root.geometry("760x520")
        self.root.deiconify()
        self.root.update()
        for button in self.buttons.values():
            with self.subTest(action=button.cget("text")):
                self.assertGreaterEqual(
                    button.winfo_width(), button.winfo_reqwidth()
                )

    def test_actions_fit_with_larger_display_scaling(self):
        self.destroy_root()
        self.root = tk.Tk()
        self.root.tk.call("tk", "scaling", 2.0)
        with mock.patch("expenses.tk.Tk", return_value=self.root):
            with mock.patch.object(self.root, "mainloop"):
                expenses.create_gui()
        self.root.geometry("760x520")
        self.root.update()
        buttons = [
            widget for widget in walk_widgets(self.root)
            if isinstance(widget, ttk.Button)
        ]
        for button in buttons:
            with self.subTest(action=button.cget("text")):
                self.assertGreaterEqual(
                    button.winfo_width(), button.winfo_reqwidth()
                )

    def test_copy_acknowledges_success_with_a_checkmark(self):
        self.set_output()
        self.buttons["Copy Output"].invoke()
        self.copy.assert_called_once_with("Sample groceries\t\u20ac 12,50")
        self.assertEqual(
            self.buttons["Copy Output"].cget("text"), "\u2713 Copied"
        )

    def test_copy_feedback_expires(self):
        self.set_output()
        with mock.patch.object(self.root, "after", return_value="feedback") as after:
            with mock.patch.object(self.root, "after_cancel"):
                self.buttons["Copy Output"].invoke()
                delay, restore = after.call_args.args
                self.assertEqual(delay, 2000)
                restore()
        self.assertEqual(
            self.buttons["Copy Output"].cget("text"), "Copy Output"
        )

    def test_repeated_copy_restarts_feedback(self):
        self.set_output()
        with mock.patch.object(
            self.root, "after", side_effect=["first", "second"]
        ) as after:
            with mock.patch.object(self.root, "after_cancel") as cancel:
                self.buttons["Copy Output"].invoke()
                self.buttons["Copy Output"].invoke()
                cancel.assert_called_once_with("first")
                self.assertEqual(after.call_count, 2)
                after.call_args.args[1]()
        self.assertEqual(self.copy.call_count, 2)

    def test_clipboard_failure_is_visible_and_logged(self):
        self.set_output()
        self.buttons["Copy Output"].invoke()
        self.copy.side_effect = expenses.pyperclip.PyperclipException(
            "Mock clipboard unavailable"
        )
        with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.buttons["Copy Output"].invoke()
        self.assertEqual(
            self.buttons["Copy Output"].cget("text"), "Copy Output"
        )
        self.assertTrue(any("Could not copy" in text for text in self.label_texts()))
        self.assertIn("Mock clipboard unavailable", stderr.getvalue())

    def test_processing_resets_copy_feedback(self):
        self.set_output()
        self.buttons["Copy Output"].invoke()
        self.input_text.insert("1.0", "3 Sample coffee")
        self.buttons["Process"].invoke()
        self.root.update()
        self.assertEqual(
            self.buttons["Copy Output"].cget("text"), "Copy Output"
        )

    def test_editing_output_resets_feedback(self):
        self.set_output()
        self.buttons["Copy Output"].invoke()
        self.output_text.insert(tk.END, "\nSample coffee\t\u20ac 3")
        self.root.update()
        self.assertEqual(
            self.buttons["Copy Output"].cget("text"), "Copy Output"
        )

    def test_reversing_output_resets_feedback_and_keeps_rows(self):
        self.set_output("Sample groceries\t\u20ac 12,50\nSample coffee\t\u20ac 3")
        self.buttons["Copy Output"].invoke()
        self.buttons["Reverse Order"].invoke()
        self.root.update()
        self.assertEqual(
            self.output_text.get("1.0", tk.END).strip(),
            "Sample coffee\t\u20ac 3\nSample groceries\t\u20ac 12,50",
        )
        self.assertEqual(
            self.buttons["Copy Output"].cget("text"), "Copy Output"
        )

    def test_clear_actions_remain_independent(self):
        self.input_text.insert("1.0", "3 Sample coffee")
        self.set_output()
        self.buttons["Clear Input"].invoke()
        self.assertEqual(self.input_text.get("1.0", tk.END).strip(), "")
        self.assertNotEqual(self.output_text.get("1.0", tk.END).strip(), "")

        self.input_text.insert("1.0", "3 Sample coffee")
        self.buttons["Copy Output"].invoke()
        self.buttons["Clear Output"].invoke()
        self.root.update()
        self.assertEqual(self.output_text.get("1.0", tk.END).strip(), "")
        self.assertEqual(
            self.input_text.get("1.0", tk.END).strip(), "3 Sample coffee"
        )
        self.assertEqual(
            self.buttons["Copy Output"].cget("text"), "Copy Output"
        )

    def test_destroy_cancels_pending_copy_feedback(self):
        self.set_output()
        timers_before = set(self.root.tk.call("after", "info"))
        self.buttons["Copy Output"].invoke()
        feedback_timers = set(self.root.tk.call("after", "info")) - timers_before
        self.assertEqual(len(feedback_timers), 1)
        interpreter = self.root.tk
        self.destroy_root()
        self.assertTrue(
            feedback_timers.isdisjoint(interpreter.call("after", "info"))
        )


if __name__ == "__main__":
    unittest.main()
