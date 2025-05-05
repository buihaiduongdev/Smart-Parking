# --- File: pathfinding.py ---
import heapq
from collections import deque, defaultdict # Thêm defaultdict
import time
import random
import math
import numpy as np
from typing import Tuple, List, Set, Optional, Dict, FrozenSet # Thêm Set, Optional, Dict, FrozenSet

# Định nghĩa các kiểu dữ liệu cho rõ ràng
Point = Tuple[int, int]        # (row, col)
Grid = List[List[int]]       # 0 là ô trống, 1 là tường (hoặc số khác nếu có)
Path = List[Point]           # Danh sách các ô tạo thành đường đi
BeliefStatePoint = Set[Point] # Tập hợp các vị trí có thể của tác tử

# === Heuristic ===
def heuristic(a: Point, b: Point) -> float: # Thêm type hints
    """Tính khoảng cách Manhattan giữa hai điểm (row, col)."""
    # Đảm bảo a và b là các tuple (row, col)
    if not (isinstance(a, tuple) and len(a) == 2 and isinstance(b, tuple) and len(b) == 2):
        # print(f"Cảnh báo Heuristic: Input không hợp lệ - a={a}, b={b}")
        return float('inf') # Trả về vô cực nếu input sai
    return float(abs(a[0] - b[0]) + abs(a[1] - b[1])) # Ép kiểu float

# === Helpers ===
def get_neighbors(grid: Grid, node: Point) -> List[Point]: # Thêm type hints
    """Trả về danh sách các ô hàng xóm hợp lệ (ô trống) của một ô."""
    rows, cols = len(grid), len(grid[0])
    neighbors = []
    r, c = node
    # Thứ tự ưu tiên có thể ảnh hưởng nhẹ đến một số thuật toán (DFS, HC)
    # [(0, 1, 'R'), (1, 0, 'D'), (-1, 0, 'U'), (0, -1, 'L')]
    for dr, dc in [(0, 1), (1, 0), (-1, 0), (0, -1)]: # Phải, Dưới, Trên, Trái
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0: # Chỉ đi vào ô trống (0)
            neighbors.append((nr, nc))
    return neighbors

# Hàm helper mới cho Sensorless và Q-Learning để lấy hành động/kết quả
def get_valid_moves(grid: Grid, node: Point) -> List[Tuple[str, Point]]:
    """Trả về danh sách các hành động hợp lệ và trạng thái kết quả."""
    moves = []
    rows, cols = len(grid), len(grid[0])
    r, c = node
    # Lưu ý: Thứ tự hành động có thể quan trọng cho Q-Learning nếu dùng epsilon-greedy tie-breaking
    possible_actions: List[Tuple[int, int, str]] = [(0, 1, 'R'), (1, 0, 'D'), (-1, 0, 'U'), (0, -1, 'L')]
    for dr, dc, action_char in possible_actions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
            moves.append((action_char, (nr, nc)))
    return moves


def reconstruct_path(came_from: Dict[Point, Optional[Point]], current: Point) -> Path: # Thêm type hints
    """Dựng lại đường đi từ dictionary came_from."""
    path = [current]
    while current in came_from and came_from[current] is not None:
        current = came_from[current] # Type hint đảm bảo current là Point
        path.append(current)
    return path[::-1] # Đảo ngược để có thứ tự start -> goal

# === BFS Search ===
def bfs(grid: Grid, start: Point, goal: Point) -> Optional[Path]: # Thêm type hints
    """Tìm kiếm theo chiều rộng."""
    rows, cols = len(grid), len(grid[0])
    q = deque([(start, [start])]) # Hàng đợi lưu (node, path_list)
    visited: Set[Point] = {start} # Sửa type hint
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
def dfs(grid: Grid, start: Point, goal: Point, max_depth: int = 1000) -> Optional[Path]: # Thêm type hints, giới hạn độ sâu
    """Tìm kiếm theo chiều sâu."""
    rows, cols = len(grid), len(grid[0])
    stack: List[Tuple[Point, Path]] = [(start, [start])] # Sửa type hint
    visited: Set[Point] = {start} # Chỉ cần visited để tránh lặp vô hạn cơ bản
    while stack:
        (vertex, path) = stack.pop()
        if vertex == goal:
            return path
        if len(path) > max_depth: # Kiểm tra giới hạn độ sâu
            continue
        # Ưu tiên khám phá sâu hơn (thêm vào stack trước)
        # Đảo ngược để thứ tự khám phá tự nhiên hơn (L-U-D-R nếu get_neighbors là R,D,U,L)
        for neighbor in reversed(get_neighbors(grid, vertex)):
            # Chỉ cần kiểm tra visited tổng thể là đủ cho DFS cơ bản
            # Nếu muốn tránh chu trình trong 1 nhánh thì dùng `if neighbor not in path:`
            if neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, path + [neighbor]))
    return None

