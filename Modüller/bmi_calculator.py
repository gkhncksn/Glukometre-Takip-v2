import tkinter as tk
from tkinter import ttk, messagebox

def open_bmi_calculation_dialog():
    dialog = tk.Tk()
    dialog.title("Vücut Kitle İndeksi Hesaplama")
    dialog.geometry("300x170")
    dialog.resizable(False, False)

    ttk.Label(dialog, text="Kilonuzu Giriniz (Kg):").pack(pady=5)
    weight_entry = ttk.Entry(dialog)
    weight_entry.pack(pady=5)

    ttk.Label(dialog, text="Boyunuzu Giriniz (Cm):").pack(pady=5)
    height_entry = ttk.Entry(dialog)
    height_entry.pack(pady=5)
    dialog.focus_set()
    weight_entry.focus_set()

    def calculate_bmi():
        try:
            kilo = float(weight_entry.get())
            boy = float(height_entry.get())
            if kilo <= 0 or boy <= 0:
                messagebox.showerror("Hata", "Kilo ve boy pozitif değerler olmalıdır!", parent=dialog)
                return
            vki = kilo / ((boy / 100) ** 2)
            durum = ""
            if vki < 18.5:
                durum = "Zayıf"
            elif 18.5 <= vki < 24.9:
                durum = "Normal"
            elif 25 <= vki < 29.9:
                durum = "Fazla Kilolu"
            elif 30 <= vki < 34.9:
                durum = "Obez (Sınıf 1)"
            elif 35 <= vki < 39.9:
                durum = "Obez (Sınıf 2)"
            else:
                durum = "Aşırı Obez (Sınıf 3)"
            messagebox.showinfo("Vücut Kitle İndeksi", f"Vücut Kitle İndeksiniz: {vki:.2f}\nMevcut Durumunuz: {durum}", parent=dialog)
        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin!", parent=dialog)

    ttk.Button(dialog, text="Hesapla", command=calculate_bmi).pack(pady=10)

    # Pencereyi ekranın ortasına al
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{x}+{y}")

    dialog.mainloop()

if __name__ == "__main__":
    open_bmi_calculation_dialog()
