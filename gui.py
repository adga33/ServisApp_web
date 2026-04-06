import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import pandas as pd

from config import SHEETS, COLUMNS, ADMIN_LOZINKA, EXCEL_FILE
from database import append_row, load_sheet, backup_excel
from logic import filtriraj


def login_admin():
    win = tk.Toplevel()
    win.title("Admin prijava")
    win.resizable(False, False)

    tk.Label(win, text="Lozinka:").pack(padx=10, pady=5)
    entry = tk.Entry(win, show="*")
    entry.pack(padx=10, pady=5)

    def provjeri():
        if entry.get() == ADMIN_LOZINKA:
            messagebox.showinfo("Admin", "Prijava uspješna.")
            win.destroy()
        else:
            messagebox.showerror("Greška", "Pogrešna lozinka.")

    tk.Button(win, text="Prijava", command=provjeri).pack(padx=10, pady=10)


def start_gui():
    root = tk.Tk()
    root.title("Evidencija servisa plovila")
    root.geometry("1300x800")

    style = ttk.Style(root)
    style.theme_use("clam")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    tab_unos = ttk.Frame(notebook)
    notebook.add(tab_unos, text="Unos")

    ttk.Label(tab_unos, text="Plovilo:").grid(
        row=0, column=0, padx=5, pady=5, sticky="w"
    )
    combo_plovilo = ttk.Combobox(tab_unos, values=SHEETS, state="readonly", width=25)
    combo_plovilo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    label_zadnji = ttk.Label(tab_unos, text="Zadnji servis: -")
    label_zadnji.grid(row=0, column=2, padx=10, pady=5)

    label_sljedeci = ttk.Label(tab_unos, text="Sljedeći servis: -")
    label_sljedeci.grid(row=1, column=2, padx=10, pady=5)

    label_tehnicki = ttk.Label(tab_unos, text="Tehnički pregled: -")
    label_tehnicki.grid(row=2, column=2, padx=10, pady=5)

    label_upozorenje = ttk.Label(tab_unos, text="", foreground="white")
    label_upozorenje.grid(row=3, column=2, padx=10, pady=5)

    entries = {}

    ttk.Label(tab_unos, text="Datum:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entries["datum"] = DateEntry(tab_unos, width=22, date_pattern="dd.mm.yyyy")
    entries["datum"].grid(row=1, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(tab_unos, text="Trenutni radni sati:").grid(
        row=2, column=0, padx=5, pady=5, sticky="w"
    )
    entries["trenutni radni sati"] = ttk.Entry(tab_unos, width=25)
    entries["trenutni radni sati"].grid(row=2, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(tab_unos, text="Vrsta unosa:").grid(
        row=3, column=0, padx=5, pady=5, sticky="w"
    )
    entries["vrsta unosa"] = ttk.Combobox(
        tab_unos, values=["Servis", "Tehnički pregled", "Ostalo"], width=22
    )
    entries["vrsta unosa"].grid(row=3, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(tab_unos, text="Napomena:").grid(
        row=4, column=0, padx=5, pady=5, sticky="w"
    )
    entries["Napomena"] = ttk.Entry(tab_unos, width=40)
    entries["Napomena"].grid(row=4, column=1, padx=5, pady=5, sticky="w")

    def ucitaj_zadnji_servis(event=None):
        sheet = combo_plovilo.get()
        if not sheet:
            return

        df = load_sheet(sheet)
        df_servisi = df[df["vrsta unosa"] == "Servis"]

        if df_servisi.empty:
            zadnji_servis = 0
            sljedeci = 20
        else:
            zadnji_servis = int(df_servisi.iloc[-1]["servis rađen na"])
            broj_servisa = len(df_servisi)
            sljedeci = 20 + broj_servisa * 100

        label_zadnji.config(text=f"Zadnji servis: {zadnji_servis} h")
        label_sljedeci.config(text=f"Sljedeći servis: {sljedeci} h")

        entries["zadnji_servis"] = zadnji_servis
        entries["sljedeci_servis"] = sljedeci

        df_tech = df[df["vrsta unosa"] == "Tehnički pregled"]
        poruke = []

        if df_tech.empty:
            label_tehnicki.config(text="Tehnički pregled: nije evidentiran")
            label_tehnicki.config(background=root.cget("background"))
        else:
            zadnji_tech = df_tech.iloc[-1]["datum"]
            zadnji_tech_date = pd.to_datetime(zadnji_tech, format="%d.%m.%Y")
            istek = zadnji_tech_date + pd.DateOffset(years=2)
            danas = pd.Timestamp.today()
            dana_do_isteka = (istek - danas).days

            label_tehnicki.config(
                text=f"Istek: {istek.strftime('%d.%m.%Y')} ({dana_do_isteka} dana)"
            )

            if dana_do_isteka < 0:
                label_tehnicki.config(background="#ff4d4d")
                poruke.append(f"Tehnički istekao prije {abs(dana_do_isteka)} dana!")
            else:
                label_tehnicki.config(background=root.cget("background"))

        try:
            trenutni = int(df.iloc[-1]["trenutni radni sati"])
        except:
            trenutni = None

        if trenutni is not None:
            do_servisa = sljedeci - trenutni
            if do_servisa < 0:
                label_sljedeci.config(background="#ff4d4d")
                poruke.append(f"Servis kasni {abs(do_servisa)} h!")
            else:
                label_sljedeci.config(background=root.cget("background"))

        if poruke:
            label_upozorenje.config(
                text="\n".join(poruke), background="#ff4d4d", foreground="white"
            )
        else:
            label_upozorenje.config(text="", background=root.cget("background"))

    combo_plovilo.bind("<<ComboboxSelected>>", ucitaj_zadnji_servis)

    def spremi():
        sheet = combo_plovilo.get()
        if not sheet:
            messagebox.showerror("Greška", "Odaberi plovilo.")
            return

        if not entries["datum"].get():
            messagebox.showerror("Greška", "Datum mora biti odabran.")
            return

        if not entries["trenutni radni sati"].get().strip().isdigit():
            messagebox.showerror("Greška", "Radni sati moraju biti broj.")
            return

        trenutni = int(entries["trenutni radni sati"].get().strip())
        vrsta = entries["vrsta unosa"].get().strip()

        if vrsta == "Servis":
            servis_raden = trenutni
        else:
            servis_raden = entries["zadnji_servis"]

        ocekivani = entries["sljedeci_servis"]
        do_servisa = ocekivani - trenutni

        data = {
            "datum": entries["datum"].get(),
            "trenutni radni sati": trenutni,
            "servis rađen na": servis_raden,
            "očekivani servis": ocekivani,
            "do servisa": do_servisa,
            "vrsta unosa": vrsta,
            "Napomena": entries["Napomena"].get().strip(),
        }

        append_row(sheet, data)
        messagebox.showinfo("OK", "Zapis spremljen.")

        entries["trenutni radni sati"].delete(0, tk.END)
        entries["Napomena"].delete(0, tk.END)
        entries["vrsta unosa"].set("")

        ucitaj_zadnji_servis()

    ttk.Button(tab_unos, text="Spremi zapis", command=spremi).grid(
        row=5, column=0, columnspan=2, pady=10
    )
    ttk.Button(tab_unos, text="Pregled servisa", command=pregled_servisa).grid(
        row=6, column=0, padx=5, pady=5
    )

    def pregled_tehnickih():
        win = tk.Toplevel()
        win.title("Pregled tehničkih pregleda svih plovila")
        win.geometry("700x400")

        tree = ttk.Treeview(
            win, columns=["plovilo", "zadnji", "istek", "dana"], show="headings"
        )

        for col in ["plovilo", "zadnji", "istek", "dana"]:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.pack(fill="both", expand=True)
        tree.tag_configure("istekao", background="#ff4d4d", foreground="white")

        danas = pd.Timestamp.today()

        for sheet in SHEETS:
            df = load_sheet(sheet)
            df_tech = df[df["vrsta unosa"] == "Tehnički pregled"]

            if df_tech.empty:
                tree.insert("", "end", values=[sheet, "-", "-", "-"])
                continue

            zadnji = df_tech.iloc[-1]["datum"]
            zadnji_d = pd.to_datetime(zadnji, format="%d.%m.%Y")

            istek = zadnji_d + pd.DateOffset(years=2)
            dana = (istek - danas).days

            tag = "istekao" if dana < 0 else ""

            tree.insert(
                "",
                "end",
                values=[sheet, zadnji, istek.strftime("%d.%m.%Y"), dana],
                tags=(tag,),
            )

    ttk.Button(tab_unos, text="Pregled tehničkih", command=pregled_tehnickih).grid(
        row=6, column=1, padx=5, pady=5
    )

    tab_pregled = ttk.Frame(notebook)
    notebook.add(tab_pregled, text="Pregled")

    ttk.Label(tab_pregled, text="Plovilo:").grid(
        row=0, column=0, padx=5, pady=5, sticky="w"
    )
    combo_plovilo2 = ttk.Combobox(
        tab_pregled, values=SHEETS, state="readonly", width=25
    )
    combo_plovilo2.grid(row=0, column=1, padx=5, pady=5, sticky="w")

    ttk.Label(tab_pregled, text="Pretraga:").grid(
        row=1, column=0, padx=5, pady=5, sticky="w"
    )
    entry_search = ttk.Entry(tab_pregled, width=40)
    entry_search.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    tree = ttk.Treeview(tab_pregled, columns=COLUMNS, show="headings", height=18)
    for col in COLUMNS:
        tree.heading(col, text=col)
        tree.column(col, width=140)
    tree.grid(row=2, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")

    tab_pregled.rowconfigure(2, weight=1)
    tab_pregled.columnconfigure(3, weight=1)

    def osvjezi():
        sheet = combo_plovilo2.get()
        if not sheet:
            messagebox.showerror("Greška", "Odaberi plovilo.")
            return
        df = load_sheet(sheet)
        df_f = filtriraj(df, entry_search.get())

        for i in tree.get_children():
            tree.delete(i)
        for _, row in df_f.iterrows():
            tree.insert("", "end", values=[row.get(c, "") for c in COLUMNS])
