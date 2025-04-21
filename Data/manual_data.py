import matplotlib.pyplot as plt
import json
import os

# Load data from manual_results.json
file_path = os.path.join(os.path.dirname(__file__), "manual_results.json")
with open(file_path, 'r') as file:
    data = json.load(file)

# Extract data for plotting
algorithms = [entry["algorithm"] for entry in data]
times = [entry["time"] for entry in data]
distances = [entry["distance"] for entry in data]

# Create a bar chart for time and distance
fig, ax1 = plt.subplots(figsize=(10, 6))

bar_width = 0.35
x = range(len(algorithms))

# Plot time bars
bars1 = ax1.bar([i - bar_width/2 for i in x], times, 
                bar_width, label='Thời gian (s)', 
                color='skyblue', edgecolor='black')
ax1.set_xlabel('Thuật toán', fontsize=12)
ax1.set_ylabel('Thời gian (s)', color='blue', fontsize=12)
ax1.tick_params(axis='y', labelcolor='blue')
ax1.set_xticks(x)
ax1.set_xticklabels(algorithms, fontsize=11)
ax1.grid(True, axis='y', linestyle='--', alpha=0.7)

# Plot distance bars on a secondary y-axis
ax2 = ax1.twinx()
bars2 = ax2.bar([i + bar_width/2 for i in x], distances, 
                bar_width, label='Khoảng cách', 
                color='lightgreen', edgecolor='black')
ax2.set_ylabel('Khoảng cách', color='green', fontsize=12)
ax2.tick_params(axis='y', labelcolor='green')

# Add value labels to bars
for bar in bars1:
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.1f}', ha='center', va='bottom', color='blue')

for bar in bars2:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{height:.1f}', ha='center', va='bottom', color='green')

# Add title and legend
plt.title('So sánh thời gian và khoảng cách của các thuật toán', fontsize=14, pad=15)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, 
           bbox_to_anchor=(0.5, -0.15), loc='upper center', 
           ncol=2, fontsize=10, frameon=True)

plt.tight_layout()
plt.show()