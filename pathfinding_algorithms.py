# pathfinding_algorithms.py
import heapq
from collections import deque # Import deque cho hàng đợi BFS
import pygame # Needed for pygame.time.get_ticks()

# === A* Pathfinding ===
def heuristic(a, b):
    """Calculates the Manhattan distance heuristic."""
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def a_star(grid, start, goal, timeout_ms=200):
    """
    Finds a path from start to goal using the A* algorithm.

    Args:
        grid: A 2D list representing the map (0=walkable, 1=obstacle).
        start: A tuple (row, col) for the starting cell.
        goal: A tuple (row, col) for the destination cell.
        timeout_ms: Maximum time in milliseconds allowed for the search.

    Returns:
        A list of (row, col) tuples representing the path from the cell
        *after* the start cell up to and including the goal cell,
        or None if no path is found or the search times out.
    """
    rows, cols = len(grid), len(grid[0])
    open_set = []
    # Store: (priority, cost, current_node, path_list)
    # Priority = cost + heuristic
    heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start, []))
    visited = set()
    start_time = pygame.time.get_ticks() # Use Pygame time for consistency

    while open_set:
        # Timeout check
        if pygame.time.get_ticks() - start_time > timeout_ms:
            print(f"A* search timed out ({timeout_ms}ms)")
            return None

        # Get the node with the lowest estimated total cost
        try:
            est_cost, cost, current, path = heapq.heappop(open_set)
        except IndexError:
            # Should not happen if open_set is checked, but as a safeguard
            print("A* Error: Open set became empty unexpectedly.")
            return None


        # Check if we reached the goal
        if current == goal:
            # Return the constructed path (excluding the start node itself,
            # as the path list stores the steps *to* reach a node)
            return path + [current] # Include the goal in the returned path

        # Avoid reprocessing nodes
        if current in visited:
            continue
        visited.add(current)

        # Explore neighbors (Up, Down, Left, Right)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # NESW
            nx, ny = current[0] + dx, current[1] + dy

            # Check boundaries and obstacles
            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0:
                if (nx, ny) not in visited:
                    # Calculate costs for the neighbor
                    new_cost = cost + 1  # Assuming uniform cost grid
                    priority = new_cost + heuristic((nx, ny), goal)
                    # Add neighbor to the open set with its path history
                    # The path stored is the path *to* (nx, ny)
                    heapq.heappush(open_set, (priority, new_cost, (nx, ny), path + [current]))

    print(f"A* could not find a path from {start} to {goal}")
    return None # No path found

# === Breadth-First Search (BFS) ===
def bfs(grid, start, goal, timeout_ms=500): # Tăng timeout một chút cho BFS nếu cần
    """
    Finds the shortest path (in number of steps) using BFS.

    Args:
        grid: A 2D list representing the map (0=walkable, 1=obstacle).
        start: A tuple (row, col) for the starting cell.
        goal: A tuple (row, col) for the destination cell.
        timeout_ms: Maximum time allowed for the search.

    Returns:
        A list of (row, col) tuples representing the path from the cell
        *after* the start cell up to and including the goal cell,
        or None if no path is found or times out.
    """
    rows, cols = len(grid), len(grid[0])
    queue = deque([(start, [start])]) # Hàng đợi chứa (node, path_tới_node)
    visited = {start} # Set để lưu các ô đã thăm
    start_time = pygame.time.get_ticks()

    while queue:
        # Timeout check
        if pygame.time.get_ticks() - start_time > timeout_ms:
            print(f"BFS search timed out ({timeout_ms}ms)")
            return None

        (current_node, path) = queue.popleft() # Lấy từ đầu hàng đợi (FIFO)

        if current_node == goal:
            # Trả về đường đi, bỏ qua điểm start ban đầu
            return path[1:]

        # Khám phá các hàng xóm (Neighbors)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # NESW
            nx, ny = current_node[0] + dx, current_node[1] + dy

            neighbor = (nx, ny)

            # Kiểm tra biên, vật cản và ô đã thăm
            if 0 <= nx < rows and 0 <= ny < cols and \
               grid[nx][ny] == 0 and \
               neighbor not in visited:

                visited.add(neighbor)
                new_path = list(path) # Tạo bản sao của path cũ
                new_path.append(neighbor) # Thêm hàng xóm vào path mới
                queue.append((neighbor, new_path)) # Thêm vào cuối hàng đợi

    print(f"BFS could not find a path from {start} to {goal}")
    return None # Không tìm thấy đường đi