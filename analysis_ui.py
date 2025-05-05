# analysis_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import json, os
from PIL import Image, ImageTk


# ──────────────────────────────────────────────────────────────────────────────
#  HÀM VẼ PHÂN TÍCH
# ──────────────────────────────────────────────────────────────────────────────
def draw_analysis(canvas_frame):
    """Đọc ./Data/simulation_results.json và vẽ 3 biểu đồ cột + 1 biểu đồ bánh
       (mỗi lát 1 màu, legend 2 cột không tràn)."""

    for w in canvas_frame.winfo_children():
        w.destroy()

    # Đọc dữ liệu --------------------------------------------------------------
    try:
        with open("./Data/simulation_results.json", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc dữ liệu:\n{e}")
        return

    algos, t_ms, steps, s_rate = [], [], [], []
    for algo, info in data.items():
        if None in (
            info.get("time_avg_ms"),
            info.get("path_len_avg"),
            info.get("success_rate"),
        ):
            continue
        algos.append(algo)
        t_ms.append(info["time_avg_ms"])
        steps.append(info["path_len_avg"])
        s_rate.append(info["success_rate"] * 100)

    if not algos:
        messagebox.showinfo("Thông báo", "Không có dữ liệu hợp lệ để phân tích.")
        return

    # Tạo figure ---------------------------------------------------------------
    fig, axs = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle("Phân tích kết quả", fontsize=24, weight="bold")

    axs[0, 0].bar(algos, t_ms, color="#90caf9")
    axs[0, 0].set_title("Thời gian trung bình (ms)")
    axs[0, 0].set_ylabel("milliseconds")

    axs[0, 1].bar(algos, steps, color="#ffb74d")
    axs[0, 1].set_title("Số bước trung bình")
    axs[0, 1].set_ylabel("steps")

    axs[1, 0].bar(algos, s_rate, color="#66bb6a")
    axs[1, 0].set_title("Tỉ lệ thành công (%)")
    axs[1, 0].set_ylabel("%")

    # Pie chart ---------------------------------------------------------------
    labels, values = [], []
    for algo, info in data.items():
        for stt, rate in [
            ("Thành công", info.get("success_rate", 0)),
            ("Va chạm",    info.get("collision_rate", 0)),
            ("Timeout",    info.get("timeout_rate", 0)),
        ]:
            labels.append(f"{algo} - {stt}")
            values.append(rate)

    cmap = plt.cm.get_cmap("tab20", len(values))          # N màu khác nhau
    colors = [cmap(i) for i in range(len(values))]

    wedges, *_ = axs[1, 1].pie(
        values,
        autopct="%1.1f%%",
        pctdistance=0.75,
        colors=colors,
        startangle=90,
        textprops=dict(color="white", fontsize=8),
        wedgeprops=dict(edgecolor="white", linewidth=1),
    )

    axs[1, 1].set_title("Tỉ lệ trạng thái")
    axs[1, 1].axis("equal")

    # Legend hai cột bên phải
    axs[1, 1].legend(
        wedges,
        labels,
        title="Chú giải",
        ncol=2,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        title_fontsize=10,
    )

    plt.tight_layout(rect=[0, 0, 0.88, 0.95])  # chừa chỗ cho legend

    # Nhúng vào Tkinter --------------------------------------------------------
    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(padx=20, pady=20)


# ──────────────────────────────────────────────────────────────────────────────
#  TIỆN ÍCH GIAO DIỆN
# ──────────────────────────────────────────────────────────────────────────────
def exit_program():
    os._exit(0)


def open_analysis():
    win = tk.Toplevel()
    win.title("Phân tích kết quả Simulation")
    win.attributes("-fullscreen", True)
    win.bind("<Escape>", lambda e: win.attributes("-fullscreen", False))

    try:
        bg = Image.open("./Data/bgr3.jpg")
        bg = bg.resize((win.winfo_screenwidth(), win.winfo_screenheight()))
        bg_ph = ImageTk.PhotoImage(bg)
        tk.Label(win, image=bg_ph).place(relwidth=1, relheight=1)
        win._bg = bg_ph
    except Exception as e:
        print("Lỗi background:", e)

    main = tk.Frame(win, bg="white")
    main.pack(fill="both", expand=True)

    canvas = tk.Canvas(main, bg="white", highlightthickness=0)
    vsb = ttk.Scrollbar(main, orient="vertical", command=canvas.yview)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.configure(yscrollcommand=vsb.set)

    inner = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    draw_analysis(inner)


def launch_analysis_ui():
    root = tk.Tk()
    root.title("Simulation Completed")
    root.attributes("-fullscreen", True)
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

    try:
        bg = Image.open("./Data/bgr3.jpg")
        bg = bg.resize((root.winfo_screenwidth(), root.winfo_screenheight()))
        bg_ph = ImageTk.PhotoImage(bg)
        tk.Label(root, image=bg_ph).place(relwidth=1, relheight=1)
        root._bg = bg_ph
    except Exception as e:
        print("Lỗi background:", e)

    tk.Label(
        root,
        text="Simulation Hoàn tất!",
        font=("Consolas", 48, "bold"),
        bg="white",
        fg="black",
    ).pack(pady=50)

    tk.Button(
        root,
        text="Phân tích kết quả",
        font=("Consolas", 32, "bold"),
        bg="#4CAF50",
        fg="white",
        padx=20,
        pady=10,
        command=open_analysis,
    ).pack(pady=20)

    tk.Button(
        root,
        text="Thoát",
        font=("Consolas", 24),
        bg="#f44336",
        fg="white",
        padx=20,
        pady=5,
        command=exit_program,
    ).pack(pady=20)

    root.protocol("WM_DELETE_WINDOW", exit_program)
    root.mainloop()


if __name__ == "__main__":
    launch_analysis_ui()
