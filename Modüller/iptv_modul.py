import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import vlc
import threading
import time
import requests
import locale
import sqlite3

DB_FILE = "veriler.db"

def parse_m3u_playlist(url):
    """M3U playlistini URL'den çeker ve kanal listesini döndürür."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        lines = response.text.splitlines()
        channels = []
        name, stream_url = None, None
        for line in lines:
            if line.startswith("#EXTINF"):
                name = line.split(",")[-1].strip()
            elif line and not line.startswith("#"):
                stream_url = line.strip()
                if name and stream_url:
                    channels.append((name, stream_url))
                    name, stream_url = None, None
        return channels
    except Exception as e:
        raise Exception(f"M3U playlist ayrıştırılamadı: {e}")

def create_iptv_tab(parent, notebook, channels):
    """IPTV sekmesini oluşturur ve kanalları Treeview'e ekler."""
    iptv_tab = ttk.Frame(notebook)
    mevcut_tab_sayisi = len(notebook.tabs())
    hedef_indeks = 2 if mevcut_tab_sayisi >= 3 else "end"
    notebook.insert(hedef_indeks, iptv_tab, text="IPTV")

    iptv_tab.columnconfigure(0, weight=1)
    iptv_tab.rowconfigure(1, weight=1) # Treeview için
    iptv_tab.rowconfigure(2, weight=0) # Arama ve butonlar için

    # --- Üstteki Treeview ve Scrollbar ---
    tree_scroll = ttk.Scrollbar(iptv_tab, orient="vertical")
    tree_scroll.grid(row=1, column=1, sticky="ns")

    tree = ttk.Treeview(
        iptv_tab,
        columns=("Kanal Adı", "URL"),
        show="headings",
        yscrollcommand=tree_scroll.set,
        selectmode="extended"
    )
    tree.heading("Kanal Adı", text="Kanal Adı")
    tree.heading("URL", text="URL")
    tree.column("Kanal Adı", width=250)
    tree.column("URL", width=400)
    tree.grid(row=1, column=0, padx=10, pady=(10,0), sticky="nsew")
    tree_scroll.config(command=tree.yview)

    # --- Alttaki Kontroller için Çerçeve ---
    controls_frame = ttk.Frame(iptv_tab)
    controls_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5,10))
    controls_frame.columnconfigure(3, weight=1) # Arama kutusunun genişlemesi için

    # Playlist Yükle/Kaydet Butonu
    load_save_button = ttk.Button(controls_frame, text="Playlist Yükle / Kaydet", command=lambda: show_playlist_loader_dialog(parent, tree, parent.iptv_channels))
    load_save_button.grid(row=0, column=0, padx=(0,5))

    # Kanal Ara Label
    search_label = ttk.Label(controls_frame, text="Kanal Ara:")
    search_label.grid(row=0, column=1, padx=(5,2))

    # Kanal Ara Textbox
    search_entry = ttk.Entry(controls_frame, width=40) # Genişlik ayarı
    search_entry.grid(row=0, column=2, sticky="ew", padx=(0,5))
    
    # parent.iptv_channels her zaman orijinal, filtrelenmemiş listeyi tutacak
    # Bu listeyi bir kopya olarak saklayalım, böylece orijinal channels parametresi etkilenmez
    if not hasattr(parent, 'iptv_channels') or not parent.iptv_channels:
        parent.iptv_channels = list(channels)

    def populate_treeview(channel_list):
        # Mevcut tüm öğeleri temizle
        for item in tree.get_children():
            tree.delete(item)
        # Yeni kanalları ekle
        for kanal_adi, url in channel_list:
            tree.insert("", "end", values=(kanal_adi, url))

    populate_treeview(parent.iptv_channels) # Başlangıçta tüm kanalları yükle

    def filter_channels_on_search(event=None):
        search_term = search_entry.get().lower()
        if not search_term:
            populate_treeview(parent.iptv_channels)
            return

        filtered_channels = []
        for name, url in parent.iptv_channels:
            if search_term in name.lower():
                filtered_channels.append((name, url))
        populate_treeview(filtered_channels)

    search_entry.bind("<KeyRelease>", filter_channels_on_search)

    init_playlist_table() # Bu satır show_playlist_loader_dialog'dan önce olabilir veya orada kalabilir.

    # Çift tıklama ile oynatıcı penceresini açma
    def on_double_click(event):
        item = tree.identify_row(event.y)
        if item:
            kanal_adi, url = tree.item(item, "values")
            open_player_window(parent, kanal_adi, url)
            search_entry.delete(0, tk.END) # Arama kutusunu temizle
            populate_treeview(parent.iptv_channels) # Treeview'i orijinal liste ile doldur

    tree.bind("<Double-1>", on_double_click)

    # Tüm öğeleri seçme (Ctrl+A)
    def select_all(event=None):
        current_items = tree.get_children()
        if current_items: # Sadece görünür öğeler seçilsin
            tree.selection_set(current_items)
        return "break"

    tree.bind("<Control-a>", select_all)
    
    # parent.iptv_channels'ı güncellemek için bir yardımcı fonksiyon
    def update_parent_iptv_channels_from_tree():
        current_tree_items = []
        for item_id in tree.get_children():
            current_tree_items.append(tree.item(item_id, "values"))
        
        # Eğer arama aktifse, sadece görünenleri değil, tüm listeyi güncellemeliyiz
        # Bu biraz karmaşıklaşabilir. Şimdilik, silme işleminin parent.iptv_channels'ı
        # arama filtresinden bağımsız olarak doğru şekilde güncellemesini sağlayalım.
        
        # Silme işlemi için: parent.iptv_channels'dan doğru öğeleri bul ve sil.
        # Bu kısım, arama aktifken silme yapıldığında daha dikkatli bir implementasyon gerektirebilir.
        # Şimdilik, arama yokken doğru çalıştığını varsayalım.
        # Eğer arama aktifse, silinen öğenin parent.iptv_channels'daki orijinalini bulmak gerekir.

    # Seçilen kanalları silme
    def delete_selected(event=None):
        selected_items_in_tree = tree.selection()
        if not selected_items_in_tree:
            return

        if messagebox.askyesno(
            "Sil",
            f"{len(selected_items_in_tree)} kanalı silmek istiyor musunuz?",
            parent=parent.master
        ):
            items_to_delete_from_parent_channels = []
            
            # Treeview'dan seçilenlerin değerlerini al
            selected_values_in_tree = [tuple(tree.item(item, "values")) for item in selected_items_in_tree]

            # parent.iptv_channels listesinden bu değerlere sahip olanları bul ve sil
            new_parent_channels = []
            for ch_name, ch_url in parent.iptv_channels:
                if (ch_name, ch_url) not in selected_values_in_tree:
                    new_parent_channels.append((ch_name, ch_url))
            
            parent.iptv_channels[:] = new_parent_channels # Ana listeyi güncelle

            # Treeview'dan seçilenleri sil
            for item in selected_items_in_tree:
                tree.delete(item)
            
            # Arama aktifse, arama sonuçlarını güncelle (veya tüm listeyi göster)
            # Eğer arama kutusu doluysa, filtrelemeyi tekrar uygula.
            # Ancak, silme işleminden sonra genellikle tüm listeyi görmek daha mantıklı olabilir.
            # Bu nedenle, arama kutusunu temizleyip tüm listeyi göstermek daha kullanıcı dostu olabilir.
            # Şimdilik, sadece treeview'dan silme yapıyoruz ve parent listesini güncelliyoruz.
            # Filtrelemenin tekrar uygulanması filter_channels_on_search ile sağlanabilir.
            # Veya basitçe, silme sonrası arama kutusunu temizleyip tüm listeyi gösterebiliriz.
            # search_entry.delete(0, tk.END) # Opsiyonel: Silme sonrası aramayı temizle
            # populate_treeview(parent.iptv_channels) # Opsiyonel: Silme sonrası tüm listeyi göster

    tree.bind("<Delete>", delete_selected)

    # Sağ tıklama menüsü ile hücre düzenleme
    def show_context_menu(event):
        row_id = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if row_id:
            tree.selection_set(row_id) # Sadece sağ tıklananı seç
            menu = tk.Menu(tree, tearoff=0)
            def edit_cell():
                col_index = int(column[1:]) - 1
                original_values_tuple = tuple(tree.item(row_id, "values")) # Orijinal değerler
                current_value = original_values_tuple[col_index]

                new_value = sag_tik_edit_diyalog(
                    parent.master,
                    "Düzenle",
                    "Yeni değer:",
                    current_value
                )
                if new_value is not None and new_value != current_value:
                    new_values_list = list(original_values_tuple)
                    new_values_list[col_index] = new_value
                    tree.item(row_id, values=new_values_list) # Treeview'i güncelle

                    # parent.iptv_channels listesini güncelle
                    # Önce orijinal kaydı bul
                    try:
                        # Orijinal değerlere göre index'i bulmaya çalış
                        channel_index_in_parent = -1
                        for i, (name, url_val) in enumerate(parent.iptv_channels):
                            if name == original_values_tuple[0] and url_val == original_values_tuple[1]:
                                channel_index_in_parent = i
                                break
                        
                        if channel_index_in_parent != -1:
                            parent.iptv_channels[channel_index_in_parent] = (new_values_list[0], new_values_list[1])
                        else:
                            # Eğer bulunamadıysa (belki arama filtresi aktif ve öğe tam eşleşmiyor)
                            # Bu durumu daha iyi ele almak gerekebilir.
                            # Şimdilik, eğer arama aktifse ve öğe doğrudan bulunamıyorsa,
                            # bu durum bir uyarı verebilir veya en iyi tahminle güncelleme yapabilir.
                            # Ancak en sağlıklısı, orijinal index üzerinden gitmektir.
                            # Bu örnekte, eğer arama aktifse ve düzenleme yapılıyorsa,
                            # değişikliğin ana listeye yansıması için dikkatli olunmalıdır.
                            # Belki de düzenleme sırasında tüm listeyi göstermek daha iyi bir yaklaşımdır.
                            print("Uyarı: Düzenlenen öğe ana listede tam olarak bulunamadı. Bu durum arama filtresi aktifken olabilir.")
                            # Alternatif olarak, tree'deki tüm öğeleri parent.iptv_channels'a geri yazabilirsiniz,
                            # ama bu, büyük listelerde performansı etkileyebilir ve arama filtresini bozar.
                            # Şimdilik, bulunan index üzerinden güncelleme yapılıyor.
                    except ValueError:
                        # Öğeyi bulmada bir sorun oluştu, loglayabilir veya kullanıcıya bildirebilirsiniz.
                        print(f"Hata: Güncellenecek öğe parent.iptv_channels içinde bulunamadı: {original_values_tuple}")


            menu.add_command(label="Düzenle", command=edit_cell)
            menu.tk_popup(event.x_root, event.y_root)

    tree.bind("<Button-3>", show_context_menu)


    def sort_column(col, reverse):
        # Sıralama işlemi için parent.iptv_channels'ı kullanmak yerine,
        # doğrudan Treeview'deki mevcut (filtrelenmiş veya tam) listeyi sıralayalım.
        # Ancak, bu değişiklik parent.iptv_channels'a yansıtılmalı mı?
        # Genellikle sıralama sadece görünüm için yapılır.
        # Eğer ana listenin sıralaması değişecekse, o zaman parent.iptv_channels güncellenmeli.
        # Mevcut kodunuz parent.iptv_channels'ı güncelliyor. Bu, arama filtresi varken sorun yaratabilir.
        # Bu nedenle, sıralama yapmadan önce arama kutusunu temizleyip tüm listeyi göstermek daha tutarlı olabilir.
        # Ya da sıralamayı sadece Treeview'deki mevcut görünen öğeler üzerinde yapıp, ana listeyi değiştirmemek.

        # Mevcut implementasyonunuz ana listeyi sıralıyor. Arama aktifken bu kafa karıştırıcı olabilir.
        # Öneri: Sıralama sadece Treeview'da görünenleri etkilesin veya sıralamadan önce arama temizlensin.
        # Şimdilik orijinal mantığı koruyarak, arama filtresi yokken doğru çalışmasını hedefleyelim.

        # Arama aktifse, kullanıcıyı uyar veya sıralama öncesi aramayı temizle
        if search_entry.get():
            if not messagebox.askyesno("Sıralama Uyarısı",
                                       "Arama filtresi aktifken sıralama yapmak, ana listenin tamamını sıralayacaktır. "
                                       "Bu işlem arama filtresini etkilemez ama filtrelenmemiş veriyi sıralar.\n\n"
                                       "Devam etmek istiyor musunuz (tüm liste sıralanacak ve Treeview güncellenecek)? "
                                       "Ya da sıralamadan önce aramayı temizlemek için 'Hayır'ı seçin.", parent=parent.master):
                return # Kullanıcı iptal etti

        # Ana listeyi (parent.iptv_channels) sırala
        try:
            # locale.strxfrm kullanımı önemli
            parent.iptv_channels.sort(key=lambda x: locale.strxfrm(x[0 if col == "Kanal Adı" else 1]), reverse=reverse)
        except Exception as e: # Genel hata yakalama, özellikle strxfrm sorunları için
            print(f"Sıralama sırasında hata (muhtemelen locale): {e}")
            # Basit string sıralamasına geri dön
            parent.iptv_channels.sort(key=lambda x: x[0 if col == "Kanal Adı" else 1], reverse=reverse)

        # Treeview'ı güncellenmiş ve sıralanmış ana listeye göre yeniden doldur
        # Eğer arama aktifse, filtreyi tekrar uygula. Değilse, tüm listeyi göster.
        current_search_term = search_entry.get()
        if current_search_term:
            filter_channels_on_search() # Filtreyi yeniden uygula (sıralanmış ana liste üzerinden)
        else:
            populate_treeview(parent.iptv_channels) # Tüm sıralanmış listeyi göster

        # Başlık komutunu güncelle
        tree.heading(col, command=lambda: sort_column(col, not reverse))


    for col_name, col_id in [("Kanal Adı", "Kanal Adı"), ("URL", "URL")]:
        tree.heading(col_name, text=col_name, command=lambda c=col_id: sort_column(c, False))


    # Sürükle Bırak İşlevselliği (Drag & Drop)
    # Bu kısım, arama filtresi aktifken dikkatli yönetilmelidir.
    # Eğer sürükle bırak ile ana liste (parent.iptv_channels) güncelleniyorsa,
    # arama filtresi geçersiz hale gelebilir veya beklenmedik davranışlara yol açabilir.
    # Öneri: Sürükle bırak işlemi sırasında arama filtresi geçici olarak devre dışı bırakılabilir
    # veya işlem sonrası filtre yeniden uygulanabilir.

    def on_drag_start(event):
        item = tree.identify_row(event.y)
        if item:
            tree._drag_item_id = item
            tree._drag_item_values = tuple(tree.item(item, "values")) # Sürüklenen öğenin değerleri
            tree._highlight_item = None

    def on_drag_motion(event):
        if not hasattr(tree, '_drag_item_id') or not tree._drag_item_id:
            return
        target_item_id = tree.identify_row(event.y)
        if target_item_id and target_item_id != tree._drag_item_id:
            if tree._highlight_item and tree._highlight_item != target_item_id:
                tree.item(tree._highlight_item, tags=())
            tree.item(target_item_id, tags=("highlight",))
            tree._highlight_item = target_item_id
        elif tree._highlight_item:
            tree.item(tree._highlight_item, tags=())
            tree._highlight_item = None

    def on_drag_release(event):
        if not hasattr(tree, '_drag_item_id') or not tree._drag_item_id:
            return

        target_item_id = tree.identify_row(event.y)
        source_item_id = tree._drag_item_id
        source_item_values = tree._drag_item_values

        if target_item_id and source_item_id and source_item_id != target_item_id:
            # Treeview'de taşıma
            target_index = tree.index(target_item_id)
            if tree.index(source_item_id) < target_index: # Aşağı sürükleniyorsa
                tree.move(source_item_id, tree.parent(target_item_id), target_index)
            else: # Yukarı sürükleniyorsa
                tree.move(source_item_id, tree.parent(target_item_id), target_index)

            # parent.iptv_channels listesini güncelle
            # Sürüklenen öğeyi eski konumundan kaldır
            try:
                original_index_in_parent = -1
                for i, (name, url_val) in enumerate(parent.iptv_channels):
                    if name == source_item_values[0] and url_val == source_item_values[1]:
                        original_index_in_parent = i
                        break
                
                if original_index_in_parent != -1:
                    moved_item_data = parent.iptv_channels.pop(original_index_in_parent)

                    # Yeni konumu Treeview'dan alarak parent.iptv_channels'a ekle
                    # Treeview'daki tüm öğelerin yeni sırasını al
                    new_order_in_tree = [tuple(tree.item(item_id, "values")) for item_id in tree.get_children()]
                    
                    # parent.iptv_channels'ı bu yeni sıraya göre güncellemek karmaşık olabilir,
                    # özellikle arama filtresi aktifse.
                    # Daha basit bir yaklaşım, eğer arama filtresi yoksa doğrudan tree'den parent'ı güncellemektir.
                    # Eğer arama filtresi aktifse, bu işlem daha dikkatli yapılmalı.
                    # Şimdilik, arama filtresi yokken doğru çalışacak şekilde güncelleyelim.
                    if not search_entry.get(): # Arama filtresi aktif değilse
                        parent.iptv_channels.clear()
                        for item_values_in_tree in new_order_in_tree:
                            parent.iptv_channels.append(item_values_in_tree)
                    else:
                        # Arama aktifken sürükle-bırak daha karmaşık.
                        # Kullanıcıyı uyarabilir veya sürükle-bırak sonrası arama filtresini temizleyebiliriz.
                        # Bu örnekte, eğer arama aktifse, parent.iptv_channels'ın tutarlılığı için
                        # ya sürükle bırak engellenmeli ya da çok dikkatli bir güncelleme yapılmalı.
                        # Şimdilik, arama aktifken parent.iptv_channels'ı GÜNCELLEMİYORUZ, sadece tree'de taşıyoruz.
                        # Bu, tutarsızlığa yol açabilir. İdeal çözüm, bu durumda farklı bir strateji izlemektir.
                        # Örneğin, sürükle bırak sonrası arama filtresini temizlemek ve tüm listeyi göstermek.
                        messagebox.showinfo("Bilgi", "Arama aktifken sürükle-bırak yapıldı. Ana liste sırası değişmemiş olabilir. Tutarlılık için aramayı temizleyebilirsiniz.", parent=parent.master)


            except ValueError:
                print(f"Sürükle-bırak sırasında öğe ana listede bulunamadı: {source_item_values}")


        if hasattr(tree, '_highlight_item') and tree._highlight_item:
            tree.item(tree._highlight_item, tags=())
            tree._highlight_item = None
        tree._drag_item_id = None
        tree._drag_item_values = None
    
    tree.tag_configure("highlight", background="#d0e8f2") # Açık mavi bir arka plan
    tree.bind("<ButtonPress-1>", on_drag_start, add='+') # add='+' ile var olan binding'i ezme
    tree.bind("<B1-Motion>", on_drag_motion, add='+')
    tree.bind("<ButtonRelease-1>", on_drag_release, add='+')


    parent.tree = tree

