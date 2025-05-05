import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import subprocess, sys, os

# ──────────────── ĐƯỜNG DẪN TÀI NGUYÊN ────────────────
BG_IMG   = "bgr2.jpg"                # hình nền menu
HELP_IMG = "huongdan.png"  # hình hướng dẫn full màn hình

# ──────────────── TIỆN ÍCH ────────────────
def rounded_rectangle(w, h, r, fill):
    """Tạo PhotoImage hình chữ nhật bo tròn."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, w, h), r, fill=fill)
    return ImageTk.PhotoImage(img)

# ──────────────── CALLBACK CÁC NÚT ────────────────
def open_parking():
    subprocess.Popen([sys.executable, "manual_mode.py"])

def open_analysis():
    subprocess.run([sys.executable, "simulation_mode.py"])

def open_help():
    """Hiển thị ảnh hướng dẫn toàn màn hình – đóng bằng ESC hoặc click."""
    if not os.path.exists(HELP_IMG):
        messagebox.showerror("Lỗi", f"Không tìm thấy ảnh: {HELP_IMG}")
        return

    help_win = tk.Toplevel(root)
    help_win.attributes("-fullscreen", True)
    help_win.bind("<Escape>", lambda e: help_win.destroy())
    help_win.bind("<Button-1>", lambda e: help_win.destroy())   # click để tắt

    sw, sh = help_win.winfo_screenwidth(), help_win.winfo_screenheight()
    photo  = ImageTk.PhotoImage(Image.open(HELP_IMG).resize((sw, sh), Image.LANCZOS))
    tk.Label(help_win, image=photo).pack(fill="both", expand=True)
    help_win._photo_ref = photo        # giữ tham chiếu tránh GC

# ──────────────── KHỞI TẠO GIAO DIỆN ────────────────
root = tk.Tk()
root.title("Tìm đường đến vị trí đỗ xe - Nhập môn AI")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
bg_photo = ImageTk.PhotoImage(Image.open(BG_IMG).resize((sw, sh), Image.LANCZOS))

canvas = tk.Canvas(root, width=sw, height=sh, highlightthickness=0)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=bg_photo, anchor="nw")

# ──────────────── PANEL & NÚT ────────────────
panel_img = rounded_rectangle(720, 520, 54, fill=(255, 255, 255, 210))
panel_x, panel_y = sw // 2, sh // 2
canvas.create_image(panel_x, panel_y, image=panel_img)

canvas.create_text(
    panel_x, panel_y - 170,
    text="Hệ thống đỗ xe thông minh",
    font=("Segoe UI", 32, "bold"), fill="#892be2"
)

def make_button(text, icon, cmd):
    img = rounded_rectangle(340, 70, 20, fill="#892be2")
    btn = tk.Button(
        root,
        image=img,
        text=f"{icon}   {text}",
        compound="center",
        font=("Segoe UI", 22, "bold"),
        fg="white",
        bd=0,
        activebackground="#6417b5",
        activeforeground="#fff",
        cursor="hand2",
        command=cmd
    )
    btn._img_ref = img   # tránh rò bộ nhớ
    return btn

canvas.create_window(panel_x, panel_y -  30, window=make_button("manual",     "🚗", open_parking))
canvas.create_window(panel_x, panel_y +  70, window=make_button("Simulation", "📊", open_analysis))
canvas.create_window(panel_x, panel_y + 170, window=make_button("Hướng dẫn",  "❓", open_help))

root.mainloop()
