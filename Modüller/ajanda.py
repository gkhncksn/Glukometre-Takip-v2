# Modüller/ajanda.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkcalendar import DateEntry
import sqlite3
from datetime import date, timedelta, datetime
import os

# --- Constants ---
AGENDA_TABLE_NAME = "ajanda_verileri"
DB_DATE_FORMAT = "%Y-%m-%d"  # ISO 8601 for storing in DB
DISPLAY_DATE_FORMAT = "%d.%m.%Y" # For user display
APP_ICON_PATH_AGENDA = "Resources/calendar.ico" # Optional: Path to an icon for the agenda window

# --- Database Utility Functions ---
def _get_db_connection(db_file_path):
    """Establishes and returns a database connection."""
    try:
        conn = sqlite3.connect(db_file_path)
        return conn
    except sqlite3.Error as e:
        print(f"Ajanda DB bağlantı hatası: {e}")
        messagebox.showerror("Veritabanı Hatası", f"Ajanda veritabanına bağlanılamadı:\n{db_file_path}\n{e}", parent=None) # parent=None if no master window available
        return None

def init_agenda_db(db_file_path):
    """Initializes the agenda table in the database if it doesn't exist."""
    conn = _get_db_connection(db_file_path)
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {AGENDA_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarih TEXT NOT NULL UNIQUE,
                not_icerigi TEXT NOT NULL,
                olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                son_guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Trigger for son_guncelleme_tarihi (Optional, if you want auto-update on change)
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS update_agenda_timestamp
            AFTER UPDATE ON {AGENDA_TABLE_NAME}
            FOR EACH ROW
            BEGIN
                UPDATE {AGENDA_TABLE_NAME}
                SET son_guncelleme_tarihi = CURRENT_TIMESTAMP
                WHERE id = OLD.id;
            END;
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ajanda tablo oluşturma hatası: {e}")
        messagebox.showerror("Veritabanı Hatası", f"Ajanda tablosu oluşturulamadı:\n{e}", parent=None)
    finally:
        if conn:
            conn.close()

def save_or_update_note(db_file_path, note_date_obj, content):
    """Saves a new note or updates an existing one for the given date."""
    conn = _get_db_connection(db_file_path)
    if not conn:
        return False
    date_str = note_date_obj.strftime(DB_DATE_FORMAT)
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT id FROM {AGENDA_TABLE_NAME} WHERE tarih = ?", (date_str,))
        result = cursor.fetchone()
        if result: # Update existing note
            cursor.execute(f"""
                UPDATE {AGENDA_TABLE_NAME} SET not_icerigi = ?, son_guncelleme_tarihi = CURRENT_TIMESTAMP
                WHERE tarih = ?
            """, (content, date_str))
        else: # Insert new note
            cursor.execute(f"""
                INSERT INTO {AGENDA_TABLE_NAME} (tarih, not_icerigi)
                VALUES (?, ?)
            """, (date_str, content))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ajanda not kaydetme/güncelleme hatası: {e}")
        messagebox.showerror("Kayıt Hatası", f"Not kaydedilirken veya güncellenirken hata oluştu:\n{e}")
        return False
    finally:
        if conn:
            conn.close()

def get_note_by_date(db_file_path, note_date_obj):
    """Retrieves the note content for a specific date."""
    conn = _get_db_connection(db_file_path)
    if not conn:
        return None
    date_str = note_date_obj.strftime(DB_DATE_FORMAT)
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT not_icerigi FROM {AGENDA_TABLE_NAME} WHERE tarih = ?", (date_str,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Ajanda not alma hatası: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_dates_with_notes(db_file_path):
    """Retrieves all dates (as date objects) that have notes, sorted chronologically."""
    conn = _get_db_connection(db_file_path)
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT tarih FROM {AGENDA_TABLE_NAME} ORDER BY tarih ASC")
        date_strings = cursor.fetchall()
        return [datetime.strptime(ds[0], DB_DATE_FORMAT).date() for ds in date_strings]
    except sqlite3.Error as e:
        print(f"Ajanda notlu tarihleri alma hatası: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_note_by_date(db_file_path, note_date_obj):
    """Deletes the note for a specific date."""
    conn = _get_db_connection(db_file_path)
    if not conn:
        return False
    date_str = note_date_obj.strftime(DB_DATE_FORMAT)
    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {AGENDA_TABLE_NAME} WHERE tarih = ?", (date_str,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Ajanda not silme hatası: {e}")
        messagebox.showerror("Silme Hatası", f"Not silinirken hata oluştu:\n{e}")
        return False
    finally:
        if conn:
            conn.close()

# --- GUI Class ---
class AgendaWindow(tk.Toplevel):
    def __init__(self, master, db_file_path):
        super().__init__(master)
        self.db_file_path = db_file_path
        self.selected_date_from_listbox = None

        self.title("Kişisel Ajanda")
        self.geometry("750x550")
        try:
            # Attempt to set an icon, assuming the main app's structure for resources
            icon_path = os.path.join(os.path.dirname(os.path.abspath(master.winfo_pathname(master.winfo_id()))), APP_ICON_PATH_AGENDA)
            if os.path.exists(icon_path.replace("\\", "/")):
                 self.iconbitmap(icon_path.replace("\\", "/"))
            else: # Fallback if main script path is tricky or icon is not found
                 if os.path.exists(APP_ICON_PATH_AGENDA.replace("\\", "/")):
                    self.iconbitmap(APP_ICON_PATH_AGENDA.replace("\\", "/"))
        except Exception as e:
            print(f"Ajanda pencere ikonu ayarlanamadı: {e}")


        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill="both", expand=True)

        # Left Pane: Listbox for dates with notes
        left_pane = ttk.LabelFrame(main_frame, text="Kayıtlı Notlar", padding="5")
        left_pane.pack(side="left", fill="y", padx=(0, 10), pady=5)

        self.listbox_dates = tk.Listbox(left_pane, exportselection=False, width=20, height=20)
        self.listbox_dates.pack(side="left", fill="y", expand=True)
        listbox_scrollbar = ttk.Scrollbar(left_pane, orient="vertical", command=self.listbox_dates.yview)
        listbox_scrollbar.pack(side="right", fill="y")
        self.listbox_dates.config(yscrollcommand=listbox_scrollbar.set)
        self.listbox_dates.bind("<<ListboxSelect>>", self._on_listbox_date_selected)

        # Right Pane: Date Entry and Note Content
        right_pane = ttk.Frame(main_frame)
        right_pane.pack(side="right", fill="both", expand=True, pady=5)

        # Date Entry
        date_entry_frame = ttk.Frame(right_pane)
        date_entry_frame.pack(fill="x", pady=(0,10))
        ttk.Label(date_entry_frame, text="Tarih:").pack(side="left", padx=(0,5))
        self.date_entry = DateEntry(date_entry_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2,
                                     date_pattern='dd.mm.yyyy', firstweekday='monday',
                                     showweeknumbers=False)
        self.date_entry.pack(side="left")
        self.date_entry.bind("<<DateEntrySelected>>", self._on_date_entry_selected)

        # Note Content Area
        ttk.Label(right_pane, text="Not İçeriği:").pack(anchor="w", pady=(0,5))
        self.text_note_content = scrolledtext.ScrolledText(right_pane, wrap=tk.WORD, height=15, width=50)
        self.text_note_content.pack(fill="both", expand=True, pady=(0,10))

        # Buttons
        button_frame = ttk.Frame(right_pane)
        button_frame.pack(fill="x")

        self.btn_save = ttk.Button(button_frame, text="Kaydet / Güncelle", command=self._save_current_note)
        self.btn_save.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_delete = ttk.Button(button_frame, text="Notu Sil", command=self._delete_current_note)
        self.btn_delete.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_new = ttk.Button(button_frame, text="Yeni Not Temizle", command=self._clear_fields_for_new_note)
        self.btn_new.pack(side="left", padx=5, expand=True, fill="x")

        self._load_dates_with_notes_into_listbox()
        self._load_note_for_date(self.date_entry.get_date()) # Load note for today or default date

        # Center the window
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        self.transient(master) # Keep on top of master
        self.grab_set() # Modal behavior

    def _load_dates_with_notes_into_listbox(self):
        self.listbox_dates.delete(0, tk.END)
        dates_with_notes = get_dates_with_notes(self.db_file_path)
        for note_date_obj in dates_with_notes:
            self.listbox_dates.insert(tk.END, note_date_obj.strftime(DISPLAY_DATE_FORMAT))

    def _load_note_for_date(self, note_date_obj):
        self.text_note_content.delete("1.0", tk.END)
        note_content = get_note_by_date(self.db_file_path, note_date_obj)
        if note_content:
            self.text_note_content.insert("1.0", note_content)

        # Highlight in listbox if date exists
        date_str_display = note_date_obj.strftime(DISPLAY_DATE_FORMAT)
        listbox_items = self.listbox_dates.get(0, tk.END)
        if date_str_display in listbox_items:
            idx = listbox_items.index(date_str_display)
            self.listbox_dates.selection_clear(0, tk.END)
            self.listbox_dates.selection_set(idx)
            self.listbox_dates.see(idx) # Ensure it's visible
        else:
            self.listbox_dates.selection_clear(0, tk.END) # Clear selection if date not in list

    def _on_date_entry_selected(self, event=None):
        selected_date = self.date_entry.get_date()
        if self.selected_date_from_listbox == selected_date: # Avoid re-triggering if already selected from list
            return
        self.selected_date_from_listbox = None # Reset flag
        self._load_note_for_date(selected_date)


    def _on_listbox_date_selected(self, event=None):
        selection_indices = self.listbox_dates.curselection()
        if not selection_indices:
            return
        selected_item_str = self.listbox_dates.get(selection_indices[0])
        try:
            selected_date_obj = datetime.strptime(selected_item_str, DISPLAY_DATE_FORMAT).date()
            self.selected_date_from_listbox = selected_date_obj # Set flag
            self.date_entry.set_date(selected_date_obj) # This will trigger _on_date_entry_selected if not careful
                                                        # The flag helps prevent double loading.
                                                        # A better way is to directly call load_note_for_date
            self._load_note_for_date(selected_date_obj)

        except ValueError:
            messagebox.showerror("Tarih Hatası", "Listeden geçersiz tarih formatı seçildi.")

    def _save_current_note(self):
        current_date = self.date_entry.get_date()
        content = self.text_note_content.get("1.0", tk.END).strip()

        if not content:
            if get_note_by_date(self.db_file_path, current_date): # If note exists and content cleared, ask to delete
                 if messagebox.askyesno("Not Boş", "Not içeriği boş. Bu tarihe ait notu silmek ister misiniz?", parent=self):
                     self._delete_current_note()
                 return
            else: # No existing note, no content entered
                 messagebox.showinfo("Bilgi", "Kaydedilecek not içeriği bulunmuyor.", parent=self)
                 return


        if save_or_update_note(self.db_file_path, current_date, content):
            messagebox.showinfo("Başarılı", f"{current_date.strftime(DISPLAY_DATE_FORMAT)} tarihli not kaydedildi/güncellendi.", parent=self)
            self._load_dates_with_notes_into_listbox()
             # Re-highlight the current date in listbox after saving
            date_str_display = current_date.strftime(DISPLAY_DATE_FORMAT)
            listbox_items = self.listbox_dates.get(0, tk.END)
            if date_str_display in listbox_items:
                idx = listbox_items.index(date_str_display)
                self.listbox_dates.selection_clear(0, tk.END)
                self.listbox_dates.selection_set(idx)
                self.listbox_dates.see(idx)
        else:
            messagebox.showerror("Hata", "Not kaydedilirken bir sorun oluştu.", parent=self)

    def _delete_current_note(self):
        current_date = self.date_entry.get_date()
        note_exists = get_note_by_date(self.db_file_path, current_date)

        if not note_exists:
            messagebox.showinfo("Bilgi", "Bu tarihe ait silinecek bir not bulunmuyor.", parent=self)
            return

        if messagebox.askyesno("Not Silme Onayı",
                               f"{current_date.strftime(DISPLAY_DATE_FORMAT)} tarihli notu silmek istediğinize emin misiniz?",
                               parent=self):
            if delete_note_by_date(self.db_file_path, current_date):
                messagebox.showinfo("Başarılı", "Not silindi.", parent=self)
                self.text_note_content.delete("1.0", tk.END)
                self._load_dates_with_notes_into_listbox()
                 # Clear selection or select today after deletion
                self.listbox_dates.selection_clear(0, tk.END)
                # self.date_entry.set_date(date.today()) # Optionally reset to today
                # self._load_note_for_date(self.date_entry.get_date())
            else:
                messagebox.showerror("Hata", "Not silinirken bir sorun oluştu.", parent=self)

    def _clear_fields_for_new_note(self):
        self.date_entry.set_date(date.today()) # Reset to today's date
        self.text_note_content.delete("1.0", tk.END)
        self.listbox_dates.selection_clear(0, tk.END) # Clear selection in listbox
        self.selected_date_from_listbox = None # Reset flag
        self.text_note_content.focus_set()


