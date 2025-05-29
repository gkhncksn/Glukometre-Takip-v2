import tkinter as tk
from tkinter import ttk, messagebox
import random
import os

class CowsAndBullsGame:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("ŞİFRE KIRMA OYUNU")

        window_width = 750
        window_height = 500
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}") # Pencereyi ortala
        self.window.resizable(False, False)
        self.window.grab_set()  # Diğer pencerelerle etkileşimi engelle
        
        self.answer = self.generate_answer()
        self.guesses = []
        
        # GUI elemanları
        self.create_widgets()
        self.update_status("Oyun başladı! 4 haneli bir şifremiz var. Şifreyi kırmak için 4 Haneli bir sayı tahmini yapın.")
        
    def generate_answer(self): # Rastgele 4 haneli bir sayı oluştur
        num = random.randint(0, 9999)
        return f"{num:04d}"

    def create_widgets(self):
        # Ana çerçeve
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Başlık
        title_label = ttk.Label(
            main_frame, 
            text="S  I  F  R  E     K  I  R  M  A     O  Y  U  N  U",
            font=("DS-Digital", 30, "bold"),
            foreground="#DF0000",
        )
        title_label.pack(pady=10)
        
        # Talimatlar
        instructions = ttk.Label(
            main_frame,
            text="İpuçları yardımıyla 4 haneli şifreyi kırmaya çalışın",
            font=("Arial", 16),
            justify=tk.CENTER,
            foreground="#34495e"
        )
        instructions.pack(pady=5)
        
        # Tahmin girişi
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=15)
        
        ttk.Label(input_frame, text="Tahmininiz:", font=("Arial", 10)).pack(side=tk.LEFT, padx=(0, 10))
        
        self.guess_entry = ttk.Entry(input_frame, width=10, font=("Arial", 12))
        self.guess_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.guess_entry.focus()
        self.guess_entry.bind("<Return>", self.check_guess)
        
        submit_btn = ttk.Button(
            input_frame, 
            text="Tahmin Et", 
            command=self.check_guess,
            style="Accent.TButton"
        )
        submit_btn.pack(side=tk.LEFT)
        
        # Yeni oyun butonu
        new_game_btn = ttk.Button(
            input_frame, 
            text="Yeni Oyun", 
            command=self.reset_game,
            style="Secondary.TButton"
        )
        new_game_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # Tahmin geçmişi
        history_frame = ttk.Frame(main_frame)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        history_label = ttk.Label(
            history_frame,
            text="Tahmin Geçmişi",
            font=("Arial", 10, "bold"),
            foreground="#2c3e50"
        )
        history_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Listbox ve scrollbar
        scrollbar = ttk.Scrollbar(history_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_listbox = tk.Listbox(
            history_frame,
            height=12,
            width=50,
            font=("Courier New", 10),
            yscrollcommand=scrollbar.set,
            background="#f8f9fa",
            selectbackground="#3498db"
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_listbox.yview)
        
        # Durum bilgisi
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Arial", 9),
            foreground="#7f8c8d",
            anchor=tk.CENTER
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Stil ayarları
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"), foreground="#ffffff", background="#3498db")
        style.configure("Secondary.TButton", font=("Arial", 10), foreground="#ffffff", background="#95a5a6")
        
    def update_status(self, message):
        """Durum çubuğunu günceller"""
        self.status_var.set(message)
        
    def check_guess(self, event=None):
        """Kullanıcının tahminini kontrol eder"""
        guess = self.guess_entry.get().strip()
        
        # Geçerlilik kontrolü
        if not guess.isdigit() or len(guess) != 4:
            messagebox.showerror("Geçersiz Giriş", "Lütfen 4 haneli bir sayı girin!")
            return
            
        # Aynı tahmin kontrolü
        if any(g[0] == guess for g in self.guesses):
            messagebox.showwarning("Tekrar Eden Tahmin", "Bu sayıyı zaten tahmin ettiniz!")
            return
            
        # İnek ve boğa hesaplama
        cows, bulls = self.calculate_cows_bulls(guess)
        self.guesses.append((guess, cows, bulls))
        
        # Listbox'a ekleme
        result = f"Tahmin: {guess}   |   {cows} sayı doğru ve yeri doğru  |   {bulls} sayı doğru ama yeri yanlış"
        self.history_listbox.insert(tk.END, result)
        self.history_listbox.yview(tk.END)  # En sona kaydır
        
        # Oyun durumu güncelleme
        self.update_status(f"Son tahmin: {guess} | Toplam tahmin: {len(self.guesses)}")
        
        # Giriş alanını temizle
        self.guess_entry.delete(0, tk.END)
        
        # Kazanma kontrolü
        if cows == 4:
            self.show_win_message()
            
    def calculate_cows_bulls(self, guess):
        """İnek ve boğa sayılarını hesaplar"""
        cows = 0
        bulls = 0
        
        for i in range(4):
            if guess[i] == self.answer[i]:
                cows += 1
            elif guess[i] in self.answer:
                bulls += 1
                
        return cows, bulls
        
    def show_win_message(self):
        """Kazanma mesajını gösterir"""
        message = f"Tebrikler! {len(self.guesses)} tahminde doğru sonuca ulaştınız!\n\nDoğru cevap: {self.answer}"
        messagebox.showinfo("Oyunu Kazandınız!", message)
        self.reset_game()
            
    def reset_game(self):
        """Oyunu sıfırlar"""
        self.answer = self.generate_answer()
        self.guesses = []
        self.history_listbox.delete(0, tk.END)
        self.guess_entry.delete(0, tk.END)
        self.update_status("Yeni oyun başladı! 4 haneli şifreyi kırmaya çalışın.")
        self.guess_entry.focus()

# Test için kullanım
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = CowsAndBullsGame(root)
    root.mainloop()