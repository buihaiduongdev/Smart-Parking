# pathfinding_algorithms.py
import heapq
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