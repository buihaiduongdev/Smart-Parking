import heapq
from collections import deque

# === Heuristic cho A* ===
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# === A* Search ===
def a_star(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start, []))
    visited = set()
    while open_set:
        est_cost, cost, current, path = heapq.heappop(open_set)
        if current in visited:
            continue
        visited.add(current)
        path = path + [current]
        if current == goal:
            return path
        for dx, dy in [(0,1),(1,0),(-1,0),(0,-1)]:
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0:
                heapq.heappush(open_set, (
                    cost + 1 + heuristic((nx, ny), goal),
                    cost + 1,
                    (nx, ny),
                    path
                ))
    return None

# === BFS Search ===
def bfs(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    q = deque([start])
    parent = {start: None}
    while q:
        u = q.popleft()
        if u == goal:
            break
        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            nx, ny = u[0] + dx, u[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0 and (nx, ny) not in parent:
                parent[(nx, ny)] = u
                q.append((nx, ny))
    return reconstruct(goal, parent)

# === DFS Search ===
def dfs(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    st = [start]
    parent = {start: None}
    while st:
        u = st.pop()
        if u == goal:
            break
        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            nx, ny = u[0] + dx, u[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0 and (nx, ny) not in parent:
                parent[(nx, ny)] = u
                st.append((nx, ny))
    return reconstruct(goal, parent)

# === Simple Hill Climbing ===
def simple_hill_climbing(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    current = start
    path = [current]
    while current != goal:
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0:
                neighbors.append((nx, ny))
        if not neighbors:
            return None  # No path found
        current = min(neighbors, key=lambda n: heuristic(n, goal))
        path.append(current)
        if current == goal:
            return path
    return path

# === BFS Sensorless ===
def bfs_sensorless(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    q = deque([start])
    visited = set()
    visited.add(start)
    while q:
        current = q.popleft()
        if current == goal:
            return True  # Goal reached
        for dx, dy in [(0, 1), (1, 0), (-1, 0), (0, -1)]:
            nx, ny = current[0] + dx, current[1] + dy
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0 and (nx, ny) not in visited:
                visited.add((nx, ny))
                q.append((nx, ny))
    return False  # Goal not reachable

# === CSP Backtracking ===
def csp_backtracking(variables, domains, constraints):
    def backtrack(assignment):
        if len(assignment) == len(variables):
            return assignment
        var = select_unassigned_variable(variables, assignment)
        for value in domains[var]:
            if is_consistent(var, value, assignment, constraints):
                assignment[var] = value
                result = backtrack(assignment)
                if result:
                    return result
                del assignment[var]
        return None

    def select_unassigned_variable(variables, assignment):
        for var in variables:
            if var not in assignment:
                return var

    def is_consistent(var, value, assignment, constraints):
        for constraint in constraints:
            if not constraint(var, value, assignment):
                return False
        return True

    return backtrack({})

# === Dựng lại đường đi từ parent ===
def reconstruct(goal, parent):
    if goal not in parent:
        return []
    path = []
    node = goal
    while node is not None:
        path.append(node)
        node = parent[node]
    return path[::-1]

# === Đếm số lần rẽ ===
def count_turns(path):
    if len(path) < 3:
        return 0
    turns = 0
    prev_dir = (path[1][0] - path[0][0], path[1][1] - path[0][1])
    for i in range(1, len(path) - 1):
        curr_dir = (path[i+1][0] - path[i][0], path[i+1][1] - path[i][1])
        if curr_dir != prev_dir:
            turns += 1
        prev_dir = curr_dir
    return turns

# === Q-Learning ===
import numpy as np
import random

class QLearning:
    def __init__(self, state_size, action_size, learning_rate=0.1, discount_factor=0.9, exploration_rate=1.0, exploration_decay=0.99):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.exploration_rate = exploration_rate
        self.exploration_decay = exploration_decay
        self.q_table = np.zeros((state_size, action_size))

    def choose_action(self, state):
        if random.uniform(0, 1) < self.exploration_rate:
            return random.randint(0, self.action_size - 1)  # Chọn hành động ngẫu nhiên
        return np.argmax(self.q_table[state])  # Chọn hành động tốt nhất theo Q-table

    def update(self, state, action, reward, next_state):
        best_next_action = np.argmax(self.q_table[next_state])
        td_target = reward + self.discount_factor * self.q_table[next_state][best_next_action]
        td_error = td_target - self.q_table[state][action]
        self.q_table[state][action] += self.learning_rate * td_error

    def decay_exploration(self):
        self.exploration_rate *= self.exploration_decay
        self.exploration_rate = max(self.exploration_rate, 0.01)  # Giới hạn tối thiểu