import tkinter as tk
from tkinter import messagebox
import random

class Game2048:
    def __init__(self, master):
        self.master = master
        self.master.title("2048 Oyunu")
        self.master.resizable(False, False)
        self.grid = [[0]*4 for _ in range(4)]
        self.score = 0

        self.frame = tk.Frame(self.master, bg="azure4")
        self.frame.pack(padx=10, pady=10)

        self.labels = [[tk.Label(self.frame, text="", width=4, height=2,
                        font=("Helvetica", 24, "bold"), bg="azure", relief="ridge")
                        for _ in range(4)] for _ in range(4)]

        for i in range(4):
            for j in range(4):
                self.labels[i][j].grid(row=i, column=j, padx=5, pady=5)

        self.score_label = tk.Label(self.master, text="Skor: 0", font=("Arial", 14, "bold"))
        self.score_label.pack()

        self.master.bind("<Key>", self.key_handler)
        self.new_tile()
        self.new_tile()
        self.update_ui()

    def new_tile(self):
        empty = [(i, j) for i in range(4) for j in range(4) if self.grid[i][j] == 0]
        if empty:
            i, j = random.choice(empty)
            self.grid[i][j] = 2 if random.random() < 0.9 else 4

    def compress(self, row):
        new_row = [i for i in row if i != 0]
        new_row += [0] * (4 - len(new_row))
        return new_row

    def merge(self, row):
        for i in range(3):
            if row[i] != 0 and row[i] == row[i+1]:
                row[i] *= 2
                self.score += row[i]
                row[i+1] = 0
        return row

    def move_left(self):
        changed = False
        for i in range(4):
            original = list(self.grid[i])
            compressed = self.compress(self.grid[i])
            merged = self.merge(compressed)
            self.grid[i] = self.compress(merged)
            if self.grid[i] != original:
                changed = True
        return changed

    def move_right(self):
        self.reverse()
        changed = self.move_left()
        self.reverse()
        return changed

    def move_up(self):
        self.transpose()
        changed = self.move_left()
        self.transpose()
        return changed

    def move_down(self):
        self.transpose()
        changed = self.move_right()
        self.transpose()
        return changed

    def reverse(self):
        for i in range(4):
            self.grid[i].reverse()

    def transpose(self):
        self.grid = [list(row) for row in zip(*self.grid)]

    def key_handler(self, event):
        key = event.keysym
        moved = False
        if key == "Up":
            moved = self.move_up()
        elif key == "Down":
            moved = self.move_down()
        elif key == "Left":
            moved = self.move_left()
        elif key == "Right":
            moved = self.move_right()
        if moved:
            self.new_tile()
            self.update_ui()
            if self.is_game_over():
                messagebox.showinfo("Oyun Bitti", f"Skorunuz: {self.score}")
                self.master.destroy()

    def update_ui(self):
        for i in range(4):
            for j in range(4):
                val = self.grid[i][j]
                self.labels[i][j].config(text=str(val) if val else "", bg=self.tile_color(val))
        self.score_label.config(text=f"Skor: {self.score}")

    def tile_color(self, val):
        colors = {
            0: "azure",
            2: "#eee4da", 4: "#ede0c8", 8: "#f2b179",
            16: "#f59563", 32: "#f67c5f", 64: "#f65e3b",
            128: "#edcf72", 256: "#edcc61", 512: "#edc850",
            1024: "#edc53f", 2048: "#edc22e"
        }
        return colors.get(val, "azure4")

    def is_game_over(self):
        for i in range(4):
            for j in range(4):
                if self.grid[i][j] == 0:
                    return False
                if j < 3 and self.grid[i][j] == self.grid[i][j+1]:
                    return False
                if i < 3 and self.grid[i][j] == self.grid[i+1][j]:
                    return False
        return True

if __name__ == "__main__":
    root = tk.Tk()
    app = Game2048(root)
    root.mainloop()
