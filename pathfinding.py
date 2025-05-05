# --- File: pathfinding.py ---
import heapq
from collections import deque
import time
import random
import math
import numpy as np

# === Heuristic ===
def heuristic(a, b):
    """Tính khoảng cách Manhattan giữa hai điểm (row, col)."""
    # Đảm bảo a và b là các tuple (row, col)
    if not (isinstance(a, tuple) and len(a) == 2 and isinstance(b, tuple) and len(b) == 2):
        # print(f"Cảnh báo Heuristic: Input không hợp lệ - a={a}, b={b}")
        return float('inf') # Trả về vô cực nếu input sai
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# === Helpers ===
def get_neighbors(grid, node):
    """Trả về danh sách các ô hàng xóm hợp lệ (ô trống) của một ô."""
    rows, cols = len(grid), len(grid[0])
    neighbors = []
    r, c = node
    for dr, dc in [(0, 1), (1, 0), (-1, 0), (0, -1)]: # Phải, Dưới, Trên, Trái
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
            neighbors.append((nr, nc))
    return neighbors

def reconstruct_path(came_from, current):
    """Dựng lại đường đi từ dictionary came_from."""
    path = [current]
    while current in came_from and came_from[current] is not None:
        current = came_from[current]
        path.append(current)
    return path[::-1] # Đảo ngược để có thứ tự start -> goal

# === BFS Search ===
def bfs(grid, start, goal):
    """Tìm kiếm theo chiều rộng."""
    rows, cols = len(grid), len(grid[0])
    q = deque([(start, [start])]) # Hàng đợi lưu (node, path_list)
    visited = {start}
    while q:
        (vertex, path) = q.popleft()
        if vertex == goal:
            return path # Trả về danh sách các ô
        for neighbor in get_neighbors(grid, vertex):
            if neighbor not in visited:
                visited.add(neighbor)
                q.append((neighbor, path + [neighbor]))
    return None # Không tìm thấy đường

# === DFS Search ===
def dfs(grid, start, goal, max_depth=1000): # Thêm giới hạn độ sâu cho DFS
    """Tìm kiếm theo chiều sâu."""
    rows, cols = len(grid), len(grid[0])
    stack = [(start, [start])] # Stack lưu (node, path_list)
    visited = {start} # Chỉ cần visited để tránh lặp vô hạn cơ bản
    while stack:
        (vertex, path) = stack.pop()
        if vertex == goal:
            return path
        if len(path) > max_depth: # Kiểm tra giới hạn độ sâu
            continue
        # Ưu tiên khám phá sâu hơn (thêm vào stack trước)
        for neighbor in reversed(get_neighbors(grid, vertex)):
             # Chỉ cần kiểm tra visited tổng thể là đủ cho DFS cơ bản
             # Nếu muốn tránh chu trình trong 1 nhánh thì dùng `if neighbor not in path:`
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, path + [neighbor]))
    return None

# === A* Search ===
def a_star(grid, start, goal):
    """Thuật toán tìm kiếm A*."""
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), 0, start)) # (f_cost, g_cost, node)
    came_from = {start: None}
    g_score = {start: 0}
    # f_score không cần lưu riêng vì có trong heap
    open_set_hash = {start} # Để kiểm tra nhanh một nút có trong open_set không

    while open_set:
        current_f, current_g, current_node = heapq.heappop(open_set)
        open_set_hash.remove(current_node)

        if current_node == goal:
            return reconstruct_path(came_from, current_node)

        for neighbor in get_neighbors(grid, current_node):
            tentative_g_score = current_g + 1 # Chi phí di chuyển là 1
            current_neighbor_g = g_score.get(neighbor, float('inf'))

            if tentative_g_score < current_neighbor_g:
                # Tìm thấy đường tốt hơn đến neighbor
                came_from[neighbor] = current_node
                g_score[neighbor] = tentative_g_score
                f_neighbor = tentative_g_score + heuristic(neighbor, goal)
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_neighbor, tentative_g_score, neighbor))
                    open_set_hash.add(neighbor)
                # Nếu neighbor đã có trong open_set với f_score cao hơn,
                # heapq sẽ tự động ưu tiên cái mới có f_score thấp hơn khi pop.

    return None

