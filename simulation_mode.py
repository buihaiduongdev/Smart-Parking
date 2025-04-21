import pygame
import math
import sys
import random
import json # For config and results
import time # For performance timing independent of Pygame ticks if needed
import statistics # For calculating averages

# Import local modules
from pytmx.util_pygame import load_pygame
import Button
# from PIL import Image # No longer needed directly here

# Initialize Pygame
pygame.init()

# === Configuration Loading ===
CONFIG_FILE = "./Data/config.json"
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    ALGORITHMS_TO_RUN = config.get("algorithms_to_run", ["a_star"])
    NUM_RUNS = config.get("num_runs_per_algorithm", 5)
    SIM_SPEED_FACTOR = config.get("simulation_speed_factor", 1.0)
    RUN_HEADLESS = config.get("run_headless", False)
    MAX_RUN_TIME_MS = config.get("max_run_time_ms", 60000)
    RESULTS_FILE = "./Data/simulation_results.json"
    MAX_PEDESTRIANS = config.get("max_pedestrians", 5) # Lấy từ config, mặc định là 5 nếu thiếu
    MIN_TIME_PEDES_SPAWN = config.get("min_pedestrian_spawn_interval_ms", 1000) # Mặc định 6000ms
    MAX_TIME_PEDES_SPAWN = config.get("max_pedestrian_spawn_interval_ms", 2000) # Mặc định 12000ms
    PEDES_SPEED = config.get("pedestrian_speed", 1) # Mặc định 1
    print("--- Configuration ---")
    print(f"Algorithms: {ALGORITHMS_TO_RUN}")
    print(f"Runs per Algo: {NUM_RUNS}")
    print(f"Speed Factor: {SIM_SPEED_FACTOR}")
    print(f"Headless: {RUN_HEADLESS}")
    print(f"Max Run Time: {MAX_RUN_TIME_MS} ms")    
    print(f"Results File: {RESULTS_FILE}")
    print("---------------------")
except FileNotFoundError:
    print(f"Error: Config file '{CONFIG_FILE}' not found. Exiting.")
    sys.exit()
except json.JSONDecodeError:
    print(f"Error: Config file '{CONFIG_FILE}' is not valid JSON. Exiting.")
    sys.exit()
except Exception as e:
    print(f"Error loading config: {e}. Exiting.")
    sys.exit()

# === Constants & Screen Setup ===
CELL_SIZE = 64
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
screen = None # Initialize screen later if not headless
if not RUN_HEADLESS:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Car Simulation Comparison")
clock = pygame.time.Clock()
FPS = 60 # Target FPS for simulation steps


# === Asset Loading ===
# Load images only once
try:
    car_img_original = pygame.image.load("./PNG/App/car7.png").convert_alpha()
    CAR_WIDTH, CAR_HEIGHT = car_img_original.get_size()
    print(f"Loaded car image: Width={CAR_WIDTH}, Height={CAR_HEIGHT}")
except pygame.error as e:
    print(f"Error loading car image: {e}")
    CAR_WIDTH, CAR_HEIGHT = 43, 74
    car_img_original = pygame.Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
    car_img_original.fill((255, 165, 0))

# Load other images if needed (buttons are only needed if not headless)
play_img = None
emptyBtnImg = None
font = None
TEXT_COL = (255, 255, 255)
playBtn = None
emptyBtn = None
if not RUN_HEADLESS:
    try:
        play_img = pygame.image.load("PNG/App/PlayButton.png")
        emptyBtnImg = pygame.image.load("PNG/App/SmallEmptyButton.png")
        button_width, button_height = play_img.get_size()
        button_x = (SCREEN_WIDTH - button_width) // 2
        button_y = (SCREEN_HEIGHT - button_height) // 2
        playBtn = Button.Button(button_x, button_y, play_img, 0.4) # Assuming Button class exists
        emptyBtn = Button.Button(button_x, button_y + 100, emptyBtnImg, 0.4)
        font = pygame.font.SysFont("calibri", 48) # Smaller font maybe
    except pygame.error as e:
        print(f"Warning: Error loading button/font assets: {e}")
    except NameError:
         print(f"Warning: Button class not found. UI disabled.")


pedestrian_images = []
try:
    pedestrian_images = [
        pygame.image.load("./PNG/Other/Person_BlueBlack1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_RedBlack1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_YellowBrown2.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_RedBlond1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_PurpleBrown1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_OrangeBrown1.png").convert_alpha(),
        pygame.image.load("./PNG/Other/Person_GreenBlack2.png").convert_alpha(),
    ]
except pygame.error as e:
    print(f"Warning: Error loading pedestrian images: {e}")

# === Map Loading and Grid Creation ===
try:
    tmx_data = load_pygame("map.tmx")
except FileNotFoundError:
    print("Error: map.tmx not found. Exiting.")
    sys.exit()
except Exception as e:
    print(f"Error loading map: {e}. Exiting.")
    sys.exit()

