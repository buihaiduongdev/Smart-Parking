import matplotlib.pyplot as plt
import json
import os

file_path = os.path.join(os.path.dirname(__file__), "simulation_results.json")
with open(file_path, 'r') as file:
    data = json.load(file)

algorithms = ['A*', 'BFS']
time_avg = [data['a_star']['time_avg_ms'], data['bfs']['time_avg_ms']]
path_len_avg = [data['a_star']['path_len_avg'], data['bfs']['path_len_avg']]

fig, ax1 = plt.subplots(figsize=(8, 6))

bar_width = 0.35
x = range(len(algorithms))

bars1 = ax1.bar([i - bar_width/2 for i in x], time_avg, 
                bar_width, label='Thời gian trung bình (ms)', 
                color='skyblue', edgecolor='black')
ax1.set_xlabel('Thuật toán', fontsize=12)
ax1.set_ylabel('Thời gian (ms)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')
ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

ax2 = ax1.twinx()
bars2 = ax2.bar([i + bar_width/2 for i in x], path_len_avg, 
                bar_width, label='Độ dài đường đi trung bình', 
                color='lightgreen', edgecolor='black')
ax2.set_ylabel('Độ dài đường đi', color='green', fontsize=12)
ax2.tick_params(axis='y', labelcolor='green')

for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.1f}', ha='center', va='bottom', color='blue')

for bar in bars2:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.1f}', ha='center', va='bottom', color='green')

plt.xticks(x, algorithms, fontsize=11)
plt.title('So sánh hiệu suất A* và BFS', fontsize=14, pad=15)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, 
          bbox_to_anchor=(0.5, -0.15), loc='upper center', 
          ncol=2, fontsize=10, frameon=True)
plt.tight_layout()
plt.show()

algorithms = ['A*', 'BFS']
success_rates = [data['a_star']['success_rate'], data['bfs']['success_rate']]
collision_rates = [data['a_star']['collision_rate'], data['bfs']['collision_rate']]

fig, ax = plt.subplots(figsize=(8, 6))

bar_width = 0.35
x = range(len(algorithms))

bars1 = ax.bar([i - bar_width/2 for i in x], success_rates, 
               bar_width, label='Tỷ lệ thành công', 
               color='lightgreen', edgecolor='black')
bars2 = ax.bar([i + bar_width/2 for i in x], collision_rates, 
               bar_width, label='Tỷ lệ va chạm', 
               color='salmon', edgecolor='black')

ax.set_xlabel('Thuật toán', fontsize=12)
ax.set_ylabel('Tỷ lệ (%)', fontsize=12)
ax.set_title('So sánh tỷ lệ thành công và va chạm', fontsize=14, pad=15)
ax.set_xticks(x)
ax.set_xticklabels(algorithms, fontsize=11)
ax.set_ylim(0, 1.2)  

ax.grid(True, axis='y', linestyle='--', alpha=0.7)

for bar in bars1:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.2f}', ha='center', va='bottom', fontsize=10)

for bar in bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{height:.2f}', ha='center', va='bottom', fontsize=10)

ax.legend(bbox_to_anchor=(0.5, -0.15), loc='upper center', 
         ncol=2, fontsize=10, frameon=True)

plt.tight_layout()
plt.show()

times_a_star = data['a_star']['completion_times_ms']
times_bfs = data['bfs']['completion_times_ms']

fig, ax = plt.subplots(figsize=(8, 6))

box = ax.boxplot([times_a_star, times_bfs], labels=['A*', 'BFS'], 
                 patch_artist=True, 
                 widths=0.35)  

colors = ['skyblue', 'lightgreen']
for patch, color in zip(box['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_edgecolor('black')

ax.set_xlabel('Thuật toán', fontsize=12)
ax.set_ylabel('Thời gian (ms)', color='blue', fontsize=12)
ax.tick_params(axis='y', labelcolor='blue')
ax.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.title('Phân bố thời gian hoàn thành', fontsize=14, pad=15)


from matplotlib.patches import Patch
import os
legend_elements = [Patch(facecolor='skyblue', edgecolor='black', label='A*'),
                  Patch(facecolor='lightgreen', edgecolor='black', label='BFS')]
ax.legend(handles=legend_elements, bbox_to_anchor=(0.5, -0.15), 
          loc='upper center', ncol=2, fontsize=10, frameon=True)


plt.tight_layout()
plt.show()