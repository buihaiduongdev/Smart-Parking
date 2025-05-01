# analysis_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import json
import os
from PIL import Image, ImageTk

def your_analysis_function(frame_canvas):
    """Vẽ biểu đồ trực tiếp lên frame_canvas"""
    for widget in frame_canvas.winfo_children():
        widget.destroy()

    try:
        with open("./Data/simulation_results.json", "r", encoding="utf-8") as f:
            results = json.load(f)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc dữ liệu: {e}")
        return

    algorithms = []
    avg_times = []
    avg_steps = []
    success_rates = []

    for algo, info in results.items():
        if info.get('time_avg_ms') is not None and info.get('path_len_avg') is not None and info.get('success_rate') is not None:
            algorithms.append(algo)
            avg_times.append(info['time_avg_ms'])
            avg_steps.append(info['path_len_avg'])
            success_rates.append(info['success_rate'] * 100)  # nhân 100 cho ra %

    if not algorithms:
        messagebox.showerror("Lỗi", "Không có dữ liệu hợp lệ để phân tích!")
        return

    fig, axs = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle('Phân tích Kết quả', fontsize=24)

    axs[0,0].bar(algorithms, avg_times, color='skyblue')
    axs[0,0].set_title('Thời gian trung bình (ms)')
    axs[0,0].set_ylabel('Milliseconds')

    axs[0,1].bar(algorithms, avg_steps, color='orange')
    axs[0,1].set_title('Số bước trung bình')
    axs[0,1].set_ylabel('Steps')

    axs[1,0].bar(algorithms, success_rates, color='green')
    axs[1,0].set_title('Tỉ lệ thành công (%)')
    axs[1,0].set_ylabel('%')

    # Vẽ pie chart tổng kết
    labels = []
    values = []
    for algo, info in results.items():
        labels.append(f"{algo} - Thành công")
        labels.append(f"{algo} - Va chạm")
        labels.append(f"{algo} - Timeout")
        values.extend([
            info.get('success_rate', 0),
            info.get('collision_rate', 0),
            info.get('timeout_rate', 0)
        ])
    axs[1,1].pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    axs[1,1].set_title('Tỉ lệ trạng thái')

    plt.tight_layout()

    chart = FigureCanvasTkAgg(fig, master=frame_canvas)
    chart.draw()
    chart.get_tk_widget().pack(pady=20)

def exit_program():
    print("Đã thoát chương trình!")
    os._exit(0)

def open_analysis():
    analysis_window = tk.Toplevel()
    analysis_window.title("Phân tích kết quả Simulation")
    analysis_window.attributes('-fullscreen', True)

    # Nền
    try:
        bg_image = Image.open("./Data/bgr3.jpg")  # ← Bạn đổi path hình nếu muốn
        bg_image = bg_image.resize((analysis_window.winfo_screenwidth(), analysis_window.winfo_screenheight()))
        bg_photo = ImageTk.PhotoImage(bg_image)

        background_label = tk.Label(analysis_window, image=bg_photo)
        background_label.image = bg_photo
        background_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Lỗi load background: {e}")

    # Frame chứa biểu đồ
    main_frame = tk.Frame(analysis_window, bg="white")
    main_frame.pack(fill=tk.BOTH, expand=1)

    canvas = tk.Canvas(main_frame, bg="white")
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

    scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    second_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=second_frame, anchor="nw")

    # Gọi vẽ biểu đồ
    your_analysis_function(second_frame)

def launch_analysis_ui():
    root = tk.Tk()
    root.title("Simulation Completed")
    root.attributes('-fullscreen', True)

    try:
        bg_image = Image.open("./Data/bgr3.jpg")  # ← Ảnh nền giao diện bấm "Phân tích"
        bg_image = bg_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()))
        bg_photo = ImageTk.PhotoImage(bg_image)

        background_label = tk.Label(root, image=bg_photo)
        background_label.image = bg_photo
        background_label.place(x=0, y=0, relwidth=1, relheight=1)
    except Exception as e:
        print(f"Lỗi load background: {e}")

    # Nội dung
    label = tk.Label(root, text="Simulation Hoàn tất!", font=("consolas", 48, "bold"), bg="white", fg="black")
    label.pack(pady=50)

    analyze_btn = tk.Button(root, text="Phân tích kết quả", font=("consolas", 32, "bold"), bg="#4CAF50", fg="white", padx=20, pady=10, command=open_analysis)
    analyze_btn.pack(pady=20)

    exit_btn = tk.Button(root, text="Thoát", font=("consolas", 24), bg="#f44336", fg="white", padx=20, pady=5, command=exit_program)
    exit_btn.pack(pady=20)

    root.protocol("WM_DELETE_WINDOW", exit_program)

    root.mainloop()

if __name__ == "__main__":
    launch_analysis_ui()