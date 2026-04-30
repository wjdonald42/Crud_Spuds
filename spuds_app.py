import sqlite3
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

#CRUD Spuds - DS3850 Group Final
#Team: Wyatt Graves, Andrew Tyler, Braden Clark, Jackson Donald, Andrew Taylor
#Domain: Potato restaurant menu and orders

DB_NAME = "crud_spuds.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def setup_database():
    conn = get_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS spuds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        price REAL,
        active INTEGER DEFAULT 1
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spud_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        quantity INTEGER,
        total REAL,
        FOREIGN KEY (spud_id) REFERENCES spuds(id)
    )''')

    # only seed if empty
    c.execute("SELECT COUNT(*) FROM spuds")
    if c.fetchone()[0] == 0:
        seed_spuds = [
            ('The OG Skin On', 'Classic', 5.00),
            ('Heat Sweat',     'Sweet',   7.50),
            ('Bacon Blaster',  'Loaded',  9.00),
            ('Truffle Tot',    'Gourmet', 12.00),
            ('Chili Cheese',   'Loaded',  8.50),
            ('Garlic Herb',    'Classic', 6.00),
            ('Boneless Spud',  'Loaded',  11.00),
            ('Ukraine Tato',   'Classic', 7.00),
            ('Maple Yam',      'Sweet',   6.50),
            ('Crazy Train',    'Gourmet', 15.00),
        ]
        c.executemany("INSERT INTO spuds (name, category, price) VALUES (?, ?, ?)", seed_spuds)

    c.execute("SELECT COUNT(*) FROM orders")
    if c.fetchone()[0] == 0:
        seed_orders = [
            (1, '2025-01-10', 2, 10.00),
            (3, '2025-01-11', 1, 9.00),
            (4, '2025-01-12', 3, 36.00),
            (2, '2025-01-13', 2, 15.00),
            (5, '2025-01-14', 4, 34.00),
            (6, '2025-01-15', 1, 6.00),
            (7, '2025-01-16', 2, 22.00),
            (8, '2025-01-17', 3, 21.00),
            (9, '2025-01-18', 1, 6.50),
            (10,'2025-01-19', 2, 30.00),
        ]
        c.executemany("INSERT INTO orders (spud_id, date, quantity, total) VALUES (?, ?, ?, ?)", seed_orders)

    conn.commit()
    conn.close()


class SpudsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CRUD Spuds")
        self.root.geometry("960x680")

        self.conn = get_connection()

        self.notebook = ttk.Notebook(root)
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text="Menu Items")
        self.notebook.add(self.tab2, text="Orders")
        self.notebook.add(self.tab3, text="Reports")
        self.notebook.pack(fill="both", expand=True)

        self.build_menu_tab()
        self.build_orders_tab()
        self.build_reports_tab()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

#TAB 1
#Wyatt Graves + Andrew Tyler - menu CRUD
    def make_menu_tab(self):
        # ---- input form ----
        form = ttk.LabelFrame(self.tab1, text="Add / Edit Spud")
        form.pack(fill="x", padx=10, pady=8)

        ttk.Label(form, text="Name:").grid(row=0, column=0, padx=5, pady=4, sticky="e")
        self.ent_name = ttk.Entry(form, width=22)
        self.ent_name.grid(row=0, column=1, padx=5)

        ttk.Label(form, text="Category:").grid(row=0, column=2, padx=5, sticky="e")
        self.ent_cat = ttk.Combobox(form, values=["Classic", "Loaded", "Sweet", "Gourmet"], width=14)
        self.ent_cat.grid(row=0, column=3, padx=5)

        ttk.Label(form, text="Price ($):").grid(row=0, column=4, padx=5, sticky="e")
        self.ent_price = ttk.Entry(form, width=10)
        self.ent_price.grid(row=0, column=5, padx=5)

        ttk.Button(form, text="Add Spud",    command=self.add_spud).grid(row=1, column=1, pady=6)
        ttk.Button(form, text="Save Update", command=self.update_spud).grid(row=1, column=3, pady=6)
        ttk.Button(form, text="Clear Form",  command=self.clear_spud_form).grid(row=1, column=5, pady=6)

        ttk.Label(self.tab1, text="Tip: click a row below to load it into the form for editing",
                  foreground="gray").pack(anchor="w", padx=12)

#search/filter
        filt = ttk.Frame(self.tab1)
        filt.pack(fill="x", padx=10)
        ttk.Label(filt, text="Filter by category:").pack(side="left")
        self.filter_var = tk.StringVar(value="All")
        filter_box = ttk.Combobox(filt, textvariable=self.filter_var,
                                  values=["All", "Classic", "Loaded", "Sweet", "Gourmet"], width=12)
        filter_box.pack(side="left", padx=5)
        ttk.Button(filt, text="Apply", command=self.refresh_spuds).pack(side="left")

    #treeview
        cols = ("ID", "Name", "Category", "Price", "Active")
        self.tree_spuds = ttk.Treeview(self.tab1, columns=cols, show="headings", height=16)
        for c in cols:
            self.tree_spuds.heading(c, text=c)
            self.tree_spuds.column(c, width=120)
        self.tree_spuds.pack(fill="both", expand=True, padx=10, pady=5)
        self.tree_spuds.bind("<<TreeviewSelect>>", self.load_spud_into_form)

#lower buttons
        btns = ttk.Frame(self.tab1)
        btns.pack(pady=4)
        ttk.Button(btns, text="Delete Selected",        command=self.delete_spud).pack(side="left", padx=6)
        ttk.Button(btns, text="Toggle Active/Inactive", command=self.toggle_active).pack(side="left", padx=6)

        self.refresh_spuds()

    def plus_spud(self):
        name  = self.ent_name.get().strip()
        cat   = self.ent_cat.get().strip()
        price = self.ent_price.get().strip()

        if not name:
            messagebox.showerror("Error", "Name can't be empty")
            return
        try:
            price = float(price)
        except ValueError:
            messagebox.showerror("Error", "Price needs to be a number")
            return

        self.conn.execute("INSERT INTO spuds (name, category, price) VALUES (?, ?, ?)",
                          (name, cat, price))
        self.conn.commit()
        self.refresh_spuds()
        self.clear_spud_form()
        messagebox.showinfo("Added", f"{name} added to menu")

    def update_spud(self):
        sel = self.tree_spuds.selection()
        if not sel:
            messagebox.showwarning("Hold on", "Select a row first")
            return
        spud_id = self.tree_spuds.item(sel[0])['values'][0]
        try:
            price = float(self.ent_price.get())
        except ValueError:
            messagebox.showerror("Error", "Bad price value")
            return
        self.conn.execute("UPDATE spuds SET name=?, category=?, price=? WHERE id=?",
                          (self.ent_name.get(), self.ent_cat.get(), price, spud_id))
        self.conn.commit()
        self.refresh_spuds()

    def del_spud(self):
        sel = self.tree_spuds.selection()
        if not sel:
            return
        spud_id = self.tree_spuds.item(sel[0])['values'][0]
        if messagebox.askyesno("Delete?", "Are you sure?"):
            self.conn.execute("DELETE FROM spuds WHERE id=?", (spud_id,))
            self.conn.commit()
            self.refresh_spuds()

    def toggle_active(self):
        sel = self.tree_spuds.selection()
        if not sel:
            return
        vals = self.tree_spuds.item(sel[0])['values']
        spud_id = vals[0]
        current = vals[4]
        new_val = 0 if current == 1 else 1
        self.conn.execute("UPDATE spuds SET active=? WHERE id=?", (new_val, spud_id))
        self.conn.commit()
        self.refresh_spuds()

    def load_spud_into_form(self, event):
        sel = self.tree_spuds.selection()
        if not sel:
            return
        vals = self.tree_spuds.item(sel[0])['values']
        self.ent_name.delete(0, "end");  self.ent_name.insert(0, vals[1])
        self.ent_cat.set(vals[2])
        self.ent_price.delete(0, "end"); self.ent_price.insert(0, vals[3])

    def clear_spud_form(self):
        self.ent_name.delete(0, "end")
        self.ent_cat.set("")
        self.ent_price.delete(0, "end")

    def refresh_spuds(self):
        for row in self.tree_spuds.get_children():
            self.tree_spuds.delete(row)

        cat_filter = self.filter_var.get() if hasattr(self, 'filter_var') else "All"
        if cat_filter == "All":
            rows = self.conn.execute("SELECT id, name, category, price, active FROM spuds").fetchall()
        else:
            rows = self.conn.execute(
                "SELECT id, name, category, price, active FROM spuds WHERE category=?",
                (cat_filter,)).fetchall()

        for r in rows:
            self.tree_spuds.insert("", "end", values=r)

    #TAB 2
    #Braden Clark - order entry and view
    def build_orders_tab(self):
        form = ttk.LabelFrame(self.tab2, text="Place an Order")
        form.pack(fill="x", padx=10, pady=8)

        ttk.Label(form, text="Select Spud:").grid(row=0, column=0, padx=6, pady=4, sticky="e")
        self.order_spud_var = tk.StringVar()
        self.spud_dropdown = ttk.Combobox(form, textvariable=self.order_spud_var, width=24, state="readonly")
        self.spud_dropdown.grid(row=0, column=1, padx=6)
        self.refresh_spud_dropdown()

        ttk.Label(form, text="Quantity:").grid(row=0, column=2, padx=6, sticky="e")
        self.ent_qty = ttk.Entry(form, width=10)
        self.ent_qty.grid(row=0, column=3, padx=6)

        ttk.Button(form, text="Place Order", command=self.place_order).grid(row=0, column=4, padx=10)

#order history
        ttk.Label(self.tab2, text="Order History:").pack(anchor="w", padx=10)
        ocols = ("Order ID", "Spud", "Date", "Qty", "Total")
        self.tree_orders = ttk.Treeview(self.tab2, columns=ocols, show="headings", height=18)
        for c in ocols:
            self.tree_orders.heading(c, text=c)
            self.tree_orders.column(c, width=140)
        self.tree_orders.pack(fill="both", expand=True, padx=10, pady=5)

        self.refresh_orders()

    def refresh_spud_dropdown(self):
        rows = self.conn.execute("SELECT id, name FROM spuds WHERE active=1").fetchall()
        self.spud_id_map = {name: sid for sid, name in rows}
        self.spud_dropdown['values'] = list(self.spud_id_map.keys())

    def place_order(self):
        spud_name = self.order_spud_var.get().strip()
        qty_str = self.ent_qty.get().strip()

        if not spud_name or not qty_str:
            messagebox.showerror("Error", "Select a spud and enter a quantity")
            return

        try:
            qty = int(qty_str)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a whole number")
            return

        spud_id = self.spud_id_map.get(spud_name)
        row = self.conn.execute("SELECT price FROM spuds WHERE id=?", (spud_id,)).fetchone()
        if not row:
            messagebox.showerror("Error", "Could not find that spud")
            return

        total = row[0] * qty
        today = datetime.now().strftime("%Y-%m-%d")
        self.conn.execute("INSERT INTO orders (spud_id, date, quantity, total) VALUES (?, ?, ?, ?)",
                          (spud_id, today, qty, total))
        self.conn.commit()
        self.refresh_orders()
        self.refresh_spud_dropdown()
        messagebox.showinfo("Order placed", f"{spud_name} x{qty} = ${total:.2f}")

    def refresh_orders(self):
        for row in self.tree_orders.get_children():
            self.tree_orders.delete(row)
        q = '''SELECT o.id, s.name, o.date, o.quantity, o.total
               FROM orders o JOIN spuds s ON o.spud_id = s.id
               ORDER BY o.id DESC'''
        for r in self.conn.execute(q).fetchall():
            self.tree_orders.insert("", "end", values=r)

#TAB 3
#Jackson Donald + Andrew Taylor  pandas report
    def build_reports_tab(self):
        top = ttk.Frame(self.tab3)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Button(top, text="Run Report",   command=self.run_report).pack(side="left", padx=4)
        ttk.Button(top, text="Export to CSV", command=self.export_csv).pack(side="left", padx=4)

        self.report_box = tk.Text(self.tab3, height=22, font=("Courier", 10))
        self.report_box.pack(fill="both", expand=True, padx=10, pady=6)

    def run_report(self):
        q = '''SELECT s.name, s.category, o.quantity, o.total
               FROM orders o JOIN spuds s ON o.spud_id = s.id'''
        df = pd.read_sql_query(q, self.conn)
        self.report_df = df

        if df.empty:
            self.report_box.delete("1.0", "end")
            self.report_box.insert("1.0", "No orders yet - place some orders first!")
            return

#summary
        by_cat = df.groupby("category")["total"].sum().reset_index()
        by_cat.columns = ["Category", "Total Revenue"]

        count_by_cat = df.groupby("category")["quantity"].sum().reset_index()
        count_by_cat.columns = ["Category", "Items Sold"]

#numpy
        avg_order = np.mean(df["total"].values)
        std_order = np.std(df["total"].values)
        max_order = np.max(df["total"].values)
        min_order = np.min(df["total"].values)
        total_rev = np.sum(df["total"].values)

        out = "=" * 45 + "\n"
        out += "         CRUD SPUDS BUSINESS REPORT\n"
        out += "=" * 45 + "\n\n"

        out += "Revenue by Category:\n"
        out += "-" * 30 + "\n"
        for _, row in by_cat.iterrows():
            out += f"  {row['Category']:<12}  ${row['Total Revenue']:>8.2f}\n"

        out += "\nItems Sold by Category:\n"
        out += "-" * 30 + "\n"
        for _, row in count_by_cat.iterrows():
            out += f"  {row['Category']:<12}  {int(row['Items Sold']):>4} items\n"

        out += "\n--- NumPy Stats ---\n"
        out += f"  Total Revenue:      ${total_rev:.2f}\n"
        out += f"  Avg Order Value:    ${avg_order:.2f}\n"
        out += f"  Std Dev:            ${std_order:.2f}\n"
        out += f"  Highest Order:      ${max_order:.2f}\n"
        out += f"  Lowest Order:       ${min_order:.2f}\n"

        self.report_box.delete("1.0", "end")
        self.report_box.insert("1.0", out)

    def export_csv(self):
        if not hasattr(self, 'report_df') or self.report_df is None:
            messagebox.showwarning("No data", "Run the repot first")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV files", "*.csv")])
        if path:
            self.report_df.to_csv(path, index=False)
            messagebox.showinfo("Saved", f"CSV exported to:\n{path}")

    def on_close(self):
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    setup_database()
    root = tk.Tk()
    app = SpudsApp(root)
    root.mainloop()
