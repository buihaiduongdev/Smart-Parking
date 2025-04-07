import pygame
import sys
import math
import random
import json
import heapq # For A*
import collections # For BFS
from pytmx.util_pygame import load_pygame
import os

# === Configuration Loading ===
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "algorithms_to_run": ["a_star"], # Default if config fails
    "simulation_speed_factor": 1.0,
    "max_pedestrians": 5,
    "min_pedestrian_spawn_interval_ms": 4000,
    "max_pedestrian_spawn_interval_ms": 8000,
    "pedestrian_speed": 1.0,
    "map_file": "map.tmx"
}

try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    print(f"Loaded configuration from {CONFIG_FILE}")
except (FileNotFoundError, json.JSONDecodeError) as e:
    print(f"Warning: Config file '{CONFIG_FILE}' not found or invalid: {e}. Using defaults.")
    config = DEFAULT_CONFIG

# Lấy các giá trị config cần thiết
SIM_SPEED_FACTOR = config.get("simulation_speed_factor", DEFAULT_CONFIG["simulation_speed_factor"])
MAX_PEDESTRIANS = config.get("max_pedestrians", DEFAULT_CONFIG["max_pedestrians"])
MIN_PEDES_SPAWN = config.get("min_pedestrian_spawn_interval_ms", DEFAULT_CONFIG["min_pedestrian_spawn_interval_ms"])
MAX_PEDES_SPAWN = config.get("max_pedestrian_spawn_interval_ms", DEFAULT_CONFIG["max_pedestrian_spawn_interval_ms"])
PEDES_SPEED = config.get("pedestrian_speed", DEFAULT_CONFIG["pedestrian_speed"])
MAP_FILENAME = config.get("map_file", DEFAULT_CONFIG["map_file"])
ALGORITHMS = config.get("algorithms_to_run", DEFAULT_CONFIG["algorithms_to_run"])
FIRST_ALGORITHM_NAME = ALGORITHMS[0] if ALGORITHMS else "a_star" # Lấy algo đầu tiên hoặc mặc định là a_star

print(f"Using map: {MAP_FILENAME}")
print(f"Guide path algorithm: {FIRST_ALGORITHM_NAME}")
print(f"Simulation Speed Factor: {SIM_SPEED_FACTOR}")

# === Constants ===
CELL_SIZE = 64
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
TEXT_COL = (255, 255, 255)
GUIDE_PATH_COLOR = (0, 150, 255, 180) # Màu xanh dương cho đường dẫn gợi ý
GOAL_COLOR = (0, 255, 0, 100) # Màu xanh lá cho ô đích
CAR_IMAGE_PATH = "./PNG/App/car7.png"
PEDESTRIAN_IMAGE_PATHS = [
    "./PNG/Other/Person_BlueBlack1.png", "./PNG/Other/Person_RedBlack1.png",
    "./PNG/Other/Person_YellowBrown2.png", "./PNG/Other/Person_RedBlond1.png",
    "./PNG/Other/Person_PurpleBrown1.png", "./PNG/Other/Person_OrangeBrown1.png",
    "./PNG/Other/Person_GreenBlack2.png",
]
GRID_ROWS, GRID_COLS = 0, 0 # Sẽ được cập nhật
MANUAL_CAR_ACCEL = 0.12
MANUAL_CAR_BRAKE = 0.25
MANUAL_CAR_FRICTION = 0.97
MANUAL_CAR_ROTATION = 4.0
MANUAL_MAX_SPEED = 4.0
COLLISION_FREEZE_FRAMES = 10 # Số frame đóng băng sau va chạm

# === Asset Loading (Global variables for assets) ===
car_surface_converted = None
pedestrian_surfaces_converted = []
font_small = None
font_medium = None

def load_and_convert_assets():
    """Load và convert các ảnh cần thiết. Phải gọi SAU khi display init."""
    global car_surface_converted, pedestrian_surfaces_converted, font_small, font_medium

    print("Loading and converting assets...")
    # --- Load Car Image ---
    try:
        raw_car = pygame.image.load(CAR_IMAGE_PATH)
        car_surface_converted = raw_car.convert_alpha()
        print(f"Car asset loaded and converted.")
    except pygame.error as e:
        print(f"Fatal Error loading/converting car image: {e}")
        return False # Báo lỗi

    # --- Load Pedestrian Images ---
    temp_peds = []
    for path in PEDESTRIAN_IMAGE_PATHS:
        try:
           temp_peds.append(pygame.image.load(path).convert_alpha())
        except pygame.error as e:
           print(f"Warning: Failed to load/convert pedestrian image '{path}': {e}")
    pedestrian_surfaces_converted = temp_peds
    print(f"Loaded and converted {len(pedestrian_surfaces_converted)} pedestrian images.")

    # --- Load Fonts ---
    try:
        font_small = pygame.font.SysFont("calibri", 24)
        font_medium = pygame.font.SysFont("calibri", 36)
    except Exception as e:
        print(f"Warning: Error loading system font: {e}. Using default.")
        font_small = pygame.font.Font(None, 30)
        font_medium = pygame.font.Font(None, 40)

    return True # Báo thành công