base_grid = None # Will be created by function
grid_rows, grid_cols = 0, 0

def create_grid_from_map(tmx_data, cell_size):
    # (Keep your existing create_grid_from_map function here)
    # ... (same as your original code) ...
    global grid_rows, grid_cols # Store dimensions globally
    width = tmx_data.width * tmx_data.tilewidth
    height = tmx_data.height * tmx_data.tileheight
    grid_cols = width // cell_size
    grid_rows = height // cell_size
    grid = [[0 for _ in range(grid_cols)] for _ in range(grid_rows)]
    static_obstacle_rects = [] # Store rects of static obstacles

    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'): # Tile layers
             pass # Grid based on objects now

    for obj in tmx_data.objects:
        obj_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        left = int(obj.x) // cell_size
        top = int(obj.y) // cell_size
        # Use ceil for right/bottom to ensure full coverage
        right = math.ceil((obj.x + obj.width) / cell_size)
        bottom = math.ceil((obj.y + obj.height) / cell_size)

        is_obstacle_type = obj.name in ['Border', 'RandomCar'] or obj.type == 'Border'

        if is_obstacle_type:
            # Mark grid cells as obstacles
            for row in range(top, bottom):
                for col in range(left, right):
                    if 0 <= row < grid_rows and 0 <= col < grid_cols:
                        grid[row][col] = 1 # Mark as obstacle
            if obj.name == 'RandomCar':
                 static_obstacle_rects.append(obj_rect)


    return grid, static_obstacle_rects


# Build the base grid and get static obstacle rects ONCE
base_grid, static_obstacle_rects = create_grid_from_map(tmx_data, CELL_SIZE)
if not base_grid:
    print("Error: Failed to create grid from map. Exiting.")
    sys.exit()


# === Classes (Car, Tile, Pedestrian) ===
# (Keep your Car, Tile, Pedestrian classes here)
# !!! IMPORTANT: Modify Car and Pedestrian to use SIM_SPEED_FACTOR !!!