# === IDDFS ===
def dls(grid, node, goal, path, limit):
    """Depth Limited Search - Hàm hỗ trợ cho IDDFS."""
    if node == goal:
        return path
    if limit <= 0:
        return None
    for neighbor in get_neighbors(grid, node):
        if neighbor not in path: # Tránh chu trình trong nhánh hiện tại
            found_path = dls(grid, neighbor, goal, path + [neighbor], limit - 1)
            if found_path:
                return found_path
    return None

def iddfs(grid, start, goal, max_depth=10):
    """Iterative Deepening Depth First Search."""
    print(f"Running IDDFS with max_depth={max_depth}")
    for depth in range(max_depth + 1):
        # print(f"  IDDFS: Trying depth {depth}") # Debug
        result = dls(grid, start, goal, [start], depth)
        if result:
            print(f"  IDDFS: Path found at depth {depth}")
            return result
    print(f"  IDDFS: No path found within depth {max_depth}")
    return None

# === Greedy Best-First Search ===
def greedy_bfs(grid, start, goal):
    """Tìm kiếm Tham lam Tốt nhất đầu tiên."""
    open_set = []
    heapq.heappush(open_set, (heuristic(start, goal), start)) # (h_cost, node)
    came_from = {start: None}
    visited = {start} # Greedy thường không quay lại nút đã thăm

    while open_set:
        _, current_node = heapq.heappop(open_set)

        if current_node == goal:
            return reconstruct_path(came_from, current_node)

        for neighbor in get_neighbors(grid, current_node):
            if neighbor not in visited: # Chỉ xét nút chưa thăm
                visited.add(neighbor)
                came_from[neighbor] = current_node
                h_cost = heuristic(neighbor, goal)
                heapq.heappush(open_set, (h_cost, neighbor))

    return None

# === Simple Hill Climbing ===
def simple_hill_climbing(grid, start, goal, max_iterations=1000):
    """Leo đồi đơn giản (có thể bị kẹt)."""
    current = start
    path = [current]
    iterations = 0
    visited_branch = {start} # Chỉ tránh lặp lại trong nhánh leo đồi hiện tại

    while current != goal and iterations < max_iterations:
        neighbors = get_neighbors(grid, current)
        valid_neighbors = [n for n in neighbors if n not in visited_branch]

        if not valid_neighbors: return None # Bị kẹt

        best_next_node = None
        current_h = heuristic(current, goal)
        found_better = False
        random.shuffle(valid_neighbors) # Ngẫu nhiên thứ tự kiểm tra

        for neighbor in valid_neighbors:
            h_neighbor = heuristic(neighbor, goal)
            if h_neighbor < current_h:
                best_next_node = neighbor
                found_better = True
                break # Lấy hàng xóm tốt hơn đầu tiên

        if found_better:
            current = best_next_node
            path.append(current)
            visited_branch.add(current) # Đánh dấu đã thăm trong lần leo này
        else:
            return None # Bị kẹt ở cực tiểu địa phương

        iterations += 1
        if current == goal: return path

    return path if current == goal else None