# === A* Search ===
def a_star(grid: Grid, start: Point, goal: Point) -> Optional[Path]: # Thêm type hints
    """Thuật toán tìm kiếm A*."""
    open_set: List[Tuple[float, float, Point]] = [] # Sửa type hint (f, g, node)
    heapq.heappush(open_set, (heuristic(start, goal), 0.0, start)) # (f_cost, g_cost, node)
    came_from: Dict[Point, Optional[Point]] = {start: None} # Sửa type hint
    g_score: Dict[Point, float] = {start: 0.0} # Sửa type hint
    # f_score không cần lưu riêng vì có trong heap
    open_set_hash: Set[Point] = {start} # Để kiểm tra nhanh một nút có trong open_set không

    while open_set:
        current_f, current_g, current_node = heapq.heappop(open_set)
        open_set_hash.remove(current_node)

        if current_node == goal:
            return reconstruct_path(came_from, current_node)

        for neighbor in get_neighbors(grid, current_node):
            tentative_g_score = current_g + 1.0 # Chi phí di chuyển là 1
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

# === Simple Hill Climbing ===
def simple_hill_climbing(grid: Grid, start: Point, goal: Point, max_iterations: int = 1000) -> Optional[Path]: # Thêm type hints
    """Leo đồi đơn giản (có thể bị kẹt)."""
    current = start
    path: Path = [current] # Sửa type hint
    iterations = 0
    # visited_branch dùng để tránh quay lại ô vừa đi trong 1 lần leo
    visited_branch: Set[Point] = {start}

    while current != goal and iterations < max_iterations:
        neighbors = get_neighbors(grid, current)
        # Chỉ xét hàng xóm chưa đi qua trong lần leo này
        valid_neighbors = [n for n in neighbors if n not in visited_branch]

        if not valid_neighbors: return None # Bị kẹt nếu ko có hàng xóm hợp lệ

        best_next_node: Optional[Point] = None
        current_h = heuristic(current, goal)
        found_better = False
        random.shuffle(valid_neighbors) # Ngẫu nhiên thứ tự kiểm tra

        for neighbor in valid_neighbors:
            h_neighbor = heuristic(neighbor, goal)
            if h_neighbor < current_h:
                best_next_node = neighbor
                found_better = True
                break # Lấy hàng xóm tốt hơn đầu tiên

        if found_better and best_next_node is not None: # Thêm kiểm tra best_next_node không phải None
            current = best_next_node
            path.append(current)
            visited_branch.add(current) # Đánh dấu đã thăm trong lần leo này
            # Có thể reset visited_branch ở đây nếu muốn cho phép quay lại ô cũ sau khi đã tiến lên
        else:
            return None # Bị kẹt ở cực tiểu địa phương hoặc bình nguyên

        iterations += 1
        if current == goal: return path

    return path if current == goal else None