# === Pathfinding Algorithms (A* and BFS included directly) ===
def heuristic(a, b):
    (x1, y1), (x2, y2) = a, b
    return abs(x1 - x2) + abs(y1 - y2)

def a_star(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    close_set, came_from = set(), {}
    gscore = {start: 0}
    fscore = {start: heuristic(start, goal)}
    oheap = [(fscore[start], start)]
    while oheap:
        current = heapq.heappop(oheap)[1]
        if current == goal:
            data = []
            while current in came_from: data.append(current); current = came_from[current]
            return data[::-1] # Path from start to goal
        close_set.add(current)
        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j
            tentative_g_score = gscore[current] + 1
            if not (0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols) or grid[neighbor[0]][neighbor[1]] == 1:
                continue
            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, float('inf')):
                continue
            if tentative_g_score < gscore.get(neighbor, float('inf')) or neighbor not in [i[1] for i in oheap]:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(oheap, (fscore[neighbor], neighbor))
    return None # No path found

def bfs(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    queue = collections.deque([[start]])
    seen = {start}
    while queue:
        path = queue.popleft()
        x, y = path[-1]
        if (x, y) == goal: return path
        for dx, dy in neighbors:
            next_x, next_y = x + dx, y + dy
            if 0 <= next_x < rows and 0 <= next_y < cols and \
               grid[next_x][next_y] == 0 and (next_x, next_y) not in seen:
                seen.add((next_x, next_y))
                new_path = list(path); new_path.append((next_x, next_y))
                queue.append(new_path)
    return None

def get_pathfinding_function(algo_name):
    if algo_name == "a_star": return a_star
    elif algo_name == "bfs": return bfs
    else:
        print(f"Warning: Guide algorithm '{algo_name}' not recognized. Defaulting to A*.")
        return a_star

# === Game Object Classes ===
class Car:
    """Xe do người chơi điều khiển."""
    def __init__(self, center_x, center_y, speed_factor=1.0):
        global car_surface_converted
        if car_surface_converted is None: raise RuntimeError("Assets not loaded before creating Car!")
        self.center_x, self.center_y = float(center_x), float(center_y)
        self.original_surface = car_surface_converted
        self.surface = self.original_surface
        self.rect = self.surface.get_rect(center=(self.center_x, self.center_y))
        self.mask = pygame.mask.from_surface(self.surface)
        self.angle, self.speed = 0.0, 0.0
        # Apply scaling from config and manual constants
        self.accel = MANUAL_CAR_ACCEL * speed_factor
        self.brake_decel = MANUAL_CAR_BRAKE * speed_factor
        self.friction = MANUAL_CAR_FRICTION
        self.rotation_speed = MANUAL_CAR_ROTATION # Rotation speed might not need scaling
        self.max_speed = MANUAL_MAX_SPEED * speed_factor

    def update_manual(self, keys_pressed):
        # Acceleration/Braking
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]: self.speed = min(self.max_speed, self.speed + self.accel)
        elif keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]: self.speed = max(0, self.speed - self.brake_decel)
        else: self.speed *= self.friction
        # Rotation
        if abs(self.speed) > 0.05:
            if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]: self.angle = (self.angle + self.rotation_speed) % 360
            if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]: self.angle = (self.angle - self.rotation_speed) % 360
        # Movement
        if abs(self.speed) > 0.01:
            rad = math.radians(90 - self.angle); move_x = math.cos(rad) * self.speed; move_y = -math.sin(rad) * self.speed
            self.center_x += move_x; self.center_y += move_y
        self._update_visuals()

    def _update_visuals(self):
        self.surface = pygame.transform.rotate(self.original_surface, -self.angle)
        self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
        self.mask = pygame.mask.from_surface(self.surface)

    def draw(self, target_surface): target_surface.blit(self.surface, self.rect.topleft)

