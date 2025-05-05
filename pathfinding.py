import heapq
from collections import deque, defaultdict 
import time
import random
import math
import numpy as np
from typing import Tuple, List, Set, Optional, Dict, FrozenSet 

Point = Tuple[int, int]        
Grid = List[List[int]]       
Path = List[Point]           
BeliefStatePoint = Set[Point] 

def heuristic(a: Point, b: Point) -> float: 
    """Tính khoảng cách Manhattan giữa hai điểm (row, col)."""

    if not (isinstance(a, tuple) and len(a) == 2 and isinstance(b, tuple) and len(b) == 2):

        return float('inf') 
    return float(abs(a[0] - b[0]) + abs(a[1] - b[1])) 

def get_neighbors(grid: Grid, node: Point) -> List[Point]: 
    """Trả về danh sách các ô hàng xóm hợp lệ (ô trống) của một ô."""
    rows, cols = len(grid), len(grid[0])
    neighbors = []
    r, c = node

    for dr, dc in [(0, 1), (1, 0), (-1, 0), (0, -1)]: 
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0: 
            neighbors.append((nr, nc))
    return neighbors

def get_valid_moves(grid: Grid, node: Point) -> List[Tuple[str, Point]]:
    """Trả về danh sách các hành động hợp lệ và trạng thái kết quả."""
    moves = []
    rows, cols = len(grid), len(grid[0])
    r, c = node

    possible_actions: List[Tuple[int, int, str]] = [(0, 1, 'R'), (1, 0, 'D'), (-1, 0, 'U'), (0, -1, 'L')]
    for dr, dc, action_char in possible_actions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
            moves.append((action_char, (nr, nc)))
    return moves

def reconstruct_path(came_from: Dict[Point, Optional[Point]], current: Point) -> Path: 
    """Dựng lại đường đi từ dictionary came_from."""
    path = [current]
    while current in came_from and came_from[current] is not None:
        current = came_from[current] 
        path.append(current)
    return path[::-1] 

def bfs(grid: Grid, start: Point, goal: Point) -> Optional[Path]: 
    """Tìm kiếm theo chiều rộng."""
    rows, cols = len(grid), len(grid[0])
    q = deque([(start, [start])]) 
    visited: Set[Point] = {start} 
    while q:
        (vertex, path) = q.popleft()
        if vertex == goal:
            return path 
        for neighbor in get_neighbors(grid, vertex):
            if neighbor not in visited:
                visited.add(neighbor)
                q.append((neighbor, path + [neighbor]))
    return None 

def dfs(grid: Grid, start: Point, goal: Point, max_depth: int = 1000) -> Optional[Path]: 
    """Tìm kiếm theo chiều sâu."""
    rows, cols = len(grid), len(grid[0])
    stack: List[Tuple[Point, Path]] = [(start, [start])] 
    visited: Set[Point] = {start} 
    while stack:
        (vertex, path) = stack.pop()
        if vertex == goal:
            return path
        if len(path) > max_depth: 
            continue

        for neighbor in reversed(get_neighbors(grid, vertex)):

            if neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, path + [neighbor]))
    return None

def a_star(grid: Grid, start: Point, goal: Point) -> Optional[Path]: 
    """Thuật toán tìm kiếm A*."""
    open_set: List[Tuple[float, float, Point]] = [] 
    heapq.heappush(open_set, (heuristic(start, goal), 0.0, start)) 
    came_from: Dict[Point, Optional[Point]] = {start: None} 
    g_score: Dict[Point, float] = {start: 0.0} 

    open_set_hash: Set[Point] = {start} 

    while open_set:
        current_f, current_g, current_node = heapq.heappop(open_set)
        open_set_hash.remove(current_node)

        if current_node == goal:
            return reconstruct_path(came_from, current_node)

        for neighbor in get_neighbors(grid, current_node):
            tentative_g_score = current_g + 1.0 
            current_neighbor_g = g_score.get(neighbor, float('inf'))

            if tentative_g_score < current_neighbor_g:

                came_from[neighbor] = current_node
                g_score[neighbor] = tentative_g_score
                f_neighbor = tentative_g_score + heuristic(neighbor, goal)
                if neighbor not in open_set_hash:
                    heapq.heappush(open_set, (f_neighbor, tentative_g_score, neighbor))
                    open_set_hash.add(neighbor)

    return None