class Car:
    def __init__(self, center_x, center_y, original_image, speed_factor=1.0):
        self.center_x = float(center_x)
        self.center_y = float(center_y)
        self.original_surface = original_image
        self.surface = self.original_surface
        self.rect = self.surface.get_rect(center=(self.center_x, self.center_y))
        self.mask = pygame.mask.from_surface(self.surface)
        self.angle = 0.0
        self.speed = 0.0
        # Apply speed factor
        self.max_speed = 2.0 * speed_factor
        self.accel = 0.05 # * speed_factor # Acceleration not used with spacebar holding
        self.decel = 0.03 # * speed_factor
        self.friction = 0.98
        self.rotation_speed = 4.0 # Rotation speed might also need scaling depending on max_speed
        self.path = []
        self.target_index = 0
        self.collision_flag = False # Flag to indicate collision this frame
     # ---> THÊM CÁC THUỘC TÍNH NÀY <---
        self.is_stopped = True # Giả sử ban đầu là đứng yên
        self.stopped_since = pygame.time.get_ticks() # Thời điểm bắt đầu dừng (khởi tạo là thời điểm hiện tại)
        self.STOPPED_THRESHOLD = 0.1 # Ngưỡng tốc độ coi là dừng (pixel/frame)
        # ---> KẾT THÚC PHẦN THÊM <---
    def set_path(self, new_path):
        # (Keep your set_path method)
        if new_path and len(new_path) > 0:
             self.path = new_path
             self.target_index = 0 # Always start from the first point of the new path
        else:
             self.path = []
             self.target_index = 0

    def move_towards_path(self, pedestrian_sprites, space_pressed):
        # (Keep your move_towards_path method)
        # Reset collision flag at the start of movement
        self.collision_flag = False

        if not self.path or self.target_index >= len(self.path):
            self.speed = 0
            # Update visual state even when stopped
            self.surface = pygame.transform.rotate(self.original_surface, -self.angle) # Use -angle for pygame rotation
            self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
            self.mask = pygame.mask.from_surface(self.surface)
            return # No path or end of path reached

        # --- Determine Speed ---
        if not space_pressed: # In simulation, we might always want it "pressed"
             # For simulation, let's assume car always tries to move if it has a path
             # self.speed = 0 # Keep this if you want manual space control during visual runs
             # return
             # OR: Always try to move at max speed (adjust later based on turns)
             current_max_speed = self.max_speed
        else:
             current_max_speed = self.max_speed

        # Get target world coordinates
        target_row, target_col = self.path[self.target_index]
        target_x = target_col * CELL_SIZE + CELL_SIZE // 2
        target_y = target_row * CELL_SIZE + CELL_SIZE // 2

        # --- Rotation Calculation ---
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        distance_to_target = math.hypot(dx, dy)
        angle_diff = 0.0
        if distance_to_target > 1.0:
            target_angle_rad = math.atan2(-dy, dx) # Math angle
            target_angle_deg = math.degrees(target_angle_rad)
            desired_angle = (90 - target_angle_deg) % 360 # Pygame angle (0=up)
            angle_diff = (desired_angle - self.angle + 180) % 360 - 180

        # --- Rotation Application ---
        alignment_tolerance = 1.0
        if abs(angle_diff) > alignment_tolerance:
            direction = 1 if angle_diff > 0 else -1
            rotation_magnitude = min(self.rotation_speed, abs(angle_diff))
            self.angle = (self.angle + direction * rotation_magnitude) % 360

        # --- Speed Adjustment Based on Turn ---
        turn_slowdown_threshold = 15.0
        max_angle_diff_for_speed = 90.0
        if abs(angle_diff) <= turn_slowdown_threshold:
            actual_speed = current_max_speed
        else:
            excess_angle = abs(angle_diff) - turn_slowdown_threshold
            range_angle = max(1.0, max_angle_diff_for_speed - turn_slowdown_threshold)
            reduction_factor = max(0.0, 1.0 - (excess_angle / range_angle))
            actual_speed = current_max_speed * reduction_factor
            actual_speed = max(0.0, actual_speed) # Ensure non-negative
        # ---> THÊM CẬP NHẬT TRẠNG THÁI DỪNG <---
        now = pygame.time.get_ticks()
        if actual_speed < self.STOPPED_THRESHOLD:
            # Xe đang dừng hoặc gần như dừng
            if not self.is_stopped:
                # Nếu xe vừa mới dừng lại ở frame này
                self.is_stopped = True
                self.stopped_since = now # Ghi lại thời điểm bắt đầu dừng
        else:
            # Xe đang di chuyển
            if self.is_stopped:
                 # Nếu xe vừa bắt đầu di chuyển lại
                 self.is_stopped = False
                 self.stopped_since = 0 # Reset thời điểm dừng
        # ---> KẾT THÚC CẬP NHẬT TRẠNG THÁI DỪNG <---
        # --- Movement ---

        self.speed = actual_speed # Update internal speed state
        if self.speed > 0.01:
            move_angle_rad = math.radians(90 - self.angle) # Correct for Pygame angle
            move_x = math.cos(move_angle_rad) * self.speed
            move_y = -math.sin(move_angle_rad) * self.speed

            next_center_x = self.center_x + move_x
            next_center_y = self.center_y + move_y

            # --- Collision Check (Simplified for now - more robust check happens externally) ---
            # Basic check before moving to prevent moving *into* an immediate obstacle
            # More advanced check needed for predicting collision along the move vector
            # For now, external check after move is primary

            # --- Update Position ---
            self.center_x = next_center_x
            self.center_y = next_center_y

        # --- Update Visuals ---
        self.surface = pygame.transform.rotate(self.original_surface, -self.angle) # Pygame uses counter-clockwise rotation
        self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
        self.mask = pygame.mask.from_surface(self.surface)

        # --- Check Target Arrival ---
        final_dx = target_x - self.center_x
        final_dy = target_y - self.center_y
        final_distance_to_target = math.hypot(final_dx, final_dy)
        #arrival_threshold = max(self.speed * 1.5, CELL_SIZE / 4.0)
        arrival_threshold = CELL_SIZE * 0.6 # Simpler threshold based on cell size

        if self.target_index < len(self.path): # Check index validity
            if final_distance_to_target < arrival_threshold:
                 self.target_index += 1


    def draw(self, target_surface):
        # (Keep your draw method)
        target_surface.blit(self.surface, self.rect.topleft)
        # Optional Debug Drawing (if not RUN_HEADLESS)
        # pygame.draw.circle(target_surface, (0, 255, 0), self.rect.center, 3)
        # pygame.draw.rect(target_surface, (255, 0, 0), self.rect, 1)


class Tile(pygame.sprite.Sprite):
    # (Keep your Tile class)
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Pedestrian(pygame.sprite.Sprite):
    def __init__(self, x, y, surface, path_points, speed=1, speed_factor=1.0):
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect(center=(x, y))
        self.x = float(x)
        self.y = float(y)
        # Apply speed factor
        self.base_speed = speed
        self.speed = self.base_speed * speed_factor
        self.path_points = path_points
        self.target_point_index = 0
        self.mask = pygame.mask.from_surface(self.image)
        if not self.path_points:
             self.kill()

    def update(self):
        # (Keep your update method, ensures speed is used correctly)
        if self.target_point_index >= len(self.path_points):
            self.kill()
            return

        target_x, target_y = self.path_points[self.target_point_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        # Use a slightly larger threshold involving speed to prevent stuttering
        arrival_threshold = self.speed * 1.5
        if distance < arrival_threshold:
            self.target_point_index += 1
            if self.target_point_index >= len(self.path_points):
                self.kill()
                return
            # Update target immediately
            target_x, target_y = self.path_points[self.target_point_index]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy) # Recalculate

        if distance > 0:
            dir_x = dx / distance
            dir_y = dy / distance
            self.x += dir_x * self.speed
            self.y += dir_y * self.speed
            self.rect.center = (int(self.x), int(self.y))


