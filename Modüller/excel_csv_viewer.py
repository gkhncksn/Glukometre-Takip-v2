import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import openpyxl
import os

class ExcelCSVViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("Excel / CSV Görüntüleyici")
        self.master.geometry("800x500")
        self.master.resizable(True, True)

        self.tree = ttk.Treeview(self.master)
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        btn_frame = ttk.Frame(self.master)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text="Dosya Aç", command=self.open_file).pack()

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel veya CSV", "*.csv *.xlsx")])
        if not file_path:
            return

        try:
            data = []
            if file_path.endswith(".csv"):
                with open(file_path, newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    data = list(reader)
            elif file_path.endswith(".xlsx"):
                wb = openpyxl.load_workbook(file_path)
                ws = wb.active
                data = [[cell.value for cell in row] for row in ws.iter_rows()]

            if not data:
                messagebox.showwarning("Uyarı", "Dosya boş.")
                return

            # Treeview sıfırla
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = list(range(len(data[0])))
            self.tree["show"] = "headings"
            for i, col in enumerate(data[0]):
                self.tree.heading(i, text=str(col))
                self.tree.column(i, anchor="center", width=100)
            for row in data[1:]:
                self.tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Hata", f"Dosya açılamadı:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ExcelCSVViewer(root)
    root.mainloop()