def simple_hill_climbing(grid: Grid, start: Point, goal: Point, max_iterations: int = 1000) -> Optional[Path]: 
    """Leo đồi đơn giản (có thể bị kẹt)."""
    current = start
    path: Path = [current] 
    iterations = 0

    visited_branch: Set[Point] = {start}

    while current != goal and iterations < max_iterations:
        neighbors = get_neighbors(grid, current)

        valid_neighbors = [n for n in neighbors if n not in visited_branch]

        if not valid_neighbors: return None 

        best_next_node: Optional[Point] = None
        current_h = heuristic(current, goal)
        found_better = False
        random.shuffle(valid_neighbors) 

        for neighbor in valid_neighbors:
            h_neighbor = heuristic(neighbor, goal)
            if h_neighbor < current_h:
                best_next_node = neighbor
                found_better = True
                break 

        if found_better and best_next_node is not None: 
            current = best_next_node
            path.append(current)
            visited_branch.add(current) 

        else:
            return None 

        iterations += 1
        if current == goal: return path

    return path if current == goal else None

def backtracking(grid: Grid, start: Point, goal: Point, max_depth: int = 500, max_time_ms: int = 2000) -> Optional[Path]: 
    """Tìm kiếm quay lui (DFS với kiểm tra chu trình trên path và giới hạn thời gian)."""
    start_time = time.time()  
    stack: List[Tuple[Point, Path]] = [(start, [start])]  

    while stack:

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

            if neighbor not in path:
                stack.append((neighbor, path + [neighbor]))

    return None

def sensorless_search(grid: Grid, initial_belief_state: BeliefStatePoint, goal: Point, max_time_ms: int = 5000) -> Optional[List[str]]: 
    """Tìm một chuỗi hành động để đạt đích từ bất kỳ trạng thái nào trong belief state ban đầu."""
    start_time = time.time()

    if not initial_belief_state:
        print("Sensorless Search: Belief state ban đầu rỗng.")
        return None
    if goal in initial_belief_state and len(initial_belief_state) == 1:
        return [] 

    rows, cols = len(grid), len(grid[0] )

    queue: deque[Tuple[str, FrozenSet[Point]]] = deque([("", frozenset(initial_belief_state))])
    visited: Set[FrozenSet[Point]] = {frozenset(initial_belief_state)}

    possible_actions = ['U', 'D', 'L', 'R']
    action_deltas = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}

    while queue:

        elapsed_time_ms = (time.time() - start_time) * 1000
        if elapsed_time_ms > max_time_ms:
            print("Sensorless Search: Timeout reached!")
            return None

        action_path_str, current_belief_frozen = queue.popleft()
        current_belief = set(current_belief_frozen) 

        if all(node == goal for node in current_belief):
            return list(action_path_str) 

        for action_char in possible_actions:
            next_belief: BeliefStatePoint = set()
            dr, dc = action_deltas[action_char]

            for r, c in current_belief:
                nr, nc = r + dr, c + dc

                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                    next_belief.add((nr, nc)) 
                else:
                    next_belief.add((r, c)) 

            if next_belief:
                frozen_next_belief = frozenset(next_belief)
                if frozen_next_belief not in visited:
                    visited.add(frozen_next_belief)
                    queue.append((action_path_str + action_char, frozen_next_belief))

    print("Sensorless Search: Không tìm thấy kế hoạch phù hợp.")
    return None

