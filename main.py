import pygame
from collections import deque

# Kích thước ô lưới và màn hình
CELL_SIZE = 60
GRID_WIDTH, GRID_HEIGHT = 6, 6
SCREEN_WIDTH, SCREEN_HEIGHT = GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# Ma trận bãi đậu xe
parking_lot = [
    [0, 0, 1, 0, 0, 2],
    [0, 1, 1, 0, 1, 0],
    ["S", 0, 0, 0, 1, 0],
    [0, 0, 1, 0, 0, 2],
    [0, 1, 0, 0, 1, 0],
    [0, 0, 0, 1, 0, 2]
]

# Tìm vị trí xe và điểm đỗ
def find_positions(grid):
    start, goal = None, None
    for x in range(len(grid)):
        for y in range(len(grid[0])):
            if grid[x][y] == "S":
                start = (x, y)
            elif grid[x][y] == 2:
                goal = (x, y)
    return start, goal

# Thuật toán BFS tìm đường đi
def bfs(grid, start, goal):
    queue = deque([(start, [])])
    visited = set()
    visited.add(start)
    
    while queue:
        (x, y), path = queue.popleft()
        if (x, y) == goal:
            return path + [(x, y)]
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]) and (nx, ny) not in visited:
                if grid[nx][ny] != 1:
                    queue.append(((nx, ny), path + [(x, y)]))
                    visited.add((nx, ny))
    return []

# Khởi tạo Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

# Tìm đường đi
start_pos, goal_pos = find_positions(parking_lot)
path = bfs(parking_lot, start_pos, goal_pos)

# Chạy mô phỏng Pygame
running = True
step = 0
while running:
    screen.fill(WHITE)
    
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            rect = pygame.Rect(y * CELL_SIZE, x * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if parking_lot[x][y] == 1:
                pygame.draw.rect(screen, BLACK, rect)
            elif parking_lot[x][y] == 2:
                pygame.draw.rect(screen, GREEN, rect)
            pygame.draw.rect(screen, BLACK, rect, 2)
    
    # Hiển thị xe di chuyển theo đường đi
    if step < len(path):
        car_x, car_y = path[step]
        pygame.draw.rect(screen, RED, (car_y * CELL_SIZE, car_x * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    
    pygame.display.flip()
    clock.tick(2)  # Tốc độ di chuyển của xe
    
    step += 1 if step < len(path) - 1 else 0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
