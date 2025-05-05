import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import json, os, math
from PIL import Image, ImageTk

def draw_analysis(canvas_frame):

    for w in canvas_frame.winfo_children():
        w.destroy()

    results_file = "./Data/simulation_results.json"
    try:
        with open(results_file, 'r', encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        messagebox.showerror("Lỗi", f"Không tìm thấy file kết quả:\n{results_file}")
        return
    except json.JSONDecodeError:
         messagebox.showerror("Lỗi", f"File kết quả không phải là JSON hợp lệ:\n{results_file}")
         return
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc dữ liệu:\n{e}")
        return

    algos = []
    time_avg = []
    path_len_avg = []
    success_rate = []
    turns_avg_list = []
    nodes_expanded_avg = []
    memory_nodes_avg = [] 

    for algo, info in data.items():
        print(f"  Algorithm: {algo}") 

        t_avg = info.get("time_avg_ms")
        pl_avg = info.get("path_len_avg")
        ac_avg = info.get("action_count_avg")
        step_metric_avg = pl_avg if pl_avg is not None else ac_avg 
        s_rate_val = info.get("success_rate")
        turns_val = info.get("turns_avg") 
        nodes_val = info.get("nodes_expanded_avg") 
        mem_val = info.get("memory_nodes_avg") 

        if None in (t_avg, step_metric_avg, s_rate_val):
            print(f"    Skipping {algo}: Missing essential average data (time, steps/actions, or success rate).")
            continue

        algos.append(algo)
        time_avg.append(t_avg)
        path_len_avg.append(step_metric_avg) 
        success_rate.append(s_rate_val * 100) 
        turns_avg_list.append(turns_val if turns_val is not None else 0) 
        nodes_expanded_avg.append(nodes_val if nodes_val is not None else 0)
        memory_nodes_avg.append(mem_val if mem_val is not None else 0)

    if not algos:
        messagebox.showinfo("Thông báo", "Không có đủ dữ liệu hợp lệ để vẽ biểu đồ.")
        return

    num_metrics = 3 
    if any(t > 0 for t in turns_avg_list): num_metrics += 1 

    num_cols = 2
    num_rows = math.ceil(num_metrics / num_cols)

    fig_height = 6 * num_rows
    fig_width = 16 

    fig, axs = plt.subplots(num_rows, num_cols, figsize=(fig_width, fig_height), squeeze=False) 
    fig.suptitle("Phân Tích Kết Quả Mô Phỏng", fontsize=20, weight="bold")

    plot_index = 0 

    def plot_bar(ax, x_labels, y_values, title, ylabel, color):
        ax.bar(x_labels, y_values, color=color)
        ax.set_title(title, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.tick_params(axis='x', rotation=30, labelsize=10) 
        ax.grid(axis='y', linestyle='--', alpha=0.7) 

    row, col = divmod(plot_index, num_cols)
    plot_bar(axs[row, col], algos, time_avg, "Thời gian trung bình (ms)", "milliseconds", "#90caf9")
    plot_index += 1

    row, col = divmod(plot_index, num_cols)
    plot_bar(axs[row, col], algos, path_len_avg, "Số bước/hành động trung bình", "steps/actions", "#ffb74d")
    plot_index += 1

    row, col = divmod(plot_index, num_cols)
    plot_bar(axs[row, col], algos, success_rate, "Tỉ lệ thành công (%)", "%", "#66bb6a")
    plot_index += 1

    if any(t is not None and t > 0 for t in turns_avg_list): 
        row, col = divmod(plot_index, num_cols)
        plot_bar(axs[row, col], algos, turns_avg_list, "Số lần rẽ trung bình", "turns", "#80cbc4")
        plot_index += 1

    while plot_index < num_rows * num_cols:
        row, col = divmod(plot_index, num_cols)
        fig.delaxes(axs[row, col])
        plot_index += 1

    plt.subplots_adjust(left=0.08, right=0.95, bottom=0.3, top=0.93, wspace=0.3, hspace=0.4)

    canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

def exit_program():
    print("Exiting program.")
    os._exit(0)

def open_analysis():
    win = tk.Toplevel()
    win.title("Phân tích kết quả Simulation")
    win.geometry(f"{win.winfo_screenwidth()}x{win.winfo_screenheight()}+0+0") 
    win.bind("<Escape>", lambda e: win.destroy()) 

    main_frame = tk.Frame(win, bg="white")
    main_frame.pack(fill="both", expand=True)

    canvas_widget = tk.Canvas(main_frame, bg="white", highlightthickness=0)

    vsb = ttk.Scrollbar(main_frame, orient="vertical", command=canvas_widget.yview)
    canvas_widget.configure(yscrollcommand=vsb.set)

    vsb.pack(side="right", fill="y")
    canvas_widget.pack(side="left", fill="both", expand=True)

    inner_frame = tk.Frame(canvas_widget, bg="white")
    canvas_widget.create_window((0, 0), window=inner_frame, anchor="nw")

    inner_frame.bind("<Configure>", lambda e: canvas_widget.configure(scrollregion=canvas_widget.bbox("all")))

    draw_analysis(inner_frame)

    close_button = tk.Button(win, text="Đóng (Esc)", command=win.destroy, font=("Consolas", 12), bg="#f44336", fg="white")
    close_button.pack(pady=10)

def launch_analysis_ui():
    root = tk.Tk()
    root.title("Simulation Completed")
    root.geometry(f"{root.winfo_screenwidth()//2}x{root.winfo_screenheight()//2}+{root.winfo_screenwidth()//4}+{root.winfo_screenheight()//4}") 
    root.attributes("-fullscreen", True) 

    try:
        bg_img = Image.open("./Data/bgr3.jpg") 

        initial_w, initial_h = root.winfo_screenwidth()//2, root.winfo_screenheight()//2
        bg_img = bg_img.resize((initial_w, initial_h))
        bg_photo = ImageTk.PhotoImage(bg_img)
        bg_label = tk.Label(root, image=bg_photo)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        root._bg = bg_photo 
    except Exception as e:
        print(f"Lỗi load background cho cửa sổ chính: {e}")
        root.config(bg="lightgrey") 

    button_frame = tk.Frame(root, bg="white") 
    button_frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        button_frame,
        text="Simulation Hoàn Tất!",
        font=("Consolas", 36, "bold"), 
        bg="white", 
        fg="black",
        padx=20, pady=10
    ).pack(pady=(20, 10)) 

    tk.Button(
        button_frame,
        text="Phân tích kết quả",
        font=("Consolas", 24, "bold"), 
        bg="#4CAF50",
        fg="white",
        padx=15, pady=8,
        command=open_analysis, 
        relief=tk.RAISED, 
        bd=3 
    ).pack(pady=10, fill=tk.X, padx=20)

    tk.Button(
        button_frame,
        text="Thoát",
        font=("Consolas", 18), 
        bg="#f44336",
        fg="white",
        padx=15, pady=5,
        command=exit_program,
        relief=tk.RAISED,
        bd=3
    ).pack(pady=(10, 20), fill=tk.X, padx=20)

    root.protocol("WM_DELETE_WINDOW", exit_program)
    root.mainloop()

if __name__ == "__main__":
    launch_analysis_ui()