class Pedestrian(pygame.sprite.Sprite):
    """Người đi bộ di chuyển theo đường định sẵn."""
    def __init__(self, x, y, image_surface, path_points, base_speed=1.0, speed_factor=1.0):
        super().__init__()
        self.image = image_surface
        self.rect = self.image.get_rect(center=(x, y))
        self.x, self.y = float(x), float(y)
        self.speed = base_speed * speed_factor
        self.path_points = path_points
        self.target_point_index = 0
        self.mask = pygame.mask.from_surface(self.image)
        if not self.path_points or len(self.path_points) < 2: self.kill()

    def update(self):
        if self.target_point_index >= len(self.path_points): self.kill(); return
        target_x, target_y = self.path_points[self.target_point_index]
        dx, dy = target_x - self.x, target_y - self.y
        distance = math.hypot(dx, dy)
        if distance < self.speed * 1.5: # Arrival threshold
            self.target_point_index += 1
            if self.target_point_index >= len(self.path_points): self.kill(); return
            target_x, target_y = self.path_points[self.target_point_index] # Update target for rest of frame
            dx, dy = target_x - self.x, target_y - self.y; distance = math.hypot(dx, dy)
        if distance > 0:
            move = min(self.speed, distance); dir_x, dir_y = dx / distance, dy / distance
            self.x += dir_x * move; self.y += dir_y * move
            self.rect.center = (int(self.x), int(self.y))

class Tile(pygame.sprite.Sprite):
    """Tile tĩnh trên bản đồ."""
    def __init__(self, pos, surf, groups):
        super().__init__(groups); self.image = surf; self.rect = self.image.get_rect(topleft=pos)

# === Helper Functions ===
def draw_text(text, font, color, x, y, surface):
    if font and surface: surface.blit(font.render(text, True, color), (x, y))

def create_grid_from_map(tmx_data):
    global GRID_ROWS, GRID_COLS
    width = tmx_data.width * tmx_data.tilewidth; height = tmx_data.height * tmx_data.tileheight
    GRID_COLS = width // CELL_SIZE; GRID_ROWS = height // CELL_SIZE
    grid = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
    for obj in tmx_data.objects:
        is_obstacle = obj.name in ['Border', 'RandomCar'] or obj.type == 'Border'
        if is_obstacle:
            l, t = int(obj.x) // CELL_SIZE, int(obj.y) // CELL_SIZE
            r, b = math.ceil((obj.x + obj.width)/CELL_SIZE), math.ceil((obj.y + obj.height)/CELL_SIZE)
            for row in range(t, b):
                for col in range(l, r):
                    if 0 <= row < GRID_ROWS and 0 <= col < GRID_COLS: grid[row][col] = 1
    return grid

def load_map_data(tmx_filepath):
    try: tmx_data = load_pygame(tmx_filepath)
    except Exception as e: print(f"Fatal Error loading map '{tmx_filepath}': {e}"); return None
    base_grid = create_grid_from_map(tmx_data)
    all_sprites, static_obstacles = pygame.sprite.Group(), pygame.sprite.Group()
    borders, ped_paths, start_pos = [], [], (100, 100) # Defaults
    for layer in tmx_data.visible_layers: # Layers for drawing
        if hasattr(layer, 'data'):
            for x, y, surf in layer.tiles(): Tile((x*CELL_SIZE, y*CELL_SIZE), surf, all_sprites)
    for obj in tmx_data.objects: # Objects for logic
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        if obj.name == 'Border' or obj.type == 'Border': borders.append(rect)
        elif obj.name == 'Start': start_pos = (obj.x, obj.y)
        elif obj.name == 'RandomCar' and obj.image: Tile((obj.x, obj.y), obj.image, (all_sprites, static_obstacles))
        elif hasattr(obj, 'points') and "PedestrianPaths" in obj.name:
            y_offset = -576 # Check this offset from Tiled!
            points = [(p.x + obj.x, p.y + obj.y + y_offset) for p in obj.points]
            if len(points) >= 2: ped_paths.append(points)
    map_data = {"base_grid": base_grid, "all_map_sprites": all_sprites,
                "static_obstacle_sprites": static_obstacles, "border_rects": borders,
                "start_pos": start_pos, "pedestrian_paths": ped_paths}
    print(f"Map loaded: Grid({GRID_ROWS}x{GRID_COLS}), Start({start_pos}), {len(ped_paths)} Ped Paths.")
    return map_data

def find_random_valid_goal(grid):
    attempts = 0; max_attempts = GRID_ROWS * GRID_COLS
    while attempts < max_attempts:
        r, c = random.randint(0, GRID_ROWS - 1), random.randint(0, GRID_COLS - 1)
        if grid[r][c] == 0: return (r, c) # Found a walkable cell
        attempts += 1
    print("Warning: Could not find random goal.")
    return None