# === Genetic Algorithm ===
def genetic_algorithm(grid, start, goal, population_size=50, generations=100, mutation_rate=0.1, elite_size=2):
    """Thuật toán Di truyền tìm trạng thái đích, sau đó dùng A* tìm đường."""
    ga_start_time = time.perf_counter()
    print("Starting GA to find goal state...")
    rows, cols = len(grid), len(grid[0])

    def fitness(state_tuple, target_goal=goal):
        h = heuristic(state_tuple, target_goal)
        # Tránh chia cho 0 nếu heuristic là 0 (đã đến đích)
        return 1.0 / (1.0 + h) if h > -1 else float('inf') # Hoặc một giá trị rất lớn

    def mutate(state_tuple):
        neighbors = get_neighbors(grid, state_tuple)
        return random.choice(neighbors) if neighbors else state_tuple

    # --- Khởi tạo quần thể (Đã sửa) ---
    population = {start}
    valid_cells = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 0 and (r, c) != start]
    needed = population_size - len(population)
    count_to_add = min(needed, len(valid_cells))
    if count_to_add > 0:
        random_sample = random.sample(valid_cells, count_to_add)
        population.update(random_sample)
    print(f"Initialized GA population with {len(population)} individuals.")
    if len(population) < population_size:
         print(f"Warning: Could only initialize {len(population)}/{population_size} individuals.")

    best_state_overall = start
    best_fitness_overall = fitness(start)
    goal_found_in_ga = False

    # --- Vòng lặp tiến hóa ---
    for gen in range(generations):
        # Thêm kiểm tra nếu quần thể rỗng (ít khi xảy ra)
        if not population:
             print("GA Error: Population became empty.")
             break

        pop_with_fitness = []
        for state in population:
             fit_val = fitness(state)
             # Bỏ qua trạng thái không hợp lệ (heuristic trả về inf)
             if fit_val != float('inf'):
                  pop_with_fitness.append((fit_val, state))

        if not pop_with_fitness: # Nếu tất cả trạng thái lỗi
             print("GA Error: All individuals have invalid fitness.")
             break

        pop_with_fitness.sort(reverse=True, key=lambda x: x[0])

        # Kiểm tra heuristic = 0 (vì fitness có thể không chính xác 1.0 do float)
        current_best_h = heuristic(pop_with_fitness[0][1], goal)
        if current_best_h == 0:
            best_state_overall = pop_with_fitness[0][1]
            goal_found_in_ga = True
            print(f"GA found goal state in generation {gen}.")
            break

        current_gen_best_fitness, current_gen_best_state = pop_with_fitness[0]
        if current_gen_best_fitness > best_fitness_overall:
            best_fitness_overall = current_gen_best_fitness
            best_state_overall = current_gen_best_state

        new_population = set()
        # Đảm bảo elite_size không lớn hơn kích thước quần thể hiện tại
        actual_elite_size = min(elite_size, len(pop_with_fitness))
        elites = {state for _, state in pop_with_fitness[:actual_elite_size]}
        new_population.update(elites)

        # Lấy danh sách trạng thái hợp lệ từ pop_with_fitness
        population_list = [state for _, state in pop_with_fitness]
        if not population_list: continue # Nếu không có cá thể nào hợp lệ để chọn

        while len(new_population) < population_size:
            # Chọn lọc đơn giản
            p1 = random.choice(population_list)
            p2 = random.choice(population_list)
            parent = p1 if fitness(p1) >= fitness(p2) else p2 # Cần đảm bảo fitness hợp lệ

            # Đột biến
            offspring = mutate(parent) if random.random() < mutation_rate else parent
            new_population.add(offspring)

        population = new_population
        population.add(best_state_overall) # Giữ cá thể tốt nhất
        while len(population) > population_size: population.pop() # Giữ kích thước

    ga_end_time = time.perf_counter()

    # --- Gọi A* để tìm đường ---
    final_path_result = None # Kết quả cuối cùng
    if best_state_overall == goal or goal_found_in_ga:
        print("GA confirmed goal state. Searching for path using A*...")
        astar_start_time = time.perf_counter()
        astar_path_result = a_star(grid, start, goal) # Tìm đường từ start gốc đến goal
        astar_end_time = time.perf_counter()
        astar_time = astar_end_time - astar_start_time

        if astar_path_result:
            print(f"A* found path in {astar_time:.4f}s.")
            final_path_result = astar_path_result
        else:
            print(f"Warning: GA found goal, but A* failed to find path.")
            final_path_result = None
    else:
        print("GA did not find the goal state within generations limit.")
        final_path_result = None

    return final_path_result # Chỉ trả về path hoặc None


