import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
def open_parking():
    subprocess.Popen([sys.executable, "manual_mode.py"])



def open_analysis():
    subprocess.run([sys.executable, "simulation_mode.py"])

def open_help():
    messagebox.showinfo("Hướng dẫn", "Chức năng Hướng dẫn sẽ được thực hiện ở đây!")

def rounded_rectangle(w, h, r, fill):
    """Tạo ảnh PNG hình chữ nhật bo tròn"""
    image = Image.new("RGBA", (w, h), (255, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, w, h), r, fill=fill)
    return ImageTk.PhotoImage(image)

root = tk.Tk()
root.title("Tìm đường đến vị trí đỗ xe - Nhập môn AI")
root.attributes('-fullscreen', True)

background_image = Image.open("bgr2.jpg")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
background_image = background_image.resize((screen_width, screen_height), Image.LANCZOS)
bg_photo = ImageTk.PhotoImage(background_image)

canvas = tk.Canvas(root, width=screen_width, height=screen_height, highlightthickness=0)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# Tăng kích thước panel cho cân đối
panel_width, panel_height = 720, 520
panel_x, panel_y = screen_width//2, screen_height//2
panel_img = rounded_rectangle(panel_width, panel_height, 54, fill=(255,255,255,205))
panel = canvas.create_image(panel_x, panel_y, image=panel_img)

# Tiêu đề nằm trong panel, to hơn, màu đậm, căn giữa panel
label = tk.Label(root, text="Hệ thông đỗ xe thông minh",
                 font=("Segoe UI", 32, "bold"), bg="#ffffff", fg="#892be2", borderwidth=0)
canvas.create_window(panel_x, panel_y-170, window=label)

# Tạo nút đẹp, icon cách chữ đều, nút đủ rộng
def make_button(text, icon, command):
    btn_w, btn_h, btn_r = 340, 70, 20
    btn_img = rounded_rectangle(btn_w, btn_h, btn_r, fill="#892be2")
    btn = tk.Button(root,
        text=f"{icon}   {text}",
        font=("Segoe UI", 22, "bold"),
        fg="white",
        bg="#892be2",
        bd=0,
        highlightthickness=0,
        activebackground="#6417b5",
        activeforeground="#fff",
        cursor="hand2",
        relief=tk.FLAT,
        command=command,
        width=14, height=1,
        padx=20, pady=8,
        compound="left"
    )
    return btn

btn_parking = make_button("manual", "🚗", open_parking)
btn_analysis = make_button("Simulation", "📊", open_analysis)
btn_help = make_button("Hướng dẫn", "❓", open_help)

canvas.create_window(panel_x, panel_y-30, window=btn_parking)
canvas.create_window(panel_x, panel_y+70, window=btn_analysis)
canvas.create_window(panel_x, panel_y+170, window=btn_help)

root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
root.mainloop()