# === Backtracking ===
def backtracking(grid: Grid, start: Point, goal: Point, max_depth: int = 500, max_time_ms: int = 2000) -> Optional[Path]: # Thêm type hints
    """Tìm kiếm quay lui (DFS với kiểm tra chu trình trên path và giới hạn thời gian)."""
    start_time = time.time()  # Lưu thời gian bắt đầu
    stack: List[Tuple[Point, Path]] = [(start, [start])]  # (current_node, path_list)

    while stack:
        # Kiểm tra thời gian chạy
        elapsed_time_ms = (time.time() - start_time) * 1000
        if elapsed_time_ms > max_time_ms:
            print("Backtracking: Timeout reached!")
            return None

        (vertex, path) = stack.pop()

        if vertex == goal:
            return path

        # Kiểm tra giới hạn độ sâu
        if len(path) > max_depth:
            continue

        # Khám phá hàng xóm (đảo ngược để hợp với stack pop)
        for neighbor in reversed(get_neighbors(grid, vertex)):
            # Chỉ cần kiểm tra neighbor không nằm trong path hiện tại để tránh chu trình
            if neighbor not in path:
                stack.append((neighbor, path + [neighbor]))

    return None


# === Sensorless Search (BFS on Belief States for Grid) ===
def sensorless_search(grid: Grid, initial_belief_state: BeliefStatePoint, goal: Point, max_time_ms: int = 5000) -> Optional[List[str]]: # Trả về chuỗi hành động 'U', 'D', 'L', 'R'
    """Tìm một chuỗi hành động để đạt đích từ bất kỳ trạng thái nào trong belief state ban đầu."""
    start_time = time.time()

    # Kiểm tra input cơ bản
    if not initial_belief_state:
        print("Sensorless Search: Belief state ban đầu rỗng.")
        return None
    if goal in initial_belief_state and len(initial_belief_state) == 1:
        return [] # Đã ở đích

    rows, cols = len(grid), len(grid[0] )

    # Hàng đợi lưu (chuoi_hanh_dong, current_belief_state)
    # Dùng frozenset cho belief state để có thể hash và lưu trong visited
    queue: deque[Tuple[str, FrozenSet[Point]]] = deque([("", frozenset(initial_belief_state))])
    visited: Set[FrozenSet[Point]] = {frozenset(initial_belief_state)}

    possible_actions = ['U', 'D', 'L', 'R']
    action_deltas = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}

    while queue:
        # Kiểm tra thời gian
        elapsed_time_ms = (time.time() - start_time) * 1000
        if elapsed_time_ms > max_time_ms:
            print("Sensorless Search: Timeout reached!")
            return None

        action_path_str, current_belief_frozen = queue.popleft()
        current_belief = set(current_belief_frozen) # Chuyển lại thành set để xử lý

        # Kiểm tra xem tất cả các trạng thái trong belief state hiện tại có phải là đích không
        if all(node == goal for node in current_belief):
            return list(action_path_str) # Trả về list các ký tự hành động

        # Thử áp dụng từng hành động có thể ('U', 'D', 'L', 'R')
        for action_char in possible_actions:
            next_belief: BeliefStatePoint = set()
            dr, dc = action_deltas[action_char]

            # Tính toán belief state kết quả khi thực hiện hành động 'action_char'
            for r, c in current_belief:
                nr, nc = r + dr, c + dc
                # Nếu hành động hợp lệ (trong lưới và không phải tường)
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                    next_belief.add((nr, nc)) # Thêm trạng thái kết quả
                else:
                    next_belief.add((r, c)) # Nếu không di chuyển được, tác tử vẫn ở vị trí cũ

            # Nếu belief state kết quả không rỗng và chưa được thăm
            if next_belief:
                frozen_next_belief = frozenset(next_belief)
                if frozen_next_belief not in visited:
                    visited.add(frozen_next_belief)
                    queue.append((action_path_str + action_char, frozen_next_belief))

    print("Sensorless Search: Không tìm thấy kế hoạch phù hợp.")
    return None