# === Helper Functions ===
def draw_text(text, font_obj, color, x, y, surface):
    if font_obj and surface:
        img = font_obj.render(text, True, color)
        surface.blit(img, (x, y))

def get_pathfinding_function(algo_name):
    """Maps algorithm name string to the actual function."""
    if algo_name == "a_star":
        # Import dynamically if needed, or rely on global import
        # from pathfinding_algorithms import a_star
        from pathfinding import a_star, heuristic # Import from the new file
        return a_star
    
    elif algo_name == "bfs":
        from pathfinding import bfs # Import hàm bfs
        return bfs
    # Add other algorithms here:
    # elif algo_name == "dijkstra":
    #     from pathfinding_algorithms import dijkstra
    #     return dijkstra
    else:
        print(f"Warning: Pathfinding algorithm '{algo_name}' not found.")
        return None

def find_random_valid_goal(grid, grid_rows, grid_cols, start_cell):
    """Finds a random walkable cell, avoiding the start cell."""
    attempts = 0
    max_attempts = grid_rows * grid_cols # Limit attempts
    while attempts < max_attempts:
        rand_row = random.randint(0, grid_rows - 1)
        rand_col = random.randint(0, grid_cols - 1)
        goal_cell = (rand_row, rand_col)

        # Check if walkable and not the start cell
        if grid[rand_row][rand_col] == 0 and goal_cell != start_cell:
             # Optional: Add check against static_obstacle_rects if needed,
             # but grid should already represent them.
             return goal_cell
        attempts += 1
    print("Warning: Could not find a random valid goal after many attempts.")
    return None # Indicate failure

def check_pedestrian_on_path(path_cells, pedestrian_group, cell_size):
    # (Keep your check_pedestrian_on_path function)
    if not path_cells:
        return False
    pedestrian_occupied_cells = set()
    for ped in pedestrian_group:
        ped_col = ped.rect.centerx // cell_size
        ped_row = ped.rect.centery // cell_size
        pedestrian_occupied_cells.add((ped_row, ped_col))

    for cell in path_cells:
        if cell in pedestrian_occupied_cells:
            return True # Collision detected on path
    return False


def spawn_random_pedestrian(paths, pedestrian_group, speed_factor):
    # ---> THÊM DÒNG NÀY <---
    print(f"  DEBUG spawn_random_pedestrian: Hàm được gọi. Current Peds: {len(pedestrian_group)}/{MAX_PEDESTRIANS}")
    # ---> KẾT THÚC <---
    # (Keep your spawn_random_pedestrian function, but pass speed_factor)
    if len(pedestrian_group) >= MAX_PEDESTRIANS:
        # ---> THÊM DÒNG NÀY <---
        print("  DEBUG spawn_random_pedestrian: Thoát - Đã đạt MAX.")
         # ---> KẾT THÚC <--
        return
    if not paths or not pedestrian_images: # Check if images loaded
        # ---> THÊM DÒNG NÀY <---
        print(f"  DEBUG spawn_random_pedestrian: Thoát - Paths rỗng ({not paths}) hoặc Images rỗng ({not pedestrian_images}).")
         # ---> KẾT THÚC <---
        return

    try: # Thêm try-except để bắt lỗi random.choice
        chosen_path_points = random.choice(paths)
        if not chosen_path_points or len(chosen_path_points) < 2:
             # ---> THÊM DÒNG NÀY <---
            print("  DEBUG spawn_random_pedestrian: Thoát - Path được chọn không hợp lệ (rỗng hoặc chỉ có 1 điểm).")
             # ---> KẾT THÚC <---
            return

        if random.choice([True, False]):
            start_point = chosen_path_points[0]
            path_to_follow = chosen_path_points
        else:
            start_point = chosen_path_points[-1]
            path_to_follow = chosen_path_points[::-1]

        start_x, start_y = start_point
        image = random.choice(pedestrian_images)
        base_ped_speed = PEDES_SPEED # Base speed variation
        # ---> THÊM DÒNG NÀY <---
        print(f"  DEBUG spawn_random_pedestrian: Chuẩn bị thêm Pedestrian tại ({start_x:.0f}, {start_y:.0f})")
        # ---> KẾT THÚC <---
        pedestrian = Pedestrian(start_x, start_y, image, path_to_follow, speed=base_ped_speed, speed_factor=speed_factor)
        pedestrian_group.add(pedestrian)
    # ---> THÊM DÒNG NÀY <---
        print(f"  DEBUG spawn_random_pedestrian: Đã thêm thành công! New count: {len(pedestrian_group)}")
        # ---> KẾT THÚC <---

    except IndexError as e:
            print(f"  ERROR in spawn_random_pedestrian: Lỗi khi chọn ngẫu nhiên (paths hoặc images có thể rỗng?): {e}")
    except Exception as e:
            print(f"  ERROR in spawn_random_pedestrian: Lỗi không xác định: {e}")

