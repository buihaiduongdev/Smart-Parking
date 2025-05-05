import pygame
import math
import sys
import random
import json
import time
import statistics
import tkinter as tk 
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import analysis_ui 

from pytmx.util_pygame import load_pygame
import Button 
from typing import Tuple, List, Set, Optional, Union, FrozenSet 

from pathfinding import (
    Grid, Point, Path, BeliefStatePoint, 
    a_star, bfs, dfs,
    simple_hill_climbing,
    backtracking,
    sensorless_search,      
    q_learning_pathfinding,
    count_turns
)

pygame.init()

CONFIG_FILE = "./Data/config_hard.json"
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)

    ALGORITHMS_TO_RUN = config.get("algorithms_to_run", ["a_star"])
    NUM_RUNS = config.get("num_runs_per_algorithm", 5)
    SIM_SPEED_FACTOR = config.get("simulation_speed_factor", 1.0)
    RUN_HEADLESS = config.get("run_headless", False)
    MAX_RUN_TIME_MS = config.get("max_run_time_ms", 60000)

    RESULTS_FILE = "./Data/simulation_results.json"
    MAX_PEDESTRIANS = config.get("max_pedestrians", 5)
    MIN_TIME_PEDES_SPAWN = config.get("min_pedestrian_spawn_interval_ms", 1000)
    MAX_TIME_PEDES_SPAWN = config.get("max_pedestrian_spawn_interval_ms", 2000)
    PEDES_SPEED = config.get("pedestrian_speed", 1)

    QL_EPISODES = config.get("q_learning_episodes", 10000) 
    QL_MAX_SOLVE_STEPS = config.get("q_learning_max_solve_steps", 500) 
    SENSORLESS_TIMEOUT = config.get("sensorless_timeout_ms", 10000) 

    print("--- Configuration ---")
    print(f"Algorithms: {ALGORITHMS_TO_RUN}")
    print(f"Runs per Algo: {NUM_RUNS}")
    print(f"Speed Factor: {SIM_SPEED_FACTOR}")
    print(f"Headless: {RUN_HEADLESS}")
    print(f"Max Run Time: {MAX_RUN_TIME_MS} ms")
    print(f"Max Pedestrians: {MAX_PEDESTRIANS}")
    print(f"Results File: {RESULTS_FILE}")
    print(f"QL Episodes: {QL_EPISODES}") 
    print(f"Sensorless Timeout: {SENSORLESS_TIMEOUT} ms") 
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

CELL_SIZE = config.get("cell_size", 64)
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
screen = None
if not RUN_HEADLESS:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Simulation Comparison - Sensorless & QL Added")
clock = pygame.time.Clock()
FPS = 60

try:
    car_img_original = pygame.image.load("./PNG/App/car7.png").convert_alpha()
    CAR_WIDTH, CAR_HEIGHT = car_img_original.get_size()
except pygame.error as e:
    print(f"Error loading car image: {e}. Using placeholder.")
    CAR_WIDTH, CAR_HEIGHT = 43, 74
    car_img_original = pygame.Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
    car_img_original.fill((255, 165, 0))

pedestrian_images = []
try:

    pedestrian_images = [ pygame.image.load(f"./PNG/Other/Person_{name}.png").convert_alpha() for name in ["BlueBlack1", "RedBlack1", "YellowBrown2", "RedBlond1", "PurpleBrown1", "OrangeBrown1", "GreenBlack2"] ]
except pygame.error as e:
    print(f"Warning: Error loading pedestrian images: {e}")

font = None
TEXT_COL = (255, 255, 255)
if not RUN_HEADLESS:
    try:
        font = pygame.font.SysFont("calibri", 36)
    except Exception as e:
        print(f"Warning: Error loading font: {e}")

try:
    tmx_data = load_pygame("map.tmx")
except FileNotFoundError:
    print("Error: map.tmx not found. Exiting.")
    sys.exit()
except Exception as e:
    print(f"Error loading map: {e}. Exiting.")
    sys.exit()