# === Backtracking ===
def backtracking(grid, start, goal, max_depth=500, max_time_ms=2000):
    """Tìm kiếm quay lui (DFS với kiểm tra chu trình trên path)."""
    start_time = time.time()  # Lưu thời gian bắt đầu
    stack = [(start, [start])]  # (current_node, path_list)

    while stack:
        # Kiểm tra thời gian chạy
        elapsed_time_ms = (time.time() - start_time) * 1000
        if elapsed_time_ms > max_time_ms:
            print("Backtracking: Timeout reached!")
            return None

        (vertex, path) = stack.pop()

        if vertex == goal:
            return path

        if len(path) > max_depth:
            continue

        for neighbor in reversed(get_neighbors(grid, vertex)):
            if neighbor not in path:  # Tránh chu trình trong đường đi hiện tại
                stack.append((neighbor, path + [neighbor]))

    return None


# === Q-Learning Pathfinder ===
def q_learning_pathfinder(grid, start, goal, q_table_file="q_table.npy", max_steps=1000):
    """Tìm đường đi bằng Q-table đã huấn luyện (Cần file .npy)."""
    print("Attempting Q-Learning pathfinder...")
    rows, cols = len(grid), len(grid[0])
    state_size = rows * cols; action_size = 4 # U, D, L, R (giả định)

    def state_to_index(r, c): return r * cols + c
    # Định nghĩa action_map và index cẩn thận
    # Hành động: 0: Lên (-1, 0), 1: Xuống (1, 0), 2: Trái (0, -1), 3: Phải (0, 1)
    action_map = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1)}
    action_indices = {v: k for k, v in action_map.items()} # (dr, dc) -> index

    try:
        q_table = np.load(q_table_file)
        if q_table.shape != (state_size, action_size):
             print(f"Lỗi: Q-table shape {q_table.shape} != expected {(state_size, action_size)}"); return None
        print(f"Loaded Q-table từ {q_table_file}")
    except FileNotFoundError: print(f"Lỗi: Không tìm thấy Q-table '{q_table_file}'. Cần huấn luyện trước."); return None
    except Exception as e: print(f"Lỗi load Q-table: {e}"); return None

    path = [start]; current_node = start; steps = 0; visited_ql = {start}

    while current_node != goal and steps < max_steps:
        current_state_idx = state_to_index(current_node[0], current_node[1])
        valid_neighbors = get_neighbors(grid, current_node)
        if not valid_neighbors: break # Kẹt

        possible_actions_details = [] # List of (q_value, action_index, neighbor_node)
        for neighbor in valid_neighbors:
            dr, dc = neighbor[0] - current_node[0], neighbor[1] - current_node[1]
            move = (dr, dc)
            if move in action_indices:
                action_idx = action_indices[move]
                q_value = q_table[current_state_idx, action_idx]
                possible_actions_details.append((q_value, action_idx, neighbor))

        if not possible_actions_details: break # Không có hành động hợp lệ nào?

        # Sắp xếp theo Q-value giảm dần và chọn hành động tốt nhất
        possible_actions_details.sort(key=lambda x: x[0], reverse=True)
        best_q_value = possible_actions_details[0][0]

        # Lấy tất cả các hành động có Q-value tốt nhất (để xử lý tie-breaking)
        best_options = [opt for opt in possible_actions_details if opt[0] >= best_q_value - 1e-6] # So sánh float

        # Chọn ngẫu nhiên một trong các hành động tốt nhất
        _, chosen_action_idx, next_node = random.choice(best_options)

        if next_node in visited_ql: return None # Phát hiện chu trình

        path.append(next_node); visited_ql.add(next_node); current_node = next_node; steps += 1

    return path if current_node == goal else None