def process_simulation_results(results_list):
    """Calculates summary statistics from a list of run results."""
    summary = {
        "total_runs": len(results_list),
        "successful_runs": 0,
        "collisions": 0,
        "timeouts": 0,
        "path_failures": 0,
        "completion_times_ms": [],
        "path_lengths": [],
        "time_min_ms": None,
        "time_max_ms": None,
        "time_avg_ms": None,
        "path_len_min": None,
        "path_len_max": None,
        "path_len_avg": None,
        "collision_rate": 0.0,
        "timeout_rate": 0.0,
        "path_failure_rate": 0.0,
        "success_rate": 0.0,
    }

    for result in results_list:
        if result["status"] == "success":
            summary["successful_runs"] += 1
            summary["completion_times_ms"].append(result["time_ms"])
            if result["path_length"] is not None:
                summary["path_lengths"].append(result["path_length"])
        elif result["status"] == "collision":
            summary["collisions"] += 1
        elif result["status"] == "timeout":
            summary["timeouts"] += 1
        elif result["status"] == "path_fail":
            summary["path_failures"] += 1

    if summary["completion_times_ms"]:
        summary["time_min_ms"] = min(summary["completion_times_ms"])
        summary["time_max_ms"] = max(summary["completion_times_ms"])
        summary["time_avg_ms"] = statistics.mean(summary["completion_times_ms"])

    if summary["path_lengths"]:
        summary["path_len_min"] = min(summary["path_lengths"])
        summary["path_len_max"] = max(summary["path_lengths"])
        summary["path_len_avg"] = statistics.mean(summary["path_lengths"])

    if summary["total_runs"] > 0:
        summary["collision_rate"] = summary["collisions"] / summary["total_runs"]
        summary["timeout_rate"] = summary["timeouts"] / summary["total_runs"]
        summary["path_failure_rate"] = summary["path_failures"] / summary["total_runs"]
        summary["success_rate"] = summary["successful_runs"] / summary["total_runs"]

    # Remove raw lists from final summary if desired
    # del summary["completion_times_ms"]
    # del summary["path_lengths"]

    return summary