base_grid: Optional[Grid] = None
grid_rows: int = 0
grid_cols: int = 0
static_obstacle_rects: List[pygame.Rect] = []

def create_grid_from_map(tmx_data, cell_size):

    global grid_rows, grid_cols 
    width_px = tmx_data.width * tmx_data.tilewidth
    height_px = tmx_data.height * tmx_data.tileheight
    grid_cols = width_px // cell_size
    grid_rows = height_px // cell_size
    print(f"Creating grid: {grid_rows} rows, {grid_cols} cols")
    grid = [[0 for _ in range(grid_cols)] for _ in range(grid_rows)] 
    static_obs_rects = []

    for obj in tmx_data.objects:
        is_obstacle_type = obj.name in ['Border', 'RandomCar'] or obj.type == 'Border'
        if is_obstacle_type:
            left = int(obj.x) // cell_size
            top = int(obj.y) // cell_size
            right = math.ceil((obj.x + obj.width) / cell_size)
            bottom = math.ceil((obj.y + obj.height) / cell_size)
            for r in range(top, bottom):
                for c in range(left, right):
                    if 0 <= r < grid_rows and 0 <= c < grid_cols:
                        grid[r][c] = 1
            if obj.name == 'RandomCar':
                 static_obs_rects.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    return grid, static_obs_rects

base_grid, static_obstacle_rects = create_grid_from_map(tmx_data, CELL_SIZE)
if not base_grid:
    print("Error: Failed to create grid from map. Exiting.")
    sys.exit()

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Car:

    def __init__(self, center_x, center_y, original_image, speed_factor=1.0):
        self.center_x = float(center_x)
        self.center_y = float(center_y)
        self.original_surface = original_image
        self.surface = self.original_surface
        self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
        self.mask = pygame.mask.from_surface(self.surface)
        self.angle = 0.0
        self.speed = 0.0
        self.max_speed = 2.0 * speed_factor
        self.rotation_speed = 4.0
        self.path: Path = []
        self.target_index = 0
        self.collision_flag = False
        self.is_stopped = True
        self.stopped_since = 0
        self.STOPPED_THRESHOLD = 0.1

    def set_path(self, new_path: Optional[Path]):
        if new_path:
             self.path = new_path
             self.target_index = 0
        else:
             self.path = []
             self.target_index = 0

    def move_towards_path(self):
        self.collision_flag = False
        if not self.path or self.target_index >= len(self.path):
            self.speed = 0
            now = pygame.time.get_ticks()
            if not self.is_stopped:
                self.is_stopped = True
                self.stopped_since = now

            self.surface = pygame.transform.rotate(self.original_surface, -self.angle)
            self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
            self.mask = pygame.mask.from_surface(self.surface)
            return

        current_max_speed = self.max_speed
        target_row, target_col = self.path[self.target_index]
        target_x = target_col * CELL_SIZE + CELL_SIZE // 2
        target_y = target_row * CELL_SIZE + CELL_SIZE // 2

        dx = target_x - self.center_x
        dy = target_y - self.center_y
        distance_to_target = math.hypot(dx, dy)
        angle_diff = 0.0
        if distance_to_target > 1.0:
            target_angle_rad = math.atan2(-dy, dx)
            target_angle_deg = math.degrees(target_angle_rad)
            desired_angle = (90 - target_angle_deg) % 360
            angle_diff = (desired_angle - self.angle + 180) % 360 - 180

        alignment_tolerance = 1.0
        if abs(angle_diff) > alignment_tolerance:
            direction = 1 if angle_diff > 0 else -1
            rotation_magnitude = min(self.rotation_speed, abs(angle_diff))
            self.angle = (self.angle + direction * rotation_magnitude) % 360

        turn_slowdown_threshold = 15.0
        max_angle_diff_for_speed = 90.0
        if abs(angle_diff) <= turn_slowdown_threshold:
            actual_speed = current_max_speed
        else:
            excess_angle = abs(angle_diff) - turn_slowdown_threshold
            range_angle = max(1.0, max_angle_diff_for_speed - turn_slowdown_threshold)
            reduction_factor = max(0.0, 1.0 - (excess_angle / range_angle))
            actual_speed = current_max_speed * reduction_factor
            actual_speed = max(0.0, actual_speed)

        now = pygame.time.get_ticks()
        if actual_speed < self.STOPPED_THRESHOLD:
            if not self.is_stopped:
                self.is_stopped = True
                self.stopped_since = now
        else:
            if self.is_stopped:
                 self.is_stopped = False
                 self.stopped_since = 0

        self.speed = actual_speed
        if self.speed > 0.01:
            move_angle_rad = math.radians(90 - self.angle)
            move_x = math.cos(move_angle_rad) * self.speed
            move_y = -math.sin(move_angle_rad) * self.speed
            self.center_x += move_x
            self.center_y += move_y

        self.surface = pygame.transform.rotate(self.original_surface, -self.angle)
        self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
        self.mask = pygame.mask.from_surface(self.surface)

        final_dx = target_x - self.center_x
        final_dy = target_y - self.center_y
        final_distance_to_target = math.hypot(final_dx, final_dy)
        arrival_threshold = CELL_SIZE * 0.6

        if self.path and self.target_index < len(self.path):
            if final_distance_to_target < arrival_threshold:
                 self.target_index += 1

    def draw(self, target_surface):
        if target_surface:
            target_surface.blit(self.surface, self.rect.topleft)