def spawn_random_pedestrian(ped_paths, ped_group):
    global pedestrian_surfaces_converted # Use loaded surfaces
    if not ped_paths or not pedestrian_surfaces_converted or len(ped_group) >= MAX_PEDESTRIANS: return
    try:
        path = random.choice(ped_paths)
        if len(path) < 2: return
        img = random.choice(pedestrian_surfaces_converted)
        start_node, nodes = (path[0], path) if random.choice([True, False]) else (path[-1], path[::-1])
        ped = Pedestrian(start_node[0], start_node[1], img, nodes, base_speed=PEDES_SPEED, speed_factor=SIM_SPEED_FACTOR)
        ped_group.add(ped)
    except Exception as e: print(f"Error spawning pedestrian: {e}")

# === Main Game Function ===
def run_manual_with_guide():
    """Chạy chế độ lái thủ công với đường dẫn gợi ý."""
    print("\nStarting Manual Drive with Guide Path Mode...")

    # --- Pygame Init ---
    pygame.init()
    pygame.font.init()
    try:
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Manual Drive (Guide Path: " + FIRST_ALGORITHM_NAME.upper() + ")")
    except pygame.error as e:
        print(f"Fatal Error initializing display: {e}"); sys.exit()

    # --- Load Assets ---
    if not load_and_convert_assets(): sys.exit() # Thoát nếu load lỗi

    clock = pygame.time.Clock()

    # --- Load Map ---
    map_data = load_map_data(MAP_FILENAME)
    if not map_data: sys.exit()
    base_grid = map_data["base_grid"]
    all_map_sprites = map_data["all_map_sprites"]
    static_obstacle_sprites = map_data["static_obstacle_sprites"]
    border_rects = map_data["border_rects"]
    start_pos_x, start_pos_y = map_data["start_pos"]
    pedestrian_paths = map_data["pedestrian_paths"]

    # --- Game Objects ---
    car = Car(start_pos_x, start_pos_y, speed_factor=SIM_SPEED_FACTOR)
    pedestrian_sprites = pygame.sprite.Group()

    # --- Guide Path Setup ---
    pathfinding_func = get_pathfinding_function(FIRST_ALGORITHM_NAME)
    guide_path_cells = []
    current_goal_cell = None
    current_goal_rect = None

    def calculate_new_guide_path():
        """Tính toán đường dẫn gợi ý mới đến một đích ngẫu nhiên."""
        nonlocal guide_path_cells, current_goal_cell, current_goal_rect # Cho phép sửa biến bên ngoài
        print("Calculating new guide path...")
        # Tìm ô đích ngẫu nhiên mới
        new_goal = find_random_valid_goal(base_grid)
        if not new_goal: print("Failed to find new goal for guide path."); return

        # Lấy ô hiện tại của xe
        car_row = int(car.center_y // CELL_SIZE)
        car_col = int(car.center_x // CELL_SIZE)
        start_cell = (car_row, car_col)

        # Đảm bảo ô bắt đầu hợp lệ
        if not (0 <= start_cell[0] < GRID_ROWS and 0 <= start_cell[1] < GRID_COLS and base_grid[start_cell[0]][start_cell[1]] == 0):
             print(f"Cannot calculate guide path: Car start {start_cell} invalid/blocked.")
             guide_path_cells = []; current_goal_cell = None; current_goal_rect = None
             return

        # Tạo grid tạm thời (có thể thêm người đi bộ nếu muốn path né họ)
        # temp_grid = [row[:] for row in base_grid] # Bỏ qua người đi bộ cho path gợi ý

        # Chạy thuật toán pathfinding
        path = pathfinding_func(base_grid, start_cell, new_goal) # Dùng base_grid cho đơn giản

        if path:
            guide_path_cells = path
            current_goal_cell = new_goal
            current_goal_rect = pygame.Rect(new_goal[1]*CELL_SIZE, new_goal[0]*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            print(f"Guide path found to {new_goal}. Length: {len(path)}")
        else:
            print(f"Guide pathfinding failed from {start_cell} to {new_goal}.")
            guide_path_cells = []; current_goal_cell = None; current_goal_rect = None

    calculate_new_guide_path() # Tính path ban đầu

    # --- Timers ---
    spawn_timer = pygame.time.get_ticks()
    next_spawn_interval = random.randint(MIN_PEDES_SPAWN, MAX_PEDES_SPAWN)
    collision_timer = 0 # Đếm ngược frame đóng băng sau va chạm

    # === Main Game Loop ===
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        delta_time_ms = clock.tick(60) # Limit FPS, get delta time

        # --- 1. Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False
                if event.key == pygame.K_r: calculate_new_guide_path() # Tính lại path gợi ý

        # --- 2. Player Input ---
        keys = pygame.key.get_pressed()

        # --- 3. Update Game State ---
        # Spawn/Update Pedestrians
        if current_time - spawn_timer > next_spawn_interval:
            spawn_random_pedestrian(pedestrian_paths, pedestrian_sprites)
            spawn_timer = current_time
            next_spawn_interval = random.randint(MIN_PEDES_SPAWN, MAX_PEDES_SPAWN)
        pedestrian_sprites.update()

        # Update Car (Movement & Collision Check)
        old_center_x, old_center_y = car.center_x, car.center_y
        old_rect = car.rect.copy()

        if collision_timer <= 0: # Chỉ di chuyển nếu không bị đóng băng
            car.update_manual(keys)
        else: # Nếu đang đóng băng, chỉ giảm tốc và cập nhật hình ảnh
            car.speed *= car.friction
            car._update_visuals()
            collision_timer -= 1

        # Collision Detection
        collision_detected = False
        if any(car.rect.colliderect(border) for border in border_rects): collision_detected = True
        if not collision_detected and pygame.sprite.spritecollide(car, static_obstacle_sprites, False, pygame.sprite.collide_mask): collision_detected = True
        if not collision_detected and pygame.sprite.spritecollide(car, pedestrian_sprites, False, pygame.sprite.collide_mask): collision_detected = True

        # Collision Response
        if collision_detected and collision_timer <= 0: # Chỉ phản hồi nếu vừa va chạm
            car.center_x, car.center_y = old_center_x, old_center_y
            car.rect = old_rect
            car.speed = -car.speed * 0.3 # Nảy ngược nhẹ
            car._update_visuals()
            collision_timer = COLLISION_FREEZE_FRAMES # Đặt lại timer đóng băng

        # --- 4. Drawing ---
        screen.fill((70, 90, 110)) # Màu nền
        all_map_sprites.draw(screen) # Vẽ map

        # Vẽ đường dẫn gợi ý
        if guide_path_cells:
            dot_radius = 4
            path_surf = pygame.Surface((dot_radius*2, dot_radius*2), pygame.SRCALPHA) # Surface nhỏ để vẽ chấm alpha
            pygame.draw.circle(path_surf, GUIDE_PATH_COLOR, (dot_radius, dot_radius), dot_radius)
            for cell in guide_path_cells:
                center_x = cell[1] * CELL_SIZE + CELL_SIZE // 2 - dot_radius
                center_y = cell[0] * CELL_SIZE + CELL_SIZE // 2 - dot_radius
                screen.blit(path_surf, (center_x, center_y))

        # Vẽ ô đích của đường dẫn gợi ý
        if current_goal_rect:
            goal_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            goal_surface.fill(GOAL_COLOR)
            screen.blit(goal_surface, current_goal_rect.topleft)
            pygame.draw.rect(screen, (255, 255, 255), current_goal_rect, 2)

        pedestrian_sprites.draw(screen) # Vẽ người đi bộ
        car.draw(screen) # Vẽ xe

        # Vẽ HUD
        hud_texts = [
            f"Speed: {car.speed:.1f}", f"Angle: {car.angle:.0f}",
            f"Peds: {len(pedestrian_sprites)}/{MAX_PEDESTRIANS}",
            "WASD/Arrows: Drive | R: New Guide Path | ESC: Exit"
        ]
        for i, text in enumerate(hud_texts):
            draw_text(text, font_medium, TEXT_COL, 10, 10 + i * 35, screen)

        pygame.display.flip() # Cập nhật màn hình

    # --- Cleanup ---
    pygame.quit()
    print("Exited Manual Drive Mode.")

# === Script Entry Point ===
if __name__ == '__main__':
    # Kiểm tra file cơ bản
    if not os.path.exists(MAP_FILENAME):
        print(f"Fatal Error: Map file '{MAP_FILENAME}' not found.")
    elif not os.path.exists(CAR_IMAGE_PATH):
         print(f"Fatal Error: Car image '{CAR_IMAGE_PATH}' not found.")
    elif not os.path.exists(CONFIG_FILE):
         print(f"Warning: Config file '{CONFIG_FILE}' not found, using defaults.")
         run_manual_with_guide() # Vẫn chạy với default
    else:
        run_manual_with_guide()