def save_results(results_data, filename):
    """Saves the results dictionary to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=4)
        print(f"Results successfully saved to {filename}")
    except IOError as e:
        print(f"Error saving results to {filename}: {e}")
    except TypeError as e:
         print(f"Error serializing results to JSON: {e}")


# === Map Setup (Sprites, Start Pos, Paths) ===
sprite_group = pygame.sprite.Group()
sprite_col = pygame.sprite.Group() # Static obstacles ONLY
pedestrian_sprites = pygame.sprite.Group()
pedestrian_paths = []
border_rects = []
Start_X, Start_Y = 0, 0

# Process map layers and objects
for layer in tmx_data.visible_layers:
    if hasattr(layer, 'data'):
        for x, y, surf in layer.tiles():
            pos = (x * CELL_SIZE, y * CELL_SIZE)
            Tile(pos=pos, surf=surf, groups=sprite_group) # Add all tiles to general group

for obj in tmx_data.objects:
    obj_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
    if obj.name == 'Border' or obj.type == 'Border':
        border_rects.append(obj_rect)
    elif obj.name == 'Start':
        Start_X, Start_Y = obj.x, obj.y # Assume TMX point is center
    elif obj.name == 'RandomCar' and obj.image:
         # Add to general group for drawing, and specific group for collision
         Tile(pos=(obj.x, obj.y), surf=obj.image, groups=(sprite_group, sprite_col))
    elif obj.name and "PedestrianPaths" in obj.name:
         # Adjust Y offset based on your Tiled setup if necessary
         y_offset = -576 # Adjust this value as needed from your original code
         # Ensure obj.points exists and is iterable
         if hasattr(obj, 'points') and obj.points:
             path_points = [(point.x + obj.x, point.y + obj.y + y_offset) for point in obj.points]
             if path_points:
                  pedestrian_paths.append(path_points)

# ---> THÊM ĐOẠN NÀY <---
print(f"\nDEBUG PATHS/IMAGES CHECK:") # Thêm dòng này để dễ thấy hơn
print(f"  Số lượng pedestrian paths đã tải: {len(pedestrian_paths)}")
if len(pedestrian_paths) > 0:
    # In ra độ dài của một vài path đầu tiên để kiểm tra
    for i, p in enumerate(pedestrian_paths[:3]): # In 3 path đầu
         print(f"    Path {i} có {len(p)} điểm.")
else:
    print("  CẢNH BÁO: Không tải được đường đi nào cho người đi bộ!")

# (Di chuyển kiểm tra images xuống đây luôn cho gọn)
print(f"  Số lượng pedestrian images đã tải: {len(pedestrian_images)}")
if not pedestrian_images:
     print("  CẢNH BÁO: Không tải được hình ảnh người đi bộ!")
print("-" * 20) # Dòng phân cách
# ---> KẾT THÚC <---
# === Main Simulation Loop ===
all_algorithm_results = {}

for algo_name in ALGORITHMS_TO_RUN:
    print(f"\n===== Starting Simulation for Algorithm: {algo_name} =====")
    pathfinding_func = get_pathfinding_function(algo_name)
    if not pathfinding_func:
        all_algorithm_results[algo_name] = {"error": f"Algorithm function '{algo_name}' not found."}
        continue

    current_algo_run_results = [] # List to store results for each run of this algo


    for run_index in range(NUM_RUNS):
        print(f"--- {algo_name} | Run {run_index + 1} / {NUM_RUNS} ---")

        # --- Reset Game State for New Run --- <--- VIỆC RESET DIỄN RA Ở ĐÂY
        car = Car(Start_X, Start_Y, car_img_original, speed_factor=SIM_SPEED_FACTOR)
        pedestrian_sprites.empty() # Clear previous pedestrians
        current_path_cells = []
        user_goal_cell = None
        user_goal_rect = None
        recalculation_needed = False
        last_path_recalc_time = 0
        RECALC_COOLDOWN = 300 # ms between path recalculations if needed

    # ---> THÊM ĐOẠN CODE SPAWN BAN ĐẦU NÀY <---
        initial_pedestrians_to_spawn = 1 # Số lượng spawn ngay lúc đầu (có thể lấy từ config)
        print(f"DEBUG: Spawning {initial_pedestrians_to_spawn} initial pedestrian(s)...")
        for _ in range(initial_pedestrians_to_spawn):
            # Gọi hàm spawn nhưng bỏ qua kiểm tra thời gian và số lượng tối đa (vì đây là spawn ban đầu)
            # Cần đảm bảo paths và images đã được tải
            if pedestrian_paths and pedestrian_images:
                # Có thể tạo một hàm spawn riêng hoặc điều chỉnh hàm cũ
                # Ví dụ đơn giản là gọi trực tiếp:
                spawn_random_pedestrian(pedestrian_paths, pedestrian_sprites, SIM_SPEED_FACTOR)
            else:
                print("WARN: Cannot spawn initial pedestrian, paths or images missing.")
                break # Thoát vòng lặp nếu thiếu dữ liệu
        print(f"DEBUG: Initial spawn done. Current peds: {len(pedestrian_sprites)}")
    # ---> KẾT THÚC ĐOẠN CODE SPAWN BAN ĐẦU <---

        # Find a random valid goal
        start_cell_approx = (int(car.center_y) // CELL_SIZE, int(car.center_x) // CELL_SIZE)
        user_goal_cell = find_random_valid_goal(base_grid, grid_rows, grid_cols, start_cell_approx)

        if user_goal_cell is None:
            print("   Failed to find valid random goal. Skipping run.")
            current_algo_run_results.append({"status": "path_fail", "reason": "no_goal"})
            continue # Skip to the next run

        user_goal_rect = pygame.Rect(user_goal_cell[1] * CELL_SIZE, user_goal_cell[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        print(f"   Goal: {user_goal_cell}")
        recalculation_needed = True # Need initial path

        # Reset timers and flags for the run
        run_start_time_ms = pygame.time.get_ticks()
        spawn_timer = run_start_time_ms
        next_spawn_interval = random.randint(MIN_TIME_PEDES_SPAWN, MAX_TIME_PEDES_SPAWN)
        simulation_running = True
        run_status = "running" # 'success', 'collision', 'timeout', 'path_fail'
        run_time_ms = 0
        run_path_length = None

        # --- Single Run Loop ---
        while simulation_running:
            current_time_ms = pygame.time.get_ticks()
            delta_time = clock.tick(FPS) / 1000.0 # Time since last frame in seconds

            # 1. Check for Timeout
            # ====================
            run_time_ms = current_time_ms - run_start_time_ms
            if run_time_ms > MAX_RUN_TIME_MS:
                print("   Run timed out.")
                run_status = "timeout"
                simulation_running = False
                continue # Go to end of loop check

            # 2. Handle Events
            # =================
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Quit event received. Shutting down.")
                    save_results(all_algorithm_results, RESULTS_FILE) # Save progress
                    pygame.quit()
                    sys.exit()

            # 3. Pedestrian Spawning
            # =======================
            time_since_last_spawn = current_time_ms - spawn_timer
            should_spawn_time = time_since_last_spawn > next_spawn_interval
            paths_exist = bool(pedestrian_paths)
            images_exist = bool(pedestrian_images)
            can_spawn_more = len(pedestrian_sprites) < MAX_PEDESTRIANS

            # Debug print for spawn check
            if should_spawn_time:
                 print(f"DEBUG SPAWN CHECK @ {current_time_ms}ms: TimeOK={should_spawn_time}, PathsOK={paths_exist}, ImagesOK={images_exist}, SpaceOK={can_spawn_more}, NextInterval={next_spawn_interval}ms")

            if should_spawn_time and paths_exist and images_exist and can_spawn_more:
                 print(f"DEBUG: Calling spawn_random_pedestrian (Time: {current_time_ms}ms, Current Peds: {len(pedestrian_sprites)})")
                 spawn_random_pedestrian(pedestrian_paths, pedestrian_sprites, SIM_SPEED_FACTOR)
                 spawn_timer = current_time_ms # Reset timer AFTER successful spawn call
                 next_spawn_interval = random.randint(MIN_TIME_PEDES_SPAWN, MAX_TIME_PEDES_SPAWN)
                 print(f"DEBUG: Timer reset. Next spawn interval: {next_spawn_interval}ms")

            # 4. Pedestrian Movement
            # =====================
            pedestrian_sprites.update()

            # 5. Pathfinding Logic (Recalculation if needed)
            # ==============================================
            # Check if car is stuck
            STUCK_TIMEOUT_MS = 2000 # 2 giây
            is_stuck = False
            if car.is_stopped and car.stopped_since > 0:
                time_stopped = current_time_ms - car.stopped_since
                if time_stopped > STUCK_TIMEOUT_MS:
                    is_stuck = True
                    # print(f"   Car stuck for {time_stopped:.0f}ms.") # Debug print moved inside if block below

            # Determine if recalculation is needed
            should_recalculate = (recalculation_needed  # Explicit request
                                  or is_stuck             # Car is stuck
                                  or (user_goal_cell and not car.path)) # Has goal but no path

            # Check if cooldown period has passed
            can_recalculate_now = current_time_ms - last_path_recalc_time > RECALC_COOLDOWN

            # Perform recalculation if all conditions met
            if user_goal_cell and should_recalculate and can_recalculate_now:
                print("   Recalculating path (Trigger: Need={}, Stuck={}, NoPath={})".format(recalculation_needed, is_stuck, not car.path))

                # Create temporary grid with current obstacles
                temp_grid = [row[:] for row in base_grid]
                for ped in pedestrian_sprites:
                    ped_col = ped.rect.centerx // CELL_SIZE
                    ped_row = ped.rect.centery // CELL_SIZE
                    if 0 <= ped_row < grid_rows and 0 <= ped_col < grid_cols:
                        temp_grid[ped_row][ped_col] = 1

                # Get car's current grid position
                car_col = int(car.center_x) // CELL_SIZE
                car_row = int(car.center_y) // CELL_SIZE
                start_cell = (car_row, car_col)

                path_found = False # Reset flag

                # Check if start cell is valid before calling A*
                if 0 <= start_cell[0] < grid_rows and 0 <= start_cell[1] < grid_cols:
                    if temp_grid[start_cell[0]][start_cell[1]] == 0: # Check if blocked in temp_grid
                        print(f"   Running A* from {start_cell} to {user_goal_cell}")
                        new_path = pathfinding_func(temp_grid, start_cell, user_goal_cell)
                        if new_path:
                            print(f"   Path found by A*: Length={len(new_path)}")
                            current_path_cells = new_path
                            car.set_path(current_path_cells)
                            path_found = True
                            run_path_length = len(current_path_cells) # Optional: update path length metric
                        else:
                            print("   No path found by A* (possibly blocked).")
                            # Clear path if A* fails
                            car.set_path([])
                            current_path_cells = []
                    else:
                        print(f"   Cannot calculate path: Car start cell {start_cell} is blocked in temp_grid.")
                        car.set_path([])
                        current_path_cells = []
                else:
                     print(f"   Cannot calculate path: Car start cell {start_cell} is outside grid bounds.")
                     car.set_path([])
                     current_path_cells = []

                # Reset stuck timer AFTER attempting recalculation, regardless of success
                if is_stuck:
                    car.stopped_since = current_time_ms

                recalculation_needed = False # Reset explicit request flag
                last_path_recalc_time = current_time_ms # Update last recalc time

            # 6. Car Movement
            # ================
            # Car updates its own 'is_stopped' and 'stopped_since' internally
            car.move_towards_path(pedestrian_sprites, True)

            # 7. Collision Checks
            # ====================
            collision_this_frame = False
            # Check Borders
            for border in border_rects:
                if car.rect.colliderect(border):
                    collision_this_frame = True
                    break
            # Check Static Obstacles
            if not collision_this_frame:
                collided_statics = pygame.sprite.spritecollide(car, sprite_col, False, pygame.sprite.collide_mask)
                if collided_statics:
                    collision_this_frame = True
            # Check Pedestrians
            if not collision_this_frame:
                 collided_peds = pygame.sprite.spritecollide(car, pedestrian_sprites, False, pygame.sprite.collide_mask)
                 if collided_peds:
                     collision_this_frame = True

            # Handle Collision Result
            if collision_this_frame:
                print("   Collision detected.")
                run_status = "collision"
                simulation_running = False
                continue # Go to end of loop check

            # 8. Goal Arrival Check
            # =====================
            # Check only if simulation is still running (no collision occurred)
            if simulation_running:
                # Check if car has logically finished its path
                if car.path and car.target_index >= len(car.path):
                    is_goal_cell_occupied = False
                    if user_goal_cell:
                        goal_row, goal_col = user_goal_cell
                        for ped in pedestrian_sprites:
                            ped_col = ped.rect.centerx // CELL_SIZE
                            ped_row = ped.rect.centery // CELL_SIZE
                            if ped_row == goal_row and ped_col == goal_col:
                                is_goal_cell_occupied = True
                                print(f"   Goal cell {user_goal_cell} blocked by pedestrian. Waiting...")
                                break

                    if is_goal_cell_occupied:
                        # Goal blocked, clear path to trigger recalculation later when it's free
                        car.set_path([])
                        current_path_cells = []
                        # Keep simulation_running = True
                    else:
                        # Path finished AND goal cell is clear! Success!
                        print(f"   Goal reached! (Path index {car.target_index} >= Length {len(car.path)} AND Goal cell clear)")
                        run_status = "success"
                        simulation_running = False
                        # No continue needed, loop will terminate

            # 9. Drawing
            # ===========
            if not RUN_HEADLESS and screen:
                screen.fill((100, 100, 100))
                sprite_group.draw(screen) # Draw map tiles and static obstacles

                # Draw goal marker
                if user_goal_rect:
                    s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    s.fill((0, 255, 0, 100))
                    screen.blit(s, user_goal_rect.topleft)
                    pygame.draw.rect(screen, (255, 255, 255), user_goal_rect, 1)
                
                # --- Draw Car Path ---
                if current_path_cells:  # Chỉ vẽ nếu có đường đi hiện tại
                    PATH_COLOR_FUTURE = (255, 0, 0)  # Màu đỏ cho các điểm sắp tới
                    PATH_COLOR_PAST = (255, 120, 120) # Màu xám (hoặc đỏ mờ) cho các điểm đã qua
                    # Bạn cũng có thể dùng màu đỏ mờ: PATH_COLOR_PAST = (150, 50, 50)
                    DOT_RADIUS = 4  # Kích thước của chấm

                    # Lặp qua từng ô (cell) trong đường đi hiện tại
                    for i, cell in enumerate(current_path_cells):
                        row, col = cell
                        # Chuyển đổi tọa độ grid (ô) sang tọa độ pixel (điểm ảnh) ở tâm ô
                        center_x = col * CELL_SIZE + CELL_SIZE // 2
                        center_y = row * CELL_SIZE + CELL_SIZE // 2

                        # Kiểm tra xem điểm này là điểm sắp tới hay đã đi qua
                        # car.target_index là chỉ số của điểm tiếp theo mà xe đang hướng tới
                        if i >= car.target_index:
                            color_to_use = PATH_COLOR_FUTURE
                        else:
                            color_to_use = PATH_COLOR_PAST

                        # Vẽ chấm tròn tại vị trí tương ứng
                        pygame.draw.circle(screen, color_to_use, (center_x, center_y), DOT_RADIUS)
                # Draw pedestrians
                pedestrian_sprites.draw(screen)
                # Draw car
                car.draw(screen)
                # Draw run info text
                draw_text(f"Algo: {algo_name}", font, TEXT_COL, 10, 10, screen)
                draw_text(f"Run: {run_index + 1}/{NUM_RUNS}", font, TEXT_COL, 10, 50, screen)
                draw_text(f"Time: {run_time_ms/1000:.1f}s", font, TEXT_COL, 10, 90, screen)
                draw_text(f"Status: {run_status}", font, TEXT_COL, 10, 130, screen)
                # Optional: Draw car path debug
                # if current_path_cells: ...

                pygame.display.flip()

            # End of main simulation loop (while simulation_running:)
            # Loop condition (simulation_running) will be checked next iteration

        # --- End of Single Run Loop ---
        # (Code to record results for this run remains the same)
        # ...
        current_algo_run_results.append({
            "status": run_status,
            "time_ms": run_time_ms if run_status == "success" else None,
            "path_length": run_path_length if run_status == "success" else None,
            "reason": "" # Could add more detail for failures
        })
        # Brief pause if running visually
        if not RUN_HEADLESS:
             pygame.time.wait(50) # Short pause to see result before next run


    # --- End of All Runs for One Algorithm ---
    # Process and store the results for this algorithm
    print(f"\n--- Results Summary for Algorithm: {algo_name} ---")
    processed_results = process_simulation_results(current_algo_run_results)
    all_algorithm_results[algo_name] = processed_results
    # Print summary to console
    for key, value in processed_results.items():
        if isinstance(value, float):
             print(f"   {key}: {value:.3f}")
        else:
             print(f"   {key}: {value}")


# --- End of All Algorithms ---
print("\n===== Simulation Complete =====")
# Save all results
save_results(all_algorithm_results, RESULTS_FILE)

pygame.quit()
sys.exit()