class Pedestrian(pygame.sprite.Sprite):

    def __init__(self, x, y, surface, path_points: List[Tuple[float, float]], speed=1, speed_factor=1.0):
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect(center=(x, y))
        self.x = float(x)
        self.y = float(y)
        self.base_speed = speed
        self.speed = self.base_speed * speed_factor
        self.path_points = path_points
        self.target_point_index = 0
        self.mask = pygame.mask.from_surface(self.image)
        if not self.path_points:
             self.kill()

    def update(self):
        if self.target_point_index >= len(self.path_points):
            self.kill()
            return

        target_x, target_y = self.path_points[self.target_point_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)
        arrival_threshold = self.speed * 1.5

        if distance < arrival_threshold:
            self.target_point_index += 1
            if self.target_point_index >= len(self.path_points):
                self.kill()
                return
            target_x, target_y = self.path_points[self.target_point_index]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy)

        if distance > 0:
            dir_x = dx / distance
            dir_y = dy / distance
            self.x += dir_x * self.speed
            self.y += dir_y * self.speed
            self.rect.center = (int(self.x), int(self.y))

def draw_text(text, font_obj, color, x, y, surface):
    if font_obj and surface:
        img = font_obj.render(text, True, color)
        surface.blit(img, (x, y))

def get_pathfinding_function(algo_name: str):
    if algo_name == "a_star": return a_star
    elif algo_name == "bfs": return bfs
    elif algo_name == "dfs": return dfs
    elif algo_name == "simple_hill_climbing": return simple_hill_climbing
    elif algo_name == "backtracking": return backtracking
    elif algo_name == "sensorless_search": return sensorless_search 
    elif algo_name == "q_learning": return q_learning_pathfinding 
    else:
        print(f"Warning: Pathfinding algorithm '{algo_name}' not found or mapped.")
        return None

def find_random_valid_goal(grid: Grid, grid_rows: int, grid_cols: int, start_cell: Point) -> Optional[Point]:

    attempts = 0
    max_attempts = grid_rows * grid_cols
    while attempts < max_attempts:
        rand_row = random.randint(0, grid_rows - 1)
        rand_col = random.randint(0, grid_cols - 1)
        goal_cell: Point = (rand_row, rand_col)
        if grid[rand_row][rand_col] == 0 and goal_cell != start_cell:
             return goal_cell
        attempts += 1
    print("Warning: Could not find a random valid goal after many attempts.")
    return None