# === Q-Learning (Simple Tabular Version for Grid Pathfinding) ===
def q_learning_pathfinding(
    grid: Grid, start: Point, goal: Point,
    episodes: int = 5000,         # Số lượt huấn luyện
    alpha: float = 0.1,          # Tốc độ học
    gamma: float = 0.9,          # Hệ số chiết khấu
    epsilon_start: float = 0.9,  # Epsilon ban đầu (cao để khám phá)
    epsilon_end: float = 0.05, # Epsilon cuối cùng (thấp để khai thác)
    epsilon_decay: float = 0.999,# Tốc độ giảm epsilon
    max_steps_episode: int = 200,# Giới hạn bước trong 1 episode huấn luyện
    max_steps_solve: int = 500   # Giới hạn bước khi trích xuất đường đi
) -> Optional[Path]:
    """Học đường đi bằng Q-Learning và trả về path."""
    print(f"Q-Learning: Bắt đầu huấn luyện ({episodes} episodes)...")
    training_start_time = time.time()
    rows, cols = len(grid), len(grid[0])

    # Q-table: Dict[Point, Dict[str, float]] -> Q(state, action)
    q_table: Dict[Point, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    epsilon = epsilon_start

    # --- Pha Huấn Luyện ---
    for episode in range(episodes):
        current_pos = start
        if episode % (episodes // 10) == 0 and episode > 0: # In tiến độ
             print(f"  Q-Learning Episode {episode}/{episodes}, Epsilon: {epsilon:.3f}")

        for _ in range(max_steps_episode):
            if current_pos == goal:
                break # Đạt đích trong episode này

            valid_moves = get_valid_moves(grid, current_pos)
            if not valid_moves: break # Bị kẹt

            action: str
            next_pos: Point

            # Chọn hành động (Epsilon-Greedy)
            if random.random() < epsilon:
                action, next_pos = random.choice(valid_moves) # Khám phá
            else:
                # Khai thác: chọn hành động có Q-value cao nhất
                best_q = -float('inf')
                best_actions = []
                for act, next_state in valid_moves:
                    q_val = q_table[current_pos][act]
                    if q_val > best_q:
                        best_q = q_val
                        best_actions = [(act, next_state)]
                    elif q_val == best_q:
                        best_actions.append((act, next_state))

                if not best_actions: # Chưa có giá trị nào, chọn ngẫu nhiên
                    action, next_pos = random.choice(valid_moves)
                else: # Chọn ngẫu nhiên trong các hành động tốt nhất
                    action, next_pos = random.choice(best_actions)

            # --- Cập nhật Q-value ---
            # Phần thưởng: cao khi đến đích, nhỏ (âm) khi di chuyển
            reward = -0.1 # Phạt nhẹ để khuyến khích đường ngắn
            if next_pos == goal:
                reward = 100.0 # Phần thưởng lớn khi đến đích

            # Tìm max Q-value của trạng thái kế tiếp
            max_next_q = 0.0
            if next_pos != goal:
                next_state_moves = get_valid_moves(grid, next_pos)
                if next_state_moves:
                    q_values_next = [q_table[next_pos][act] for act, _ in next_state_moves]
                    if q_values_next:
                        max_next_q = max(q_values_next)

            # Công thức cập nhật Q-Learning
            old_q = q_table[current_pos][action]
            new_q = old_q + alpha * (reward + gamma * max_next_q - old_q)
            q_table[current_pos][action] = new_q

            current_pos = next_pos # Di chuyển đến trạng thái mới

        # Giảm Epsilon
        if epsilon > epsilon_end:
            epsilon *= epsilon_decay

    training_end_time = time.time()
    print(f"Q-Learning: Huấn luyện xong sau {training_end_time - training_start_time:.2f}s.")
    print("Q-Learning: Trích xuất đường đi...")

    # --- Pha Trích Xuất Đường Đi (Khai thác) ---
    path: Path = [start]
    current_pos = start
    visited_solve: Set[Point] = {start} # Tránh lặp trong lúc giải

    for _ in range(max_steps_solve):
        if current_pos == goal:
            print("Q-Learning: Tìm thấy đường đi!")
            return path # Trả về path nếu đến đích

        valid_moves = get_valid_moves(grid, current_pos)
        if not valid_moves:
            print("Q-Learning: Bị kẹt khi trích xuất đường đi (không có bước đi hợp lệ).")
            return None # Bị kẹt

        # Chọn hành động tốt nhất (không khám phá nữa)
        best_q = -float('inf')
        best_action: Optional[str] = None
        next_pos_from_best_action: Optional[Point] = None

        possible_next_actions = []
        for act, next_state in valid_moves:
             q_val = q_table[current_pos].get(act, 0.0) # Lấy Q-value, mặc định là 0
             possible_next_actions.append((q_val, act, next_state))

        if not possible_next_actions: # Vẫn nên kiểm tra lại
            print("Q-Learning: Bị kẹt khi trích xuất đường đi (lỗi logic?).")
            return None

        # Sắp xếp theo Q-value giảm dần, nếu bằng nhau thì ngẫu nhiên
        random.shuffle(possible_next_actions) # Ngẫu nhiên trước khi sort để phá vỡ thế cân bằng
        possible_next_actions.sort(key=lambda item: item[0], reverse=True)

        # Lấy hành động tốt nhất
        best_q_val, best_action, next_pos_from_best_action = possible_next_actions[0]

        # Kiểm tra nếu hành động tốt nhất dẫn đến ô đã thăm -> có thể bị lặp
        if next_pos_from_best_action in visited_solve:
             # Thử hành động tốt thứ 2 nếu có và không bị lặp
             if len(possible_next_actions) > 1 and possible_next_actions[1][2] not in visited_solve:
                  print(f"Q-Learning: Tránh lặp, chọn hành động tốt thứ 2 từ {current_pos}")
                  _, best_action, next_pos_from_best_action = possible_next_actions[1]
             else:
                  print(f"Q-Learning: Bị kẹt trong vòng lặp khi trích xuất đường đi tại {current_pos}.")
                  # Có thể thử cho phép đi vào ô đã thăm 1 lần? Hoặc báo lỗi.
                  # Hiện tại: báo lỗi
                  return None # Bị kẹt trong lặp

        # Di chuyển
        current_pos = next_pos_from_best_action
        path.append(current_pos)
        visited_solve.add(current_pos)


    print(f"Q-Learning: Không tìm thấy đường đi trong giới hạn {max_steps_solve} bước.")
    return None # Không tìm thấy đường trong giới hạn bước


# === Các hàm tiện ích khác nếu cần ===
def count_turns(path: Optional[Path]) -> int: # Thêm type hints
    """Đếm số lần rẽ trong đường đi (dạng list các ô)."""
    if not path or len(path) < 3: return 0
    turns = 0
    # Tính hướng cho đoạn đầu tiên (kiểm tra path[1] tồn tại)
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


# Ví dụ sử dụng (có thể bỏ đi khi tích hợp vào main)
if __name__ == '__main__':
    # Tạo grid mẫu (0: trống, 1: tường)
    grid_example = [
        [0, 0, 0, 0, 1, 0, 0, 0],
        [0, 1, 1, 0, 1, 0, 1, 0],
        [0, 1, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 1, 1, 1, 1, 0],
        [1, 1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 1, 1, 1, 1],
        [0, 1, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 1, 1, 0, 0],
    ]
    start_point: Point = (0, 0)
    goal_point: Point = (7, 7)

    print("--- Thử nghiệm Sensorless Search ---")
    # Giả sử ban đầu không chắc chắn vị trí, có thể là (0,0) hoặc (0,1)
    initial_belief: BeliefStatePoint = {(0, 0), (0, 1)}
    sensorless_plan = sensorless_search(grid_example, initial_belief, goal_point)
    if sensorless_plan:
        print(f"Sensorless Plan tìm được: {''.join(sensorless_plan)} (Độ dài: {len(sensorless_plan)})")
    else:
        print("Sensorless Search không tìm được kế hoạch.")

    print("\n--- Thử nghiệm Q-Learning ---")
    q_path = q_learning_pathfinding(grid_example, start_point, goal_point, episodes=10000) # Tăng episodes
    if q_path:
        print(f"Q-Learning Path tìm được (độ dài {len(q_path)}):")
        # print(q_path)
    else:
        print("Q-Learning không tìm được đường đi.")

    print("\n--- Thử nghiệm A* để so sánh ---")
    astar_path = a_star(grid_example, start_point, goal_point)
    if astar_path:
         print(f"A* Path tìm được (độ dài {len(astar_path)}):")
         # print(astar_path)
    else:
         print("A* không tìm được đường đi.")