def q_learning_pathfinding(
    grid: Grid, start: Point, goal: Point,
    episodes: int = 5000,         
    alpha: float = 0.1,          
    gamma: float = 0.9,          
    epsilon_start: float = 0.9,  
    epsilon_end: float = 0.05, 
    epsilon_decay: float = 0.999,
    max_steps_episode: int = 200,
    max_steps_solve: int = 500   
) -> Optional[Path]:
    """Học đường đi bằng Q-Learning và trả về path."""
    print(f"Q-Learning: Bắt đầu huấn luyện ({episodes} episodes)...")
    training_start_time = time.time()
    rows, cols = len(grid), len(grid[0])

    q_table: Dict[Point, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    epsilon = epsilon_start

    for episode in range(episodes):
        current_pos = start
        if episode % (episodes // 10) == 0 and episode > 0: 
             print(f"  Q-Learning Episode {episode}/{episodes}, Epsilon: {epsilon:.3f}")

        for _ in range(max_steps_episode):
            if current_pos == goal:
                break 

            valid_moves = get_valid_moves(grid, current_pos)
            if not valid_moves: break 

            action: str
            next_pos: Point

            if random.random() < epsilon:
                action, next_pos = random.choice(valid_moves) 
            else:

                best_q = -float('inf')
                best_actions = []
                for act, next_state in valid_moves:
                    q_val = q_table[current_pos][act]
                    if q_val > best_q:
                        best_q = q_val
                        best_actions = [(act, next_state)]
                    elif q_val == best_q:
                        best_actions.append((act, next_state))

                if not best_actions: 
                    action, next_pos = random.choice(valid_moves)
                else: 
                    action, next_pos = random.choice(best_actions)

            reward = -0.1 
            if next_pos == goal:
                reward = 100.0 

            max_next_q = 0.0
            if next_pos != goal:
                next_state_moves = get_valid_moves(grid, next_pos)
                if next_state_moves:
                    q_values_next = [q_table[next_pos][act] for act, _ in next_state_moves]
                    if q_values_next:
                        max_next_q = max(q_values_next)

            old_q = q_table[current_pos][action]
            new_q = old_q + alpha * (reward + gamma * max_next_q - old_q)
            q_table[current_pos][action] = new_q

            current_pos = next_pos 

        if epsilon > epsilon_end:
            epsilon *= epsilon_decay

    training_end_time = time.time()
    print(f"Q-Learning: Huấn luyện xong sau {training_end_time - training_start_time:.2f}s.")
    print("Q-Learning: Trích xuất đường đi...")

    path: Path = [start]
    current_pos = start
    visited_solve: Set[Point] = {start} 

    for _ in range(max_steps_solve):
        if current_pos == goal:
            print("Q-Learning: Tìm thấy đường đi!")
            return path 

        valid_moves = get_valid_moves(grid, current_pos)
        if not valid_moves:
            print("Q-Learning: Bị kẹt khi trích xuất đường đi (không có bước đi hợp lệ).")
            return None 

        best_q = -float('inf')
        best_action: Optional[str] = None
        next_pos_from_best_action: Optional[Point] = None

        possible_next_actions = []
        for act, next_state in valid_moves:
             q_val = q_table[current_pos].get(act, 0.0) 
             possible_next_actions.append((q_val, act, next_state))

        if not possible_next_actions: 
            print("Q-Learning: Bị kẹt khi trích xuất đường đi (lỗi logic?).")
            return None

        random.shuffle(possible_next_actions) 
        possible_next_actions.sort(key=lambda item: item[0], reverse=True)

        best_q_val, best_action, next_pos_from_best_action = possible_next_actions[0]

        if next_pos_from_best_action in visited_solve:

             if len(possible_next_actions) > 1 and possible_next_actions[1][2] not in visited_solve:
                  print(f"Q-Learning: Tránh lặp, chọn hành động tốt thứ 2 từ {current_pos}")
                  _, best_action, next_pos_from_best_action = possible_next_actions[1]
             else:
                  print(f"Q-Learning: Bị kẹt trong vòng lặp khi trích xuất đường đi tại {current_pos}.")

                  return None 

        current_pos = next_pos_from_best_action
        path.append(current_pos)
        visited_solve.add(current_pos)

    print(f"Q-Learning: Không tìm thấy đường đi trong giới hạn {max_steps_solve} bước.")
    return None 

def count_turns(path: Optional[Path]) -> int: 
    """Đếm số lần rẽ trong đường đi (dạng list các ô)."""
    if not path or len(path) < 3: return 0
    turns = 0

    dx1, dy1 = path[1][1] - path[0][1], path[1][0] - path[0][0]
    prev_dir = (dx1, dy1)

    for i in range(1, len(path) - 1):

        dx2, dy2 = path[i+1][1] - path[i][1], path[i+1][0] - path[i][0]
        curr_dir = (dx2, dy2)

        if curr_dir != (0, 0) and prev_dir != (0, 0) and curr_dir != prev_dir:
            turns += 1
        if curr_dir != (0,0): 
            prev_dir = curr_dir
    return turns