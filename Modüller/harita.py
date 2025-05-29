import tkinter as tk
from tkinter import messagebox
import tkintermapview

class MapViewer:
    def __init__(self, master):
        self.master = master
        self.points = []
        self.measuring = False
        self.map_viewer = None

    def record_point(self, lat, lon):
        if self.measuring:
            self.points.append((lat, lon))
            if len(self.points) == 2:
                distance = self.haversine(self.points[0], self.points[1])
                messagebox.showinfo("Mesafe", f"Mesafe: {distance:.2f} km")
                self.map_viewer.set_path([self.points[0], self.points[1]], color="blue")
                self.measuring = False
                self.points = []

    def open_map(self):
        top = tk.Toplevel(self.master)
        top.title("Harita")
        top.geometry("1100x630")
        top.resizable(True, True)
        top.transient(self.master)
        top.grab_set()

        # Kontrol çerçevesi
        control_frame = tk.Frame(top)
        control_frame.pack(side=tk.TOP, fill=tk.X)


        def clear_markers():
            self.map_viewer.delete_all_marker()

        clear_button = tk.Button(control_frame, text="İşaretçileri Sil", command=clear_markers)
        clear_button.pack(side=tk.LEFT)

        # Harita görüntüleyici
        self.map_viewer = tkintermapview.TkinterMapView(master=top, width=1100, height=580, corner_radius=0, bg="#332f2f")
        self.map_viewer.pack(fill="both", expand=True)
        self.map_viewer.set_position(41.271743, 36.298203)
        self.map_viewer.set_marker(41.271743, 36.298203, text="Samsun Eğitim ve Araştırma Hastanesi")
        self.map_viewer.set_marker(41.261700, 36.320961, text="Çokşen's Home")
        self.map_viewer.set_zoom(14)

        # Sol tıklama komutu
        self.map_viewer.add_left_click_map_command(self.record_point)