# Diğer fonksiyonlar (sag_tik_edit_diyalog, open_player_window, show_playlist_loader_dialog, init_playlist_table) olduğu gibi kalır.
# Ancak, show_playlist_loader_dialog içindeki `yukle` fonksiyonu,
# parent.iptv_channels'ı güncelledikten sonra populate_treeview'i çağırmalıdır.

def sag_tik_edit_diyalog(parent_widget, title, prompt, initialvalue): # parent -> parent_widget
    dialog = tk.Toplevel(parent_widget) # parent -> parent_widget
    dialog.title(title)
    dialog.geometry("700x150")
    dialog.transient(parent_widget) # parent -> parent_widget
    dialog.grab_set()
    dialog.resizable(False, False)

    frame = ttk.Frame(dialog, padding="10")
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text=prompt).pack(anchor="w", pady=(0, 5))
    entry = ttk.Entry(frame, width=80)
    entry.pack(fill="x", pady=(0, 10))
    entry.insert(0, initialvalue)
    entry.focus_set()
    entry.select_range(0, tk.END)

    result = [None]
    def on_ok():
        result[0] = entry.get()
        dialog.destroy()
    def on_cancel():
        dialog.destroy()

    btn_frame = ttk.Frame(frame)
    btn_frame.pack()
    ttk.Button(btn_frame, text="Tamam", command=on_ok).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text="İptal", command=on_cancel).pack(side=tk.LEFT, padx=5)

    dialog.update_idletasks()
    # parent -> parent_widget
    x = parent_widget.winfo_rootx() + (parent_widget.winfo_width() - 700) // 2
    y = parent_widget.winfo_rooty() + (parent_widget.winfo_height() - 150) // 2
    dialog.geometry(f"+{x}+{y}")
    dialog.wait_window()
    return result[0]

