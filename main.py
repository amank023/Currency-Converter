import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime

API_URL = "https://api.exchangerate-api.com/v4/latest/USD"


class CurrencyConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Currency Converter")
        self.geometry("700x500")        # starting size
        self.minsize(400, 300)          # user can freely maximize/minimize

        # allow everything to stretch so the child frame can stay centered
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.history = []

        container = tk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (ConverterPage, HistoryPage, AboutPage):
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(ConverterPage)

    def show_frame(self, page):
        """Raise the requested page and refresh if needed."""
        frame = self.frames[page]
        if page == HistoryPage:
            frame.refresh_history()
        frame.tkraise()


class FilterableCombobox(ttk.Combobox):
    """Combobox that filters items as the user types."""
    def __init__(self, master=None, **kwargs):
        self._full_values = kwargs.get("values", [])
        var = kwargs.get("textvariable", None)
        if var is None:
            var = tk.StringVar()
            kwargs["textvariable"] = var
        super().__init__(master, **kwargs)

        self._var = var  # actual StringVar object
        self._var.trace_add("write", self._on_change)
        # open dropdown as user types
        self.bind("<KeyRelease>", lambda e: self.event_generate("<Down>"))

    def _on_change(self, *args):
        typed = self._var.get().upper()
        if not typed:
            self["values"] = self._full_values
        else:
            self["values"] = [v for v in self._full_values if v.startswith(typed)]


class BasePage(tk.Frame):
    """
    Base page with an inner self.center frame that stays centered
    regardless of window size.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.center = tk.Frame(self)
        self.center.grid(row=0, column=0)  # grid keeps it perfectly centered


class ConverterPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self.center, text="Currency Converter",
                 font=("Arial", 20, "bold")).pack(pady=15)

        self.amount_var = tk.StringVar()
        self.from_currency = tk.StringVar()
        self.to_currency = tk.StringVar()
        self.result_var = tk.StringVar(value="Result will appear here")

        self.currencies = self.get_currency_list()

        tk.Label(self.center, text="Amount:").pack()
        tk.Entry(self.center, textvariable=self.amount_var,
                 width=25, justify="center").pack(pady=5)

        tk.Label(self.center, text="From Currency:").pack()
        self.from_box = FilterableCombobox(
            self.center, textvariable=self.from_currency,
            values=self.currencies, state="normal", width=20
        )
        self.from_box.pack(pady=5)

        tk.Label(self.center, text="To Currency:").pack()
        self.to_box = FilterableCombobox(
            self.center, textvariable=self.to_currency,
            values=self.currencies, state="normal", width=20
        )
        self.to_box.pack(pady=5)

        tk.Button(self.center, text="Convert", command=self.convert).pack(pady=12)
        tk.Label(self.center, textvariable=self.result_var,
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Navigation buttons
        nav = tk.Frame(self.center)
        nav.pack(pady=10)
        tk.Button(nav, text="History",
                  command=lambda: controller.show_frame(HistoryPage)).pack(side="left", padx=6)
        tk.Button(nav, text="About",
                  command=lambda: controller.show_frame(AboutPage)).pack(side="left", padx=6)

    def get_currency_list(self):
        """Fetch list of available currency codes."""
        try:
            r = requests.get(API_URL, timeout=5)
            data = r.json()
            return sorted(data["rates"].keys())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch currency list.\n{e}")
            return ["USD", "INR", "EUR"]

    def convert(self):
        amount = self.amount_var.get()
        from_cur = self.from_currency.get().upper()
        to_cur = self.to_currency.get().upper()

        if not amount or not from_cur or not to_cur:
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        try:
            amount = float(amount)
        except ValueError:
            messagebox.showerror("Invalid", "Amount must be a number.")
            return

        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_cur}"
            data = requests.get(url, timeout=5).json()
            if to_cur not in data["rates"]:
                messagebox.showerror("Error", "Currency not supported.")
                return
            rate = data["rates"][to_cur]
            result = round(amount * rate, 2)
            text = f"{amount} {from_cur} = {result} {to_cur}"
            self.result_var.set(text)
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.controller.history.append(f"[{stamp}] {text}")
        except Exception as e:
            messagebox.showerror("Error", f"Conversion failed.\n{e}")


class HistoryPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self.center, text="Conversion History",
                 font=("Arial", 20, "bold")).pack(pady=15)

        self.history_box = tk.Listbox(self.center, width=80, height=18)
        self.history_box.pack(pady=10, fill="both", expand=True)

        nav = tk.Frame(self.center)
        nav.pack(pady=10)
        tk.Button(nav, text="Back to Converter",
                  command=lambda: controller.show_frame(ConverterPage)).pack(side="left", padx=6)
        tk.Button(nav, text="About",
                  command=lambda: controller.show_frame(AboutPage)).pack(side="left", padx=6)

    def refresh_history(self):
        self.history_box.delete(0, tk.END)
        if not self.controller.history:
            self.history_box.insert(tk.END, "No conversions yet.")
        else:
            for item in self.controller.history:
                self.history_box.insert(tk.END, item)


class AboutPage(BasePage):
    def __init__(self, parent, controller):
        super().__init__(parent)
        tk.Label(self.center, text="About This App",
                 font=("Arial", 20, "bold")).pack(pady=15)
        tk.Label(
            self.center,
            text=("Currency Converter\nBuilt with Python & Tkinter\n"
                  "Live rates via ExchangeRate API\n"
                  "Features: Auto-filter dropdown & History"),
            justify="center"
        ).pack(pady=20)

        nav = tk.Frame(self.center)
        nav.pack(pady=10)
        tk.Button(nav, text="Back to Converter",
                  command=lambda: controller.show_frame(ConverterPage)).pack(side="left", padx=6)
        tk.Button(nav, text="History",
                  command=lambda: controller.show_frame(HistoryPage)).pack(side="left", padx=6)


if __name__ == "__main__":
    app = CurrencyConverterApp()
    app.mainloop()