def spawn_random_pedestrian(paths: List[List[Tuple[float, float]]], pedestrian_group: pygame.sprite.Group, speed_factor: float):

    if len(pedestrian_group) >= MAX_PEDESTRIANS: return
    if not paths or not pedestrian_images: return

    try:
        chosen_path_points = random.choice(paths)
        if not chosen_path_points or len(chosen_path_points) < 2: return

        if random.choice([True, False]):
            start_point = chosen_path_points[0]
            path_to_follow = chosen_path_points
        else:
            start_point = chosen_path_points[-1]
            path_to_follow = chosen_path_points[::-1]

        start_x, start_y = start_point
        image = random.choice(pedestrian_images)
        base_ped_speed = PEDES_SPEED
        pedestrian = Pedestrian(start_x, start_y, image, path_to_follow, speed=base_ped_speed, speed_factor=speed_factor)
        pedestrian_group.add(pedestrian)

    except Exception as e:
            print(f"ERROR in spawn_random_pedestrian: {e}")

def process_simulation_results(results_list):

    summary = {
        "total_runs": len(results_list), "successful_runs": 0, "collisions": 0,
        "timeouts": 0, "path_failures": 0, "completion_times_ms": [],
        "path_lengths": [], "action_counts": [], 
        "time_min_ms": None, "time_max_ms": None, "time_avg_ms": None,
        "path_len_min": None, "path_len_max": None, "path_len_avg": None,
        "turns": [],
        "turns_min": None,
        "turns_max": None,
        "turns_avg": None,
        "collision_rate": 0.0, "timeout_rate": 0.0, "path_failure_rate": 0.0,
        "success_rate": 0.0,
    }
    for result in results_list:
        if result["status"] == "success":
            summary["successful_runs"] += 1
            if result["time_ms"] is not None:
                 summary["completion_times_ms"].append(result["time_ms"])
            if result.get("turns") is not None:
                summary["turns"].append(result["turns"])

            if result.get("path_length") is not None: 
                summary["path_lengths"].append(result["path_length"])
            elif result.get("action_count") is not None: 
                summary["action_counts"].append(result["action_count"])

        elif result["status"] == "collision": summary["collisions"] += 1
        elif result["status"] == "timeout": summary["timeouts"] += 1
        elif result["status"] == "path_fail": summary["path_failures"] += 1
    if summary["turns"]: # <-- Tính toán cho turns
        summary["turns_min"] = min(summary["turns"])
        summary["turns_max"] = max(summary["turns"])
        summary["turns_avg"] = statistics.mean(summary["turns"])
        
    if summary["completion_times_ms"]:
        summary["time_min_ms"] = min(summary["completion_times_ms"])
        summary["time_max_ms"] = max(summary["completion_times_ms"])
        summary["time_avg_ms"] = statistics.mean(summary["completion_times_ms"])
    if summary["path_lengths"]:
        summary["path_len_min"] = min(summary["path_lengths"])
        summary["path_len_max"] = max(summary["path_lengths"])
        summary["path_len_avg"] = statistics.mean(summary["path_lengths"])
    if summary["action_counts"]:
        summary["action_count_min"] = min(summary["action_counts"])
        summary["action_count_max"] = max(summary["action_counts"])
        summary["action_count_avg"] = statistics.mean(summary["action_counts"])
    if summary["total_runs"] > 0:
        summary["collision_rate"] = summary["collisions"] / summary["total_runs"]
        summary["timeout_rate"] = summary["timeouts"] / summary["total_runs"]
        summary["path_failure_rate"] = summary["path_failures"] / summary["total_runs"]
        summary["success_rate"] = summary["successful_runs"] / summary["total_runs"]
    return summary

def save_results(results_data, filename):

    try:
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=4)
        print(f"Results successfully saved to {filename}")
    except IOError as e: print(f"Error saving results to {filename}: {e}")
    except TypeError as e: print(f"Error serializing results to JSON: {e}")

sprite_group = pygame.sprite.Group()
sprite_col = pygame.sprite.Group()
pedestrian_sprites = pygame.sprite.Group()
pedestrian_paths: List[List[Tuple[float, float]]] = []
border_rects: List[pygame.Rect] = []
Start_X, Start_Y = 0, 0