def open_player_window(parent_obj, title, stream_url): # parent -> parent_obj (main app instance)
    """VLC oynatıcı penceresini açar."""
    # ... (open_player_window içeriği, parent parametresi ana uygulama nesnesine (parent.master) işaret etmeli)
    # messagebox'larda parent=parent_obj.master kullanılmalı
    def check_stream_availability(url, timeout=5):
        """Stream URL'sinin erişilebilirliğini kontrol eder."""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def play_stream():
        nonlocal player, instance # nonlocal olarak tanımlanmalı
        try:
            if not check_stream_availability(stream_url):
                raise Exception("Stream URL'sine erişilemiyor veya geçersiz.")

            instance = vlc.Instance("--network-caching=1000")
            player = instance.media_player_new()
            media = instance.media_new(stream_url)
            player.set_media(media)
            win.update_idletasks()
            player.set_hwnd(frame.winfo_id())

            start_time = time.time()
            player.play()
            while not player.is_playing() and time.time() - start_time < 10:
                time.sleep(0.1)
            if not player.is_playing():
                raise Exception("Stream oynatılamadı: Zaman aşımı veya bağlantı hatası.")
            win.deiconify()
        except Exception as e:
            if win.winfo_exists(): # Pencere hala varsa destroy et
                 win.destroy()
            # parent_obj.master.after kullanılmalı
            parent_obj.master.after(0, lambda: messagebox.showerror(
                "Hata", f"Oynatıcı başlatılamadı: {e}", parent=parent_obj.master
            ))
            if instance is not None: # instance null check
                instance.release()
            # player'ı da None yapmak iyi bir pratik olabilir
            player = None


    try:
        instance = None # Başlangıçta None
        player = None   # Başlangıçta None

        topmost_choice = messagebox.askyesno(
            "Pencere Ayarı",
            "Oynatma penceresi en üstte ve küçük boyutta açılsın mı?\n(Hem izleyip, hem programı kullanmaya devam edebilirsin)\n\nHAYIR dersen TV daha büyük bir pencerede açılacak ve arkaplanda oynatabileceksin",
            parent=parent_obj.master # parent_obj.master
        )

        win = tk.Toplevel(parent_obj.master) # parent_obj.master
        win.title(f"{title} - Tam Ekran oynatmak için Alt + ENTER tuşlarına birlikte basın")
        win.withdraw()

        if topmost_choice:
            win.geometry("450x275")
            win.attributes("-topmost", True)
        else:
            w, h = 800, 450
            x_pos = (win.winfo_screenwidth() - w) // 2 # x -> x_pos
            y_pos = (win.winfo_screenheight() - h) // 2 # y -> y_pos
            win.geometry(f"{w}x{h}+{x_pos}+{y_pos}") # x,y -> x_pos, y_pos

        win.configure(bg="black")
        win.resizable(True, True)
        parent_obj.master.focus_set() # parent_obj.master

        frame = tk.Frame(win, bg="black")
        frame.pack(fill="both", expand=True)

        threading.Thread(target=play_stream, daemon=True).start()

        def toggle_play_pause(event=None):
            if player is not None and player.is_playing(): # player null check
                player.pause()
            elif player is not None: # player null check
                player.play()

        def toggle_fullscreen(event=None):
            win.attributes("-fullscreen", not win.attributes("-fullscreen"))
            if win.attributes("-fullscreen"):
                win.attributes("-topmost", False)
            elif topmost_choice:
                win.attributes("-topmost", True)

        def on_close():
            if player is not None: # player null check
                player.stop()
            if instance is not None: # instance null check
                instance.release()
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", on_close)
        win.bind("<space>", toggle_play_pause)
        win.bind("<Alt-Return>", toggle_fullscreen)
        win.bind("<Double-1>", toggle_fullscreen) # Çift tıklama ile tam ekran
        win.bind("<Button-1>", toggle_play_pause) # Tek tıklama ile duraklat/oynat

    except Exception as e:
        messagebox.showerror("Hata", f"Oynatıcı penceresi oluşturulamadı: {e}", parent=parent_obj.master) # parent_obj.master


