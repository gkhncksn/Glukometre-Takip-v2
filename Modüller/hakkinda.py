import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import webbrowser

# Constants
APP_ICON_PATH = "Resources\\app_icon.ico"  # Update with actual icon path

class AboutWindow:
    def __init__(self, master):
        self.master = master
        self.create_window()

    def create_window(self):
        about_win = tk.Toplevel(self.master)
        about_win.title("Hakkında - Glukometre Takip Programı")
        about_win.geometry("500x440")
        about_win.resizable(False, False)
        about_win.transient(self.master)
        about_win.grab_set()

        # Window icon
        try:
            about_win.iconbitmap(APP_ICON_PATH)
        except:
            pass

        # Main frame
        main_frame = ttk.Frame(about_win)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Logo and title
        logo_frame = ttk.Frame(main_frame)
        logo_frame.pack(fill="x", pady=(0, 15))

        try:
            logo_img = Image.open(APP_ICON_PATH)
            logo_img = logo_img.resize((96, 96), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(logo_frame, image=logo_photo)
            logo_label.image = logo_photo  # Keep a reference
            logo_label.pack(side="left", padx=(0, 15))
        except:
            pass

        title_frame = ttk.Frame(logo_frame)
        title_frame.pack(side="left", fill="y")
        ttk.Label(title_frame, text="Glukometre Takip Programı", font=("Cambria", 16, "bold")).pack(anchor="w")
        ttk.Label(title_frame, text="Versiyon 2.1", font=("Cambria", 10)).pack(anchor="w")
        ttk.Label(title_frame, text="© Gökhan ÇOKŞEN", font=("Cambria", 10)).pack(anchor="w")
        ttk.Label(title_frame, text="2025", font=("Cambria", 10)).pack(anchor="w")

        # Info text
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill="both", expand=True)

        info_text = tk.Text(info_frame, wrap="word", height=12, padx=10, pady=10, font=("Tahoma", 10))
        info_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=info_text.yview)
        scrollbar.pack(side="right", fill="y")
        info_text.config(yscrollcommand=scrollbar.set)

        info_content = """
Glukometre Takip Programı, sağlık kuruluşlarında kullanılan glukometre cihazlarının kalite kontrol ve yüzde sapma hesabı ile performans takibini kolaylaştırmak amacıyla geliştirilmiştir.

Öne Çıkan Özellikler:
• Kullanıcı dostu, anlaşılır arayüz
• Kalite kontrol ve yüzde sapma ölçümlerinin kaydı
• Otomatik Veri Yedekleme
• Excel ve Word raporları oluşturma
• Günü Geçen/Yaklaşan Ölçüm Uyarıları

Ek Özellikler:
• Ajandalı Takvim
• Windows Notepad ve Hesap Makinası erişimi
• Dahili IPTV ve M3U oynatıcı
• Dahili İnternet Radyosu
• Dahili Ekran Görünüsü Alma Aracı
• Dahili Excel Dosya Görüntüleme Aracı
• Dahili Dijital Saat
• Zaman Geçirmek için Küçük Oyunlar
• Vücut Kitle İndeksi Hesaplama
• Hava Durumu Bilgisi (to do)
• İnsülin Doz Hesaplama (to do)
• Diyabet Bilgilendirme ve Rehberlik (to do)

Teknik Özellikler:
• Python 3.11 ile geliştirildi
• SQLite veritabanı kullanılıyor
• Modern Tkinter arayüzü

Sistem Gereksinimleri:
• Windows 7/10/11
• Python 3.8+
• 4GB RAM
• 100MB boş disk alanı

Geliştirici: Gökhan ÇOKŞEN
İletişim: g.coksen@gmail.com
Son Güncelleme: 19 Mayıs 2025
"""
        info_text.insert("1.0", info_content)
        info_text.config(state="disabled")  # Read-only

        # Hyperlink
        hyperlink = tk.Label(main_frame, text="GitHub: https://github.com/gkhncksn/Glukometre_Takip", fg="blue", cursor="hand2", font=("Arial", 10, "underline"))
        hyperlink.pack(pady=(10, 0))
        def open_link(event):
            webbrowser.open("https://github.com/biorap/Glukometre_Takip")
        hyperlink.bind("<Button-1>", open_link)

        # Footer
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill="x", pady=(10, 0))
        ttk.Label(footer_frame, text="Yapay Zeka yardımıyla kodlanmış olup, kaynak kodları GitHub'da yayınlanmıştır.", font=("Arial", 8)).pack(side="left")

        # Center the window
        about_win.update_idletasks()
        width = about_win.winfo_width()
        height = about_win.winfo_height()
        x = (about_win.winfo_screenwidth() // 2) - (width // 2)
        y = (about_win.winfo_screenheight() // 2) - (height // 2)
        about_win.geometry(f"{width}x{height}+{x}+{y}")
        about_win.focus_set()
        about_win.wait_window()

def show_about(master):
    """Function to create and show the About window."""
    AboutWindow(master)