for layer in tmx_data.visible_layers:
    if hasattr(layer, 'data'):
        for x, y, surf in layer.tiles():
            Tile(pos=(x * CELL_SIZE, y * CELL_SIZE), surf=surf, groups=sprite_group)

for obj in tmx_data.objects:
    obj_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
    if obj.name == 'Border' or obj.type == 'Border': border_rects.append(obj_rect)
    elif obj.name == 'Start': Start_X, Start_Y = obj.x, obj.y
    elif obj.name == 'RandomCar' and obj.image: Tile(pos=(obj.x, obj.y), surf=obj.image, groups=(sprite_group, sprite_col))
    elif obj.name and "PedestrianPaths" in obj.name:
         y_offset = -576
         if hasattr(obj, 'points') and obj.points:
             path_points = [(point.x + obj.x, point.y + obj.y + y_offset) for point in obj.points]
             if len(path_points) >= 2: pedestrian_paths.append(path_points)

print(f"Loaded {len(pedestrian_paths)} pedestrian paths.")
if not pedestrian_paths: print("Warning: No pedestrian paths loaded.")
if not pedestrian_images: print("Warning: No pedestrian images loaded.")

all_algorithm_results = {}

for algo_name in ALGORITHMS_TO_RUN:
    print(f"\n===== Starting Simulation for Algorithm: {algo_name} =====")
    pathfinding_func = get_pathfinding_function(algo_name)
    if not pathfinding_func:
        print(f"Error: Algorithm function for '{algo_name}' not found. Skipping.")
        all_algorithm_results[algo_name] = {"error": f"Algorithm function '{algo_name}' not found."}
        continue

    current_algo_run_results = []

    for run_index in range(NUM_RUNS):
        print(f"--- {algo_name} | Run {run_index + 1} / {NUM_RUNS} ---")

        car = Car(Start_X, Start_Y, car_img_original, speed_factor=SIM_SPEED_FACTOR)
        pedestrian_sprites.empty()
        current_path_cells: Optional[Union[Path, List[str]]] = None 
        user_goal_cell: Optional[Point] = None
        user_goal_rect: Optional[pygame.Rect] = None

        initial_pedestrians_to_spawn = random.randint(0, min(2, MAX_PEDESTRIANS))

        start_cell_approx: Point = (int(car.center_y) // CELL_SIZE, int(car.center_x) // CELL_SIZE)
        user_goal_cell = find_random_valid_goal(base_grid, grid_rows, grid_cols, start_cell_approx)
        if user_goal_cell is None:
            print("   Failed to find valid random goal. Skipping run.")
            current_algo_run_results.append({"status": "path_fail", "reason": "no_goal", "time_ms": 0, "path_length": None})
            continue
        if not RUN_HEADLESS:
            user_goal_rect = pygame.Rect(user_goal_cell[1] * CELL_SIZE, user_goal_cell[0] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        print(f"   Goal set to: {user_goal_cell}")

        path_calculated = False
        run_path_length = None 
        run_action_count = None 
        calculation_time_ms = 0.0

        car_start_cell: Point = (int(car.center_y) // CELL_SIZE, int(car.center_x) // CELL_SIZE)

        if not (0 <= car_start_cell[0] < grid_rows and 0 <= car_start_cell[1] < grid_cols and base_grid[car_start_cell[0]][car_start_cell[1]] == 0):
            print(f"   Cannot calculate initial path: Start cell {car_start_cell} is invalid or blocked.")
            current_algo_run_results.append({"status": "path_fail", "reason": "invalid_start", "time_ms": 0, "path_length": None})
            continue

        print(f"   Calculating initial path/plan from {car_start_cell} to {user_goal_cell} using {algo_name}...")
        path_calc_start_time = time.time()
        calculated_result = None 

        try:

            if algo_name == "sensorless_search":

                initial_belief: BeliefStatePoint = {car_start_cell}

                calculated_result = sensorless_search(base_grid, initial_belief, user_goal_cell, SENSORLESS_TIMEOUT)

            elif algo_name == "q_learning":

                calculated_result = q_learning_pathfinding(base_grid, car_start_cell, user_goal_cell,
                                                           episodes=QL_EPISODES,
                                                           max_steps_solve=QL_MAX_SOLVE_STEPS)
            else:

                calculated_result = pathfinding_func(base_grid, car_start_cell, user_goal_cell)

            calculation_time_ms = (time.time() - path_calc_start_time) * 1000
            print(f"   Calculation took: {calculation_time_ms:.2f} ms")

            run_turns = None
            if calculated_result is not None:
                path_calculated = True
                if algo_name == "sensorless_search":

                    current_path_cells = calculated_result 
                    run_action_count = len(calculated_result)
                    print(f"   Sensorless plan found. Action Count: {run_action_count}")

                    car.set_path(None)
                elif algo_name == "q_learning":

                     current_path_cells = calculated_result
                     run_path_length = len(calculated_result)
                     car.set_path(current_path_cells)
                     if current_path_cells and isinstance(current_path_cells, list):
                        run_turns = count_turns(current_path_cells)
                     else:
                         run_turns = None
                     print(f"   Q-Learning path found. Length: {run_path_length}")
                else:

                     current_path_cells = calculated_result
                     run_path_length = len(calculated_result)
                     car.set_path(current_path_cells)
                     run_turns = count_turns(current_path_cells) # <-- GỌI HÀM COUNT_TURNS
                     print(f"Path: {current_path_cells}")
                     print(f"Turns: {run_turns}")
                     print(f"   Path found. Length: {run_path_length}")
            else:
                print(f"   Failed to find an initial path/plan using {algo_name}.")
                current_algo_run_results.append({"status": "path_fail", "reason": f"{algo_name}_initial_fail", "time_ms": calculation_time_ms, "path_length": None})
                continue 

        except Exception as e:
            calculation_time_ms = (time.time() - path_calc_start_time) * 1000
            print(f"   ERROR during {algo_name} calculation: {e}")
            import traceback
            traceback.print_exc()
            current_algo_run_results.append({"status": "path_fail", "reason": f"{algo_name}_runtime_error", "time_ms": calculation_time_ms, "path_length": None})
            continue 

        run_start_time_ms = pygame.time.get_ticks()
        spawn_timer = run_start_time_ms
        next_spawn_interval = random.randint(MIN_TIME_PEDES_SPAWN, MAX_TIME_PEDES_SPAWN)
        simulation_running = True
        run_status = "running"
        run_time_ms = 0

        if algo_name == "sensorless_search" and path_calculated:
            print("   Sensorless run complete (plan found).")
            run_status = "success"
            run_time_ms = calculation_time_ms 
            simulation_running = False 

            current_algo_run_results.append({
                "status": run_status,
                "time_ms": run_time_ms if run_status == "success" else calculation_time_ms, 
                "path_length": run_path_length if run_status == "success" and run_path_length is not None else None,
                "action_count": run_action_count if run_status == "success" and run_action_count is not None else None,
                "turns": run_turns if run_turns is not None else None
            })
            continue 

        while simulation_running:
            current_time_ms = pygame.time.get_ticks()

            run_time_ms = current_time_ms - run_start_time_ms
            if run_time_ms > MAX_RUN_TIME_MS:
                print("   Run timed out during simulation.")
                run_status = "timeout"
                simulation_running = False
                continue

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("Quit event received. Saving progress and exiting.")
                    processed_results = process_simulation_results(current_algo_run_results)
                    all_algorithm_results[algo_name] = processed_results
                    save_results(all_algorithm_results, RESULTS_FILE)
                    pygame.quit()
                    sys.exit()

            # time_since_last_spawn = current_time_ms - spawn_timer
            # if time_since_last_spawn > next_spawn_interval:
            #     spawn_random_pedestrian(pedestrian_paths, pedestrian_sprites, SIM_SPEED_FACTOR)
            #     spawn_timer = current_time_ms
            #     next_spawn_interval = random.randint(MIN_TIME_PEDES_SPAWN, MAX_TIME_PEDES_SPAWN)

            pedestrian_sprites.update()

            car.move_towards_path()

            collision_detected = False
            for border in border_rects:
                if car.rect.colliderect(border): collision_detected = True; break
            if not collision_detected:
                if pygame.sprite.spritecollide(car, sprite_col, False, pygame.sprite.collide_mask): collision_detected = True
            if not collision_detected:
                 if pygame.sprite.spritecollide(car, pedestrian_sprites, False, pygame.sprite.collide_mask): collision_detected = True

            if collision_detected:
                print("   Collision detected during simulation.")
                run_status = "collision"
                simulation_running = False
                continue

            if car.path and car.target_index >= len(car.path):
                 print(f"   Goal reached by car!")
                 run_status = "success"
                 simulation_running = False

            if not RUN_HEADLESS and screen:
                screen.fill((100, 100, 100))
                sprite_group.draw(screen)

                if user_goal_rect:
                    s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    s.fill((0, 255, 0, 80))
                    screen.blit(s, user_goal_rect.topleft)
                    pygame.draw.rect(screen, (255, 255, 255), user_goal_rect, 1)

                if isinstance(current_path_cells, list) and all(isinstance(p, tuple) for p in current_path_cells):
                    PATH_COLOR_FUTURE = (255, 0, 0, 200)
                    PATH_COLOR_PAST = (150, 150, 150, 150)
                    DOT_RADIUS = 3
                    for i, cell in enumerate(current_path_cells):
                        center_x = cell[1] * CELL_SIZE + CELL_SIZE // 2
                        center_y = cell[0] * CELL_SIZE + CELL_SIZE // 2
                        color_to_use = PATH_COLOR_FUTURE if i >= car.target_index else PATH_COLOR_PAST
                        pygame.draw.circle(screen, color_to_use, (center_x, center_y), DOT_RADIUS)

                pedestrian_sprites.draw(screen)
                car.draw(screen)

                draw_text(f"Algorithm: {algo_name}", font, TEXT_COL, 10, 10, screen)
                draw_text(f"Run: {run_index + 1}/{NUM_RUNS}", font, TEXT_COL, 10, 45, screen)
                draw_text(f"Time: {run_time_ms/1000:.1f}s", font, TEXT_COL, 10, 80, screen)
                draw_text(f"Status: {run_status}", font, TEXT_COL, 10, 115, screen)
                draw_text(f"Peds: {len(pedestrian_sprites)}/{MAX_PEDESTRIANS}", font, TEXT_COL, 10, 150, screen)

                pygame.display.flip()
            else:

                 clock.tick(FPS*10) 

        if algo_name != "sensorless_search" or not path_calculated: 
            print(f"   Run finished with status: {run_status}")
            current_algo_run_results.append({
                "status": run_status,
                "time_ms": run_time_ms if run_status == "success" else calculation_time_ms, 
                "path_length": run_path_length if run_status == "success" and run_path_length is not None else None,
                "action_count": run_action_count if run_status == "success" and run_action_count is not None else None, 
                "turns": run_turns if run_turns is not None else None,
            })

        if not RUN_HEADLESS:
             pygame.time.wait(50)

    print(f"\n--- Results Summary for Algorithm: {algo_name} ---")
    processed_results = process_simulation_results(current_algo_run_results)
    all_algorithm_results[algo_name] = processed_results

    for key, value in processed_results.items():
        if isinstance(value, float): print(f"   {key}: {value:.3f}")
        else: print(f"   {key}: {value}")

    save_results(all_algorithm_results, RESULTS_FILE)

print("\n===== Simulation Complete =====")
save_results(all_algorithm_results, RESULTS_FILE)
pygame.quit()

try:
    print("Launching Analysis UI...")
    analysis_ui.launch_analysis_ui()
except NameError: print("Analysis UI module not found.")
except Exception as e: print(f"Error launching analysis UI: {e}")

print("Exiting script.")
sys.exit()