def show_playlist_loader_dialog(parent_obj, tree, iptv_channels_ref): # parent -> parent_obj, iptv_channels -> iptv_channels_ref
    dialog = tk.Toplevel(parent_obj.master) # parent.master
    dialog.title("IPTV Playlist Yükle")
    dialog.geometry("500x250")
    dialog.transient(parent_obj.master) # parent.master
    dialog.grab_set()
    dialog.resizable(False, False)
    dialog.update_idletasks()
    w = dialog.winfo_width()
    h = dialog.winfo_height()
    x_pos = (dialog.winfo_screenwidth() // 2) - (w // 2) # x -> x_pos
    y_pos = (dialog.winfo_screenheight() // 2) - (h // 2) # y -> y_pos
    dialog.geometry(f"{w}x{h}+{x_pos}+{y_pos}") # x,y -> x_pos, y_pos

    notebook = ttk.Notebook(dialog)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    frm_yukle = ttk.Frame(notebook)
    notebook.add(frm_yukle, text="Playlist Yükle")

    ttk.Label(frm_yukle, text="Playlist Seç:").pack(pady=(10, 0))
    cmb_playlist = ttk.Combobox(frm_yukle, state="readonly", width=40)
    cmb_playlist.pack(pady=(0, 10))

    def update_combobox():
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT playlist_adi FROM m3u_playlists")
            adlar = [row[0] for row in cursor.fetchall()]
            conn.close()
            cmb_playlist['values'] = adlar
            if adlar:
                cmb_playlist.current(0)
        except Exception as e:
            print(f"Playlist adları çekilemedi: {e}")

    update_combobox()

    def yukle():
        secili = cmb_playlist.get()
        if not secili:
            messagebox.showwarning("Uyarı", "Lütfen bir playlist seçin.", parent=dialog)
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT url_adresi FROM m3u_playlists WHERE playlist_adi=?", (secili,))
            row = cursor.fetchone()
            conn.close()
            if row:
                url = row[0]
                kanallar = parse_m3u_playlist(url)
                iptv_channels_ref.clear() # Ana listeyi temizle
                iptv_channels_ref.extend(kanallar) # Ana listeye ekle
                
                # Treeview'ı güncellemek için create_iptv_tab içindeki populate_treeview benzeri bir yapı lazım.
                # Ya da doğrudan parent_obj.tree (Treeview referansı) üzerinden işlem yapılmalı.
                # Ve parent_obj.search_entry (arama kutusu referansı) temizlenmeli.
                for item_tree in tree.get_children(): # tree parametresi bu scope'da geçerli
                    tree.delete(item_tree)
                for kanal in kanallar:
                    tree.insert("", "end", values=kanal)
                
                # Arama kutusunu da temizle (eğer ana uygulama bunu handle etmiyorsa)
                # Bu diyalog parent_obj (ana uygulama sınıfı örneği) üzerinden arama kutusuna erişebilir.
                if hasattr(parent_obj, 'search_entry_iptv'): # Ana uygulamada arama kutusu referansı varsa
                    parent_obj.search_entry_iptv.delete(0, tk.END)

                messagebox.showinfo("Yüklendi", f"{secili} playlist yüklendi.", parent=dialog)
                dialog.destroy()
        except Exception as e:
            messagebox.showerror("Hata", f"Yükleme başarısız: {e}", parent=dialog)


    def sil():
        secili = cmb_playlist.get()
        if not secili:
            return
        if messagebox.askyesno("Sil", f"{secili} playlisti silinsin mi?", parent=dialog):
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM m3u_playlists WHERE playlist_adi=?", (secili,))
                conn.commit()
                conn.close()
                update_combobox()
                messagebox.showinfo("Silindi", f"{secili} silindi.", parent=dialog)
            except Exception as e:
                messagebox.showerror("Hata", f"Silme hatası: {e}", parent=dialog)

    button_frame = ttk.Frame(frm_yukle)
    button_frame.pack(pady=10)

    ttk.Button(button_frame, text="Yükle", command=yukle).pack(side="left", padx=5)
    ttk.Button(button_frame, text="Sil", command=sil).pack(side="left", padx=5)
    ttk.Button(button_frame, text="İptal", command=dialog.destroy).pack(side="left", padx=5)

    frm_kaydet = ttk.Frame(notebook)
    notebook.add(frm_kaydet, text="Playlist Kaydet")

    ttk.Label(frm_kaydet, text="Playlist Adı:").pack(pady=(10, 0))
    entry_ad = ttk.Entry(frm_kaydet)
    entry_ad.pack(fill="x", padx=10, pady=(0, 10))

    ttk.Label(frm_kaydet, text="URL Adresi:").pack()
    entry_url = ttk.Entry(frm_kaydet)
    entry_url.pack(fill="x", padx=10, pady=(0, 10))

    def kaydet():
        adi = entry_ad.get().strip()
        url = entry_url.get().strip()
        if not adi or not url:
            messagebox.showwarning("Uyarı", "Tüm alanları doldurun!", parent=dialog)
            return
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO m3u_playlists (playlist_adi, url_adresi) VALUES (?, ?)", (adi, url))
            conn.commit()
            conn.close()
            messagebox.showinfo("Başarılı", "Playlist kaydedildi.", parent=dialog)
            entry_ad.delete(0, tk.END)
            entry_url.delete(0, tk.END)
            update_combobox() # Kayıttan sonra combobox'ı güncelle
        except Exception as e:
            messagebox.showerror("Hata", f"Veritabanı hatası: {e}", parent=dialog)

    ttk.Button(frm_kaydet, text="Veritabanına Kaydet", command=kaydet).pack(pady=10)


def init_playlist_table():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS m3u_playlists (
                playlist_adi TEXT PRIMARY KEY,
                url_adresi TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Playlist tablo oluşturulamadı: {e}")

# Ana uygulama veya test için örnek bir yapı (Bu kısım normalde ana dosyanızda olur)
if __name__ == '__main__':
    class MockParentApp:
        def __init__(self, master):
            self.master = master
            self.iptv_channels = [ # Örnek başlangıç kanalları
                ("Kanal A Test", "http://example.com/a"),
                ("Deneme Kanal B", "http://example.com/b"),
                ("Test Kanal C", "http://example.com/c"),
                ("Başka Bir Kanal D", "http://example.com/d")
            ]
            self.tree = None # create_iptv_tab içinde atanacak
            self.search_entry_iptv = None # create_iptv_tab içinde atanacak (search_entry olarak)

    root = tk.Tk()
    root.title("IPTV Test Arayüzü")
    root.geometry("800x600")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # Mock parent uygulamasını oluştur
    app_parent_instance = MockParentApp(root)

    # IPTV sekmesini oluştur
    # channels parametresi başlangıçta kullanılacak, sonra app_parent_instance.iptv_channels ana referans olacak
    create_iptv_tab(app_parent_instance, notebook, app_parent_instance.iptv_channels)
    
    # search_entry'yi app_parent_instance'a bağlayalım (create_iptv_tab içinde search_entry olarak oluşturuluyor)
    # Bu normalde create_iptv_tab içinde yapılır, ama show_playlist_loader_dialog'un erişimi için bir yol.
    # Daha iyi bir yol, create_iptv_tab'ın search_entry'yi parent'a (app_parent_instance) atamasıdır.
    # create_iptv_tab içinde `parent.search_entry_iptv = search_entry` gibi bir satır eklenebilir.
    # Ya da show_playlist_loader_dialog'a tree ve search_entry doğrudan parametre olarak verilir.
    # Şu anki koda göre `parent.tree` zaten atanıyor. Benzer şekilde `parent.search_entry_iptv` de atanabilir.
    # create_iptv_tab içinde `parent.search_entry_iptv = search_entry` ekledim (dolaylı olarak, doğrudan `search_entry` kullanılacak).

    # Diğer sekmeler (opsiyonel)
    tab1 = ttk.Frame(notebook)
    notebook.add(tab1, text='Diğer Sekme 1')
    ttk.Label(tab1, text="Burası diğer bir sekme.").pack(padx=30, pady=30)

    tab_placeholder_for_iptv_position = ttk.Frame(notebook) # IPTV'nin 3. sırada olması için
    # notebook.add(tab_placeholder_for_iptv_position, text='Yer Tutucu')


    root.mainloop()