# --- Public Interface Functions (called by the main application) ---

def show_agenda_ui(master_root, db_file_path):
    """Creates and shows the main agenda window."""
    init_agenda_db(db_file_path) # Ensure DB and table are ready
    agenda_win = AgendaWindow(master_root, db_file_path)
    # The grab_set in AgendaWindow constructor handles modality

def show_startup_alerts(master_root, db_file_path):
    """Checks for notes for today and tomorrow and shows an alert if any are found."""
    # No need to call init_agenda_db here if main app calls it once at startup.
    # However, to be safe, or if this function could be called independently:
    # init_agenda_db(db_file_path)

    today = date.today()
    tomorrow = today + timedelta(days=1)
    alerts_found = []

    note_today_content = get_note_by_date(db_file_path, today)
    if note_today_content:
        preview = note_today_content[:100] + ("..." if len(note_today_content) > 100 else "")
        alerts_found.append(f"Bugün ({today.strftime(DISPLAY_DATE_FORMAT)}):\n{preview}")

    note_tomorrow_content = get_note_by_date(db_file_path, tomorrow)
    if note_tomorrow_content:
        preview = note_tomorrow_content[:100] + ("..." if len(note_tomorrow_content) > 100 else "")
        alerts_found.append(f"Yarın ({tomorrow.strftime(DISPLAY_DATE_FORMAT)}):\n{preview}")

    if alerts_found:
        alert_message = "🗓️ Ajanda Hatırlatmaları 🗓️\n\n" + "\n\n".join(alerts_found)
        messagebox.showinfo("Ajanda Bildirimi", alert_message, parent=master_root)

# Example of how to test this module independently (optional)
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Ana Test Penceresi")
    root.geometry("300x200")

    # Create a dummy DB file for testing
    TEST_DB = "ajanda_test.db"
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    init_agenda_db(TEST_DB) # Initialize

    # Add some test data
    save_or_update_note(TEST_DB, date.today(), "Bugünün testi: Ana görevleri tamamla.")
    save_or_update_note(TEST_DB, date.today() + timedelta(days=1), "Yarının testi: Proje sunumu hazırla.")
    save_or_update_note(TEST_DB, date.today() + timedelta(days=5), "5 gün sonra: Tatil planı yap.")


    ttk.Button(root, text="Ajandayı Aç", command=lambda: show_agenda_ui(root, TEST_DB)).pack(pady=20)
    ttk.Button(root, text="Başlangıç Uyarılarını Göster", command=lambda: show_startup_alerts(root, TEST_DB)).pack(pady=10)

    # Show startup alerts on launch for testing
    # show_startup_alerts(root, TEST_DB) # This will show alerts immediately

    root.mainloop()
    # Clean up dummy DB
    # if os.path.exists(TEST_DB):
    #    os.remove(TEST_DB)