# === Các hàm tiện ích khác nếu cần ===
def count_turns(path):
    """Đếm số lần rẽ trong đường đi (dạng list các ô)."""
    if not path or len(path) < 3: return 0
    turns = 0
    # Tính hướng cho đoạn đầu tiên
    dx1, dy1 = path[1][1] - path[0][1], path[1][0] - path[0][0]
    prev_dir = (dx1, dy1)

    for i in range(1, len(path) - 1):
        # Tính hướng cho đoạn hiện tại
        dx2, dy2 = path[i+1][1] - path[i][1], path[i+1][0] - path[i][0]
        curr_dir = (dx2, dy2)
        # So sánh hướng (bỏ qua trường hợp đứng yên nếu có)
        if curr_dir != (0, 0) and prev_dir != (0, 0) and curr_dir != prev_dir:
            turns += 1
        if curr_dir != (0,0): # Cập nhật hướng trước đó nếu không đứng yên
            prev_dir = curr_dir
    return turns

# --- Lớp QLearning để huấn luyện (có thể nằm riêng) ---
class QLearningTrainer: # Đổi tên để phân biệt với hàm pathfinder
    def __init__(self, state_size, action_size, learning_rate=0.1, discount_factor=0.9, exploration_rate=1.0, exploration_decay=0.99, min_exploration_rate=0.01):
        self.state_size = state_size; self.action_size = action_size
        self.lr = learning_rate; self.gamma = discount_factor
        self.epsilon = exploration_rate; self.epsilon_decay = exploration_decay; self.epsilon_min = min_exploration_rate
        self.q_table = np.zeros((state_size, action_size))
        # Định nghĩa action_map ở đây để nhất quán
        # 0: Lên, 1: Xuống, 2: Trái, 3: Phải
        self.action_map = {0: (-1, 0), 1: (1, 0), 2: (0, -1), 3: (0, 1)}

    def choose_action(self, state_index, valid_actions_indices):
        """Chọn hành động dùng epsilon-greedy trong tập các hành động hợp lệ."""
        if not valid_actions_indices: return None # Không có hành động nào
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(valid_actions_indices) # Khám phá
        else:
            # Khai thác: Chọn hành động hợp lệ có Q-value cao nhất
            q_values = self.q_table[state_index, valid_actions_indices]
            best_local_index = np.argmax(q_values)
            return valid_actions_indices[best_local_index] # Trả về global action index

    def update(self, state_index, action_index, reward, next_state_index):
        """Cập nhật Q-table."""
        best_next_q = np.max(self.q_table[next_state_index]) # Q-value tốt nhất của trạng thái kế tiếp
        td_target = reward + self.gamma * best_next_q
        td_error = td_target - self.q_table[state_index, action_index]
        self.q_table[state_index, action_index] += self.lr * td_error

    def decay_exploration(self):
        """Giảm exploration rate."""
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
            self.epsilon = max(self.epsilon_min, self.epsilon) # Đảm bảo không nhỏ hơn min

    def save_q_table(self, filename="q_table.npy"):
        np.save(filename, self.q_table)
        print(f"Q-table saved to {filename}")

    def load_q_table(self, filename="q_table.npy"):
         try:
              self.q_table = np.load(filename)
              # Kiểm tra kích thước nếu cần
              if self.q_table.shape != (self.state_size, self.action_size):
                   print(f"Cảnh báo: Kích thước Q-table tải lên {self.q_table.shape} không khớp mong đợi {(self.state_size, self.action_size)}. Có thể gây lỗi.")
              print(f"Q-table loaded from {filename}")
         except FileNotFoundError: print(f"Lỗi: Không tìm thấy file Q-table {filename}.")
         except Exception as e: print(f"Lỗi khi tải Q-table: {e}")

# Bạn sẽ cần một hàm riêng để chạy quá trình huấn luyện Q-Learning
# Ví dụ: def train_q_learning(grid, episodes, ...) -> QLearningTrainer: ...