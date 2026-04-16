import sqlite3
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

class CRUDSpudsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CRUD Spuds - Enterprise Dashboard")
        self.root.geometry("900x700")
        
        #Initialize Database
        self.conn = sqlite3.connect("crud_spuds_business.db")
        self.cursor = self.conn.cursor()
        self.setup_database()
        
        self.tabs = ttk.Notebook(self.root)
        self.tab_menu = ttk.Frame(self.tabs)
        self.tab_orders = ttk.Frame(self.tabs)
        self.tab_reports = ttk.Frame(self.tabs)
        
        self.tabs.add(self.tab_menu, text="Menu Management (Primary CRUD)")
        self.tabs.add(self.tab_orders, text="Order Entry (Secondary Table)")
        self.tabs.add(self.tab_reports, text="Business Analytics (Pandas/NumPy)")
        self.tabs.pack(expand=1, fill="both")
        
        #Build UI Sections
        self.create_menu_tab()
        self.create_order_tab()
        self.create_report_tab()

    def setup_database(self):
        """Requirement: Two tables with FK and 10+ Seed Records"""
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS spuds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price REAL,
            active INTEGER DEFAULT 1)''')
            
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spud_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            quantity INTEGER,
            total REAL,
            FOREIGN KEY (spud_id) REFERENCES spuds(id))''')
        
        #Seed spud records
        self.cursor.execute("SELECT COUNT(*) FROM spuds")
        if self.cursor.fetchone()[0] == 0:
            spuds_seed = [
                ('The OG Skin On', 'Classic', 5.00), ('Heat Sweat', 'Sweet', 7.50),
                ('Bacon Blaster', 'Loaded', 9.00), ('Truffle Tot', 'Gourmet', 12.00),
                ('Chili Cheese', 'Loaded', 8.50), ('Garlic Herb', 'Classic', 6.00),
                ('Boneless Spud', 'Loaded', 11.00), ('Ukraine tato', 'Classic', 7.00),
                ('Maple Yam', 'Sweet', 6.50), ('Crazy Train', 'Gourmet', 15.00)
            ]
            self.cursor.executemany("INSERT INTO spuds (name, category, price) VALUES (?, ?, ?)", spuds_seed)
            self.conn.commit()

    #TAB 1: MENU MANAGEMENT= Wyatt Graves/ Andrew Tyler
    def create_menu_tab(self):
        frame = ttk.LabelFrame(self.tab_menu, text="Add/Update Spud Menu")
        frame.pack(pady=10, fill="x", padx=10)

        ttk.Label(frame, text="Name:").grid(row=0, column=0)
        self.ent_name = ttk.Entry(frame)
        self.ent_name.grid(row=0, column=1)

        ttk.Label(frame, text="Category:").grid(row=0, column=2)
        self.ent_cat = ttk.Combobox(frame, values=["Classic", "Loaded", "Sweet", "Gourmet"])
        self.ent_cat.grid(row=0, column=3)

        ttk.Label(frame, text="Price:").grid(row=1, column=0)
        self.ent_price = ttk.Entry(frame)
        self.ent_price.grid(row=1, column=1)

        btn_add = ttk.Button(frame, text="Add Spud", command=self.db_add_spud)
        btn_add.grid(row=1, column=2, columnspan=2, sticky="ew")

        # Treeview to display data
        self.tree_spuds = ttk.Treeview(self.tab_menu, columns=("ID", "Name", "Category", "Price"), show='headings')
        for col in ("ID", "Name", "Category", "Price"): self.tree_spuds.heading(col, text=col)
        self.tree_spuds.pack(pady=10, fill="both", expand=True)
        
        btn_del = ttk.Button(self.tab_menu, text="Delete Selected", command=self.db_delete_spud)
        btn_del.pack(side="left", padx=10, pady=5)
        
        self.refresh_spud_list()

    def db_add_spud(self):
        try:
            self.cursor.execute("INSERT INTO spuds (name, category, price) VALUES (?, ?, ?)",
                               (self.ent_name.get(), self.ent_cat.get(), float(self.ent_price.get())))
            self.conn.commit()
            self.refresh_spud_list()
            messagebox.showinfo("Success", "Spud added to the menu!")
        except ValueError:
            messagebox.showerror("Error", "Invalid Price entry.")

    def db_delete_spud(self):
        selected = self.tree_spuds.selection()
        if selected:
            item_id = self.tree_spuds.item(selected)['values'][0]
            self.cursor.execute("DELETE FROM spuds WHERE id=?", (item_id,))
            self.conn.commit()
            self.refresh_spud_list()

    def refresh_spud_list(self):
        for i in self.tree_spuds.get_children(): self.tree_spuds.delete(i)
        self.cursor.execute("SELECT id, name, category, price FROM spuds")
        for row in self.cursor.fetchall(): self.tree_spuds.insert("", "end", values=row)

    #TAB 2: ORDER ENTRY= Braden Clark
    def create_order_tab(self):
        ttk.Label(self.tab_orders, text="Select Spud ID:").pack()
        self.ent_order_id = ttk.Entry(self.tab_orders)
        self.ent_order_id.pack()

        ttk.Label(self.tab_orders, text="Quantity:").pack()
        self.ent_qty = ttk.Entry(self.tab_orders)
        self.ent_qty.pack()

        btn_order = ttk.Button(self.tab_orders, text="Place Order", command=self.db_add_order)
        btn_order.pack(pady=10)

    def db_add_order(self):
        spud_id = self.ent_order_id.get()
        qty = int(self.ent_qty.get())
        self.cursor.execute("SELECT price FROM spuds WHERE id=?", (spud_id,))
        res = self.cursor.fetchone()
        if res:
            total = res[0] * qty
            date = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute("INSERT INTO orders (spud_id, date, quantity, total) VALUES (?, ?, ?, ?)",
                               (spud_id, date, qty, total))
            self.conn.commit()
            messagebox.showinfo("Success", f"Order Processed: ${total:.2f}")

    #TAB 3: ANALYTICS= Jackson Donald/ Andrew Taylor
    def create_report_tab(self):
        btn_run = ttk.Button(self.tab_reports, text="Generate Business Report", command=self.run_pandas_report)
        btn_run.pack(pady=10)
        
        self.report_txt = tk.Text(self.tab_reports, height=15)
        self.report_txt.pack(padx=10, pady=10, fill="both")
        
        btn_csv = ttk.Button(self.tab_reports, text="Export to CSV", command=self.export_csv)
        btn_csv.pack()

    def run_pandas_report(self):
        """Requirement: Pandas read_sql with JOIN and NumPy Stats"""
        query = '''
            SELECT s.name, s.category, o.quantity, o.total 
            FROM orders o 
            JOIN spuds s ON o.spud_id = s.id
        '''
        df = pd.read_sql_query(query, self.conn)
        self.current_df = df
        
        if df.empty:
            self.report_txt.insert("1.0", "No sales data found to analyze.")
            return

        summary = df.groupby('category')['total'].sum()
        
        #NumPy Stats
        avg_sale = np.mean(df['total'])
        max_sale = np.max(df['total'])
        
        report_output = f"--- CATEGORY REVENUE ---\n{summary}\n\n"
        report_output += f"--- NUMPY ANALYTICS ---\n"
        report_output += f"Average Order Value: ${avg_sale:.2f}\n"
        report_output += f"Highest Single Order: ${max_sale:.2f}"
        
        self.report_txt.delete("1.0", "end")
        self.report_txt.insert("1.0", report_output)

    def export_csv(self):
        if hasattr(self, 'current_df'):
            path = filedialog.asksaveasfilename(defaultextension=".csv")
            if path:
                self.current_df.to_csv(path, index=False)
                messagebox.showinfo("Export", "Report Saved Successfully!")

if __name__ == "__main__":
    root = tk.Tk()
    app = CRUDSpudsApp(root)
    root.mainloop()