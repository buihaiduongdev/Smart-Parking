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
