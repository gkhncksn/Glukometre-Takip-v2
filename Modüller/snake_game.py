import tkinter as tk
from tkinter import *
import random
import os
import sys
import math

# Modül yollarını düzelt
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Oyun sabitleri
WIDTH = 500
HEIGHT = 500
BASE_SPEED = 200  # Temel hız (ms)
SPACE_SIZE = 20
BODY_SIZE = 2
SNAKE = "#00FF00"
FOOD = "#FFFFFF"
BACKGROUND = "#000000"
GAME_OVER_COLOR = "#FF0000"
BUTTON_BG = "#4CAF50"
BUTTON_FG = "#FFFFFF"

# Global değişkenler
window = None
canvas = None
snake = None
food = None
score_label = None
level_label = None
controls_label = None
score = 0
level = 1
direction = 'down'
game_running = False
key_pressed = False
current_speed = BASE_SPEED

class Snake:
    def __init__(self, canvas):
        self.body_size = BODY_SIZE
        self.coordinates = []
        self.squares = []
        self.canvas = canvas

        # Yılanı ekranın ortasına yerleştir
        start_x = (WIDTH // 2) // SPACE_SIZE * SPACE_SIZE
        start_y = (HEIGHT // 2) // SPACE_SIZE * SPACE_SIZE
        
        for i in range(0, BODY_SIZE):
            self.coordinates.append([start_x, start_y + i * SPACE_SIZE])

        for x, y in self.coordinates:
            square = canvas.create_rectangle(
                x, y, x + SPACE_SIZE, y + SPACE_SIZE, 
                fill=SNAKE, tag="snake")
            self.squares.append(square)

class Food:
    def __init__(self, canvas, snake_coordinates):
        self.canvas = canvas
        self.snake_coordinates = snake_coordinates
        self.generate_food()
        
    def generate_food(self):
        """Yılanın üzerinde olmayan rastgele bir konumda yem oluştur"""
        while True:
            x = random.randint(0, (WIDTH // SPACE_SIZE) - 1) * SPACE_SIZE
            y = random.randint(0, (HEIGHT // SPACE_SIZE) - 1) * SPACE_SIZE
            
            # Yılanın üzerinde olmadığından emin ol
            valid_position = True
            for coord in self.snake_coordinates:
                if x == coord[0] and y == coord[1]:
                    valid_position = False
                    break
                    
            if valid_position:
                self.coordinates = [x, y]
                self.canvas.create_oval(
                    x, y, x + SPACE_SIZE, y + SPACE_SIZE, 
                    fill=FOOD, tag="food")
                return

def run_snake_game():
    global window, canvas, snake, food, score_label, level_label, controls_label
    global score, level, direction, game_running, current_speed
    
    # Oyun zaten açıksa yeniden başlat
    if window is not None and window.winfo_exists():
        reset_game()
        return
    
    # Yeni oyun penceresi oluştur
    window = tk.Toplevel()
    window.title("Yılan Oyunu")
    window.resizable(False, False)  # Pencere boyutunu sabitle
    
    # Pencereyi ekranın ortasına yerleştir
    window.update_idletasks()
    window_width = WIDTH
    window_height = HEIGHT + 50
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = int((screen_width/2) - (window_width/2))
    y = int((screen_height/2) - (window_height/2))
    
    window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # UI çerçeveleri oluştur
    top_frame = Frame(window, height=50)
    top_frame.pack(fill=tk.X, padx=10, pady=5)
    
    # Skor ve seviye etiketleri
    score_label = Label(top_frame, text="Puan: 0", font=('consolas', 16))
    score_label.pack(side=tk.LEFT)
    
    level_label = Label(top_frame, text="Seviye: 1", font=('consolas', 16))
    level_label.pack(side=tk.LEFT, padx=20)
    
    # Kontrol bilgisi
    controls_label = Label(top_frame, text="Yön tuşları ile oynayın", 
                          font=('consolas', 10), fg="gray")
    controls_label.pack(side=tk.RIGHT)
    
    # Oyun alanı
    canvas = Canvas(window, bg=BACKGROUND, height=HEIGHT, width=WIDTH)
    canvas.pack()
    
    # Oyun durumunu sıfırla
    reset_game()
    
    # Pencere odağı ve tuş bağlamaları
    window.after(100, set_focus)
    
    # Pencere kapatma davranışı
    window.protocol("WM_DELETE_WINDOW", window.destroy)

def set_focus():
    """Pencereye ve tuş girişlerine odaklan"""
    window.focus_force()
    canvas.focus_set()

def reset_game():
    global snake, food, score, level, direction, game_running, current_speed, key_pressed
    
    # Oyun durumunu sıfırla
    score = 0
    level = 1
    direction = 'down'
    game_running = True
    key_pressed = False
    current_speed = BASE_SPEED
    
    # Etiketleri güncelle
    score_label.config(text=f"Puan: {score}")
    level_label.config(text=f"Seviye: {level}")
    
    # Canvas'ı temizle
    canvas.delete(ALL)
    
    # Tuş bağlamalarını yeniden yap
    window.bind('<Left>', lambda event: key_event('left'))
    window.bind('<Right>', lambda event: key_event('right'))
    window.bind('<Up>', lambda event: key_event('up'))
    window.bind('<Down>', lambda event: key_event('down'))
    
    # Tuş bırakma olaylarını izle (hızlanma için)
    window.bind('<KeyRelease>', lambda event: key_release())
    
    # Yılan ve yem oluştur
    snake = Snake(canvas)
    food = Food(canvas, snake.coordinates)
    
    # Oyun döngüsünü başlat
    next_turn(snake, food)
    
    # Odağı yeniden ayarla
    set_focus()

def next_turn(snake, food):
    global game_running, current_speed
    
    if not game_running:
        return
    
    x, y = snake.coordinates[0]
    
    if direction == "up":
        y -= SPACE_SIZE
    elif direction == "down":
        y += SPACE_SIZE
    elif direction == "left":
        x -= SPACE_SIZE
    elif direction == "right":
        x += SPACE_SIZE
    
    snake.coordinates.insert(0, (x, y))
    
    square = canvas.create_rectangle(
        x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE)
    
    snake.squares.insert(0, square)
    
    # Yem yendi mi kontrol et
    if x == food.coordinates[0] and y == food.coordinates[1]:
        global score, level
        
        # Puanı artır
        score += 1
        score_label.config(text=f"Puan: {score}")
        
        # Her 5 puanda bir seviye atla
        if score % 5 == 0:
            level_up()
        
        # Yeni yem oluştur
        canvas.delete("food")
        food = Food(canvas, snake.coordinates)
    else:
        # Yem yenmediyse kuyruğu kısalt
        del snake.coordinates[-1]
        canvas.delete(snake.squares[-1])
        del snake.squares[-1]
    
    # Çarpışma kontrolü
    if check_collisions(snake):
        game_over()
    else:
        # Hızlanma etkisi: Tuşa basılı tutuluyorsa daha hızlı hareket et
        speed = current_speed
        if key_pressed:
            # Kısa yılanlarda daha belirgin hızlanma
            base_acceleration = 0.7 if len(snake.coordinates) < 10 else 0.5
            
            # Seviye arttıkça hızlanma etkisi azalsın
            acceleration_factor = max(0.2, base_acceleration - (level * 0.05))
            
            # Yılanın boyu arttıkça hızlanma etkisi azalsın
            length_factor = max(0.3, 1.0 - (len(snake.coordinates) * 0.01))
            
            # Nihai hızlanma faktörü
            speed_factor = acceleration_factor * length_factor
            
            # Hızı hesapla
            speed = int(current_speed * speed_factor)
        
        window.after(speed, next_turn, snake, food)

def level_up():
    global level, current_speed
    
    level += 1
    level_label.config(text=f"Seviye: {level}")
    
    # Seviye arttıkça hızlan (minimum 50ms)
    # Her seviyede 10ms daha hızlı
    current_speed = max(50, BASE_SPEED - (level - 1) * 10)

def key_event(new_direction):
    global key_pressed
    key_pressed = True
    change_direction(new_direction)

def key_release():
    global key_pressed
    key_pressed = False

def change_direction(new_direction):
    global direction
    
    if not game_running:
        return
    
    if new_direction == 'left' and direction != 'right':
        direction = 'left'
    elif new_direction == 'right' and direction != 'left':
        direction = 'right'
    elif new_direction == 'up' and direction != 'down':
        direction = 'up'
    elif new_direction == 'down' and direction != 'up':
        direction = 'down'

def check_collisions(snake):
    x, y = snake.coordinates[0]
    
    # Duvara çarpma kontrolü
    if x < 0 or x >= WIDTH:
        return True
    elif y < 0 or y >= HEIGHT:
        return True
    
    # Kendine çarpma kontrolü (baş hariç)
    for body_part in snake.coordinates[1:]:
        if x == body_part[0] and y == body_part[1]:
            return True
    
    return False

def game_over():
    global game_running
    game_running = False
    
    # Canvas üzerinde oyun bitiş ekranı
    canvas.delete(ALL)
    canvas.create_text(
        WIDTH/2, 
        HEIGHT/2 - 50,
        font=('consolas', 40), 
        text="OYUN BİTTİ", 
        fill=GAME_OVER_COLOR, 
        tag="gameover")
    
    canvas.create_text(
        WIDTH/2, 
        HEIGHT/2,
        font=('consolas', 20), 
        text=f"Puan: {score}  |  Seviye: {level}", 
        fill="white", 
        tag="score")
    
    # Buton çerçevesi
    button_frame = Frame(canvas, bg=BACKGROUND)
    canvas.create_window(WIDTH/2, HEIGHT/2 + 50, window=button_frame)
    
    # Yeni Oyun Butonu
    new_game_btn = Button(
        button_frame, 
        text="Yeni Oyun", 
        font=('consolas', 14),
        bg=BUTTON_BG,
        fg=BUTTON_FG,
        padx=20,
        pady=10,
        command=reset_game
    )
    new_game_btn.pack(side=tk.LEFT, padx=10)
    
    # Çıkış Butonu
    quit_btn = Button(
        button_frame, 
        text="Çık", 
        font=('consolas', 14),
        bg="#F44336",
        fg=BUTTON_FG,
        padx=20,
        pady=10,
        command=window.destroy
    )
    quit_btn.pack(side=tk.RIGHT, padx=10)
    
    # Odağı butonlara ver
    new_game_btn.focus_set()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi gizle
    run_snake_game()
    root.mainloop()