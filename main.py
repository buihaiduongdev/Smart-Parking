import pygame, math, sys, random, heapq
from pytmx.util_pygame import load_pygame
import Button
from PIL import Image
# Khởi tạo Pygame
pygame.init()



# === Cấu hình ===
CELL_SIZE = 64
SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Car Game")
clock = pygame.time.Clock()

# === Tải hình ảnh ===
# Load the car image ONCE here
try:
    car_img_original = pygame.image.load("./PNG/App/car7.png").convert_alpha()
    CAR_WIDTH, CAR_HEIGHT = car_img_original.get_size() # Get actual dimensions
    print(f"Loaded car image: Width={CAR_WIDTH}, Height={CAR_HEIGHT}")
except pygame.error as e:
    print(f"Error loading car image: {e}")
    # Provide default dimensions or exit
    CAR_WIDTH, CAR_HEIGHT = 43, 74 # Default guess if loading fails
    car_img_original = pygame.Surface((CAR_WIDTH, CAR_HEIGHT), pygame.SRCALPHA)
    car_img_original.fill((255, 165, 0)) # Orange placeholder

play_img = pygame.image.load("PNG/App/PlayButton.png")
emptyBtnImg = pygame.image.load("PNG/App/SmallEmptyButton.png")
pedestrian_images = [
    pygame.image.load("./PNG/Other/Person_BlueBlack1.png").convert_alpha(),
    pygame.image.load("./PNG/Other/Person_RedBlack1.png").convert_alpha(),
    pygame.image.load("./PNG/Other/Person_YellowBrown2.png").convert_alpha(),
    pygame.image.load("./PNG/Other/Person_RedBlond1.png").convert_alpha(),
    pygame.image.load("./PNG/Other/Person_PurpleBrown1.png").convert_alpha(),
    pygame.image.load("./PNG/Other/Person_OrangeBrown1.png").convert_alpha(),
    pygame.image.load("./PNG/Other/Person_GreenBlack2.png").convert_alpha(),
]
# === UI ===
font = pygame.font.SysFont("calibri", 72)
TEXT_COL = (255, 255, 255)
button_width, button_height = play_img.get_size()
button_x = (SCREEN_WIDTH - button_width) // 2
button_y = (SCREEN_HEIGHT - button_height) // 2
playBtn = Button.Button(button_x, button_y, play_img, 0.4)
emptyBtn = Button.Button(button_x, button_y + 100, emptyBtnImg, 0.4)


def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

# === A* Pathfinding ===
# (A* functions remain the same)
def create_grid_from_map(tmx_data, cell_size):
    width = tmx_data.width * tmx_data.tilewidth
    height = tmx_data.height * tmx_data.tileheight
    grid_cols = width // cell_size
    grid_rows = height // cell_size
    grid = [[0 for _ in range(grid_cols)] for _ in range(grid_rows)]

    for obj in tmx_data.objects:
        # Đánh dấu các vùng không thể đi qua, bao gồm cả viền trắng (Border)
        if obj.name in ['Border', 'RandomCar'] or obj.type == 'Border':
            left = int(obj.x) // cell_size
            top = int(obj.y) // cell_size
            right = int((obj.x + obj.width) // cell_size)
            bottom = int((obj.y + obj.height) // cell_size)
            # Iterate one cell beyond the boundary for safety if needed, but +1 seems sufficient
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    if 0 <= row < grid_rows and 0 <= col < grid_cols:
                        grid[row][col] = 1 # Mark as obstacle
    return grid


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    open_set = []
    heapq.heappush(open_set, (0 + heuristic(start, goal), 0, start, []))
    visited = set()
    start_time = pygame.time.get_ticks() # Add timeout
    TIMEOUT = 200 # milliseconds

    while open_set:
        # Timeout check
        if pygame.time.get_ticks() - start_time > TIMEOUT:
            print("A* search timed out")
            return None

        est_cost, cost, current, path = heapq.heappop(open_set)

        if current == goal:
            return path + [current] # Return the full path including goal

        if current in visited:
            continue
        visited.add(current)

        # Explore neighbors (Up, Down, Left, Right)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # Check order if needed
            nx, ny = current[0] + dx, current[1] + dy

            if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 0: # Check bounds and obstacle
                if (nx, ny) not in visited:
                    new_cost = cost + 1
                    priority = new_cost + heuristic((nx, ny), goal)
                    heapq.heappush(open_set, (priority, new_cost, (nx, ny), path + [current])) # Add current to path history

    print(f"A* could not find a path from {start} to {goal}")
    return None # No path found

# === Classes ===
class Car:
    # Pass center x, y and the already loaded original image
    def __init__(self, center_x, center_y, original_image):
        self.center_x = float(center_x)
        self.center_y = float(center_y)

        # Store the original image (used for rotation)
        self.original_surface = original_image
        # This surface will hold the currently rotated image
        self.surface = self.original_surface
        # The rect represents the bounding box of the *rotated* surface, centered correctly
        self.rect = self.surface.get_rect(center=(self.center_x, self.center_y))
        # The mask is based on the *rotated* surface
        self.mask = pygame.mask.from_surface(self.surface)

        self.angle = 0.0  # Angle 0 points UP (consistent with movement logic)
        self.speed = 0.0
        self.max_speed = 2.0 # Pixels per frame
        self.accel = 0.05
        self.decel = 0.03 # Not currently used with fixed speed on spacebar
        self.friction = 0.98 # Not currently used
        self.rotation_speed = 4.0 # Degrees per frame

        self.path = []
        self.target_index = 0 # Start by targeting the first point in the path

    def set_path(self, new_path):
        """Sets a new path for the car."""
        if new_path and len(new_path) > 0:
             self.path = new_path
             # Start targeting the first point (index 0) if path is just start,
             # or index 1 if path includes start cell. A* usually returns path from start+1.
             # Let's assume path from A* does NOT include the start cell itself.
             self.target_index = 0
        else:
             self.path = []
             self.target_index = 0


   # === INSIDE Car CLASS ===

    def move_towards_path(self, pedestrian_sprites, space_pressed):
        if not self.path or self.target_index >= len(self.path):
            self.speed = 0
            # Update rotation/rect/mask even when stopped to maintain correct orientation if needed
            self.surface = pygame.transform.rotate(self.original_surface, self.angle)
            self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
            self.mask = pygame.mask.from_surface(self.surface)
            return # No path or end of path reached

        if not space_pressed:
            self.speed = 0
             # Update rotation/rect/mask even when stopped
            self.surface = pygame.transform.rotate(self.original_surface, self.angle)
            self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
            self.mask = pygame.mask.from_surface(self.surface)
            return # Not moving if space isn't pressed
        else:
            # Set fixed speed when space is pressed (can reintroduce accel later if needed)
            current_max_speed = self.max_speed

        # Get the coordinates of the center of the target grid cell
        target_row, target_col = self.path[self.target_index]
        target_x = target_col * CELL_SIZE + CELL_SIZE // 2
        target_y = target_row * CELL_SIZE + CELL_SIZE // 2

        # --- Rotation Calculation ---
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        distance_to_target = math.hypot(dx, dy)

        angle_diff = 0.0
        # Only calculate target angle if not already at the target
        if distance_to_target > 1.0: # Avoid atan2(0,0) and spinning at destination
            target_angle_rad = math.atan2(-dy, dx) # Math angle (0=right)
            target_angle_deg = math.degrees(target_angle_rad)
            desired_angle = (90 - target_angle_deg) % 360 # Convert to game angle (0=up)

            # Calculate the shortest angle difference (-180 to 180)
            # Positive diff = CW turn needed, Negative diff = CCW turn needed
            angle_diff = (desired_angle - self.angle + 180) % 360 - 180

        # --- Rotation Application ---
        # Define a small tolerance where we consider the car aligned
        alignment_tolerance = 1.0
        if abs(angle_diff) > alignment_tolerance:
            direction = 1 if angle_diff > 0 else -1 # +1 CW, -1 CCW
            # Apply rotation speed, but don't rotate more than needed in one step
            rotation_magnitude = min(self.rotation_speed, abs(angle_diff))
            self.angle = (self.angle + direction * rotation_magnitude) % 360
        # else:
            # Optional: Snap angle if very close? Might prevent tiny drifts.
            # self.angle = desired_angle # Be careful, might cause jitter if desired_angle fluctuates

        # --- Speed Adjustment Based on Turn Severity ---
        # Reduce speed based on how much the car *still needs to turn* (angle_diff)
        # Define a threshold angle beyond which speed starts reducing
        turn_slowdown_threshold = 15.0 # Start slowing if angle diff > 15 degrees
        max_angle_diff_for_speed = 90.0 # Assume speed is minimum (or zero) for 90+ degree turns

        if abs(angle_diff) <= turn_slowdown_threshold:
            # Mostly aligned, use full speed
            actual_speed = current_max_speed
        else:
            # Reduce speed proportionally for sharper turns
            # Calculate factor (0.0 to 1.0) based on how far angle_diff is beyond the threshold
            excess_angle = abs(angle_diff) - turn_slowdown_threshold
            range_angle = max(1.0, max_angle_diff_for_speed - turn_slowdown_threshold) # Avoid division by zero
            reduction_factor = max(0.0, 1.0 - (excess_angle / range_angle))
            actual_speed = current_max_speed * reduction_factor
            # Ensure speed is not negative
            actual_speed = max(0.0, actual_speed)

            # --- Alternative Simpler Slowdown: ---
            # If angle diff > threshold, move at a fixed reduced speed, e.g., half speed
            # actual_speed = current_max_speed * 0.5
            # --- Or Stop Completely (Original method): ---
            # actual_speed = 0.0

        # --- Movement ---
        if actual_speed > 0.01: # Only move if speed is significant
            move_angle_rad = math.radians(90 - self.angle) # Convert game angle (0=Up) to math radian
            move_x = math.cos(move_angle_rad) * actual_speed
            move_y = -math.sin(move_angle_rad) * actual_speed # Pygame Y is inverted

            next_center_x = self.center_x + move_x
            next_center_y = self.center_y + move_y

            # --- Collision Check (Before Moving) ---
            # Create temporary rect/mask at the *next* position with the *current* angle
            temp_rotated_surface = pygame.transform.rotate(self.original_surface, self.angle)
            temp_rect = temp_rotated_surface.get_rect(center=(next_center_x, next_center_y))
            temp_mask = pygame.mask.from_surface(temp_rotated_surface)

            collision_detected = False
            for ped in pedestrian_sprites:
                # Broad phase check first
                if temp_rect.colliderect(ped.rect):
                    # Narrow phase (mask check)
                    offset_x = ped.rect.x - temp_rect.x
                    offset_y = ped.rect.y - temp_rect.y
                    if temp_mask.overlap(ped.mask, (offset_x, offset_y)):
                        collision_detected = True
                        break
            # Add checks for static obstacles/borders if needed here

            # --- Update Position ---
            if not collision_detected:
                self.center_x = next_center_x
                self.center_y = next_center_y
            else:
                # Stop car if collision is predicted
                self.speed = 0 # Affects speed next frame if space is held
                actual_speed = 0 # Stop movement this frame

        # --- Update Surface, Rect, Mask (Always update based on final angle and position) ---
        self.surface = pygame.transform.rotate(self.original_surface, -self.angle)
        self.rect = self.surface.get_rect(center=(int(self.center_x), int(self.center_y)))
        self.mask = pygame.mask.from_surface(self.surface)

        # --- Check Target Arrival ---
        # Re-calculate distance to the current target point using the *updated* position
        final_dx = target_x - self.center_x
        final_dy = target_y - self.center_y
        final_distance_to_target = math.hypot(final_dx, final_dy)

        # Use a threshold based on movement speed to avoid overshooting
        arrival_threshold = max(actual_speed * 1.5, CELL_SIZE / 4.0) # Adjust multiplier as needed
        # Prevent index error if path is short or already finished
        if self.target_index < len(self.path):
            if final_distance_to_target < arrival_threshold:
                self.target_index += 1

    def draw(self, target_surface):
        # Blit the already rotated surface (self.surface) at its calculated rect position
        target_surface.blit(self.surface, self.rect.topleft)
        # --- Debug Drawing (Optional) ---
        # Draw center point
        # pygame.draw.circle(target_surface, (0, 255, 0), self.rect.center, 3)
        # Draw bounding box
        # pygame.draw.rect(target_surface, (255, 0, 0), self.rect, 1)
        # Draw path target
        # if self.path and self.target_index < len(self.path):
        #     target_row, target_col = self.path[self.target_index]
        #     target_x = target_col * CELL_SIZE + CELL_SIZE // 2
        #     target_y = target_row * CELL_SIZE + CELL_SIZE // 2
        #     pygame.draw.circle(target_surface, (0, 0, 255), (target_x, target_y), 5)


class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Pedestrian(pygame.sprite.Sprite):
    def __init__(self, x, y, surface, path_points, speed=1):
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect(center=(x, y)) # Use center for consistency
        self.x = float(x) # Store precise position
        self.y = float(y)
        self.speed = speed
        self.path_points = path_points
        self.target_point_index = 0 # Start targeting the first point
        self.mask = pygame.mask.from_surface(self.image)
        if not self.path_points: # Handle empty path
             self.kill()


    def update(self):
        if self.target_point_index >= len(self.path_points):
             self.kill() # Remove if path is finished
             return

        target_x, target_y = self.path_points[self.target_point_index]
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.hypot(dx, dy)

        if distance < self.speed * 1.5: # If close to the target point
            self.target_point_index += 1 # Move to the next point
            if self.target_point_index >= len(self.path_points):
                 self.kill() # End of path
                 return
             # Update target for the same frame to avoid stopping
            target_x, target_y = self.path_points[self.target_point_index]
            dx = target_x - self.x
            dy = target_y - self.y
            distance = math.hypot(dx, dy) # Recalculate distance


        if distance > 0: # Avoid division by zero
            # Normalize direction vector
            dir_x = dx / distance
            dir_y = dy / distance
            # Move
            self.x += dir_x * self.speed
            self.y += dir_y * self.speed
            # Update rect position (center)
            self.rect.center = (int(self.x), int(self.y))


def check_pedestrian_on_path(path_cells, pedestrian_group, cell_size):
    """Checks if any pedestrian is currently in any cell of the given path."""
    if not path_cells:
        return False
    pedestrian_occupied_cells = set()
    for ped in pedestrian_group:
        ped_col = ped.rect.centerx // cell_size
        ped_row = ped.rect.centery // cell_size
        pedestrian_occupied_cells.add((ped_row, ped_col))

    for cell in path_cells:
        if cell in pedestrian_occupied_cells:
            return True # Collision detected
    return False


MAX_PEDESTRIANS = 5  # Giới hạn số lượng người đi bộ

def spawn_random_pedestrian(paths, pedestrian_group):
    if len(pedestrian_group) >= MAX_PEDESTRIANS:
        return
    if not paths:
        return

    chosen_path_points = random.choice(paths)
    if not chosen_path_points: return # Skip if path is empty

    # Decide direction (start to end, or end to start)
    if random.choice([True, False]):
        start_point = chosen_path_points[0]
        path_to_follow = chosen_path_points
    else:
        start_point = chosen_path_points[-1]
        path_to_follow = chosen_path_points[::-1] # Reverse path

    start_x, start_y = start_point
    image = random.choice(pedestrian_images)

    # Check if spawn point is too close to car? (Optional)

    pedestrian = Pedestrian(start_x, start_y, image, path_to_follow)
    pedestrian_group.add(pedestrian)


# === Map ===
tmx_data = load_pygame("map.tmx")
sprite_group = pygame.sprite.Group()
sprite_col = pygame.sprite.Group() # Obstacle sprites (like parked cars)
pedestrian_sprites = pygame.sprite.Group()
pedestrian_paths = [] # Store paths as lists of (x, y) tuples

for layer in tmx_data.visible_layers:
    if hasattr(layer, 'data'):
        for x, y, surf in layer.tiles():
            pos = (x * CELL_SIZE, y * CELL_SIZE)
            Tile(pos=pos, surf=surf, groups=sprite_group)

border_rects = []
Start_X, Start_Y = 0, 0 # These should be the CENTER coordinates for the car

# Process objects AFTER tiles
for obj in tmx_data.objects:
    if obj.name == 'Border' or obj.type == 'Border': # Assuming type might also be used
        # Store border rects for simple collision checks
        border_rects.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    elif obj.name == 'Start':
         # Crucially, assume TMX 'Start' object point is the desired CENTER of the car
        Start_X, Start_Y = obj.x, obj.y
    elif obj.name == 'RandomCar' and obj.image:
        # Add static obstacle cars to a collision group
        # Ensure correct positioning if obj.y needs adjustment for Tiled's origin
        Tile(pos=(obj.x, obj.y), surf=obj.image, groups=(sprite_group, sprite_col))
    elif obj.name and "PedestrianPaths" in obj.name:
        if hasattr(obj, 'points'):
            # Tiled points are relative to the object's x,y. Convert to absolute screen coords.
            # No offset needed if Tiled map origin is top-left (standard)
            path_points = [(point.x + obj.x - 0, point.y + obj.y - 576) for point in obj.points]
            if path_points: # Add only if path has points
                 pedestrian_paths.append(path_points)

# === Biến game ===
grid = create_grid_from_map(tmx_data, CELL_SIZE)

# Create car instance using the loaded image and start coordinates
# Pass the ORIGINAL image surface
car = Car(Start_X, Start_Y, car_img_original)

current_path_cells = [] # Store the cells (row, col) of the current A* path
user_goal_cell = None
user_goal_rect = None # For drawing the target marker
game_run = "menu"
spawn_timer = pygame.time.get_ticks() # Initialize timer
min_time_pedes_spawn = 6000 # milliseconds
max_time_pedes_spawn = 12000
next_spawn_interval = random.randint(min_time_pedes_spawn, max_time_pedes_spawn)

# === Game loop ===
recalculation_needed = False # Flag to recalculate path if obstacles change
last_path_recalc_time = 0
RECALC_COOLDOWN = 500 # milliseconds between path recalculations

while True:
    current_time = pygame.time.get_ticks()
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_run == "game":
            mx, my = pygame.mouse.get_pos()
            clicked_col, clicked_row = mx // CELL_SIZE, my // CELL_SIZE

            # Check if click is within grid bounds and not on an obstacle in the base grid
            if 0 <= clicked_row < len(grid) and 0 <= clicked_col < len(grid[0]) and grid[clicked_row][clicked_col] == 0:
                # Check if not clicking on a static obstacle 'RandomCar' tile either
                clicked_rect = pygame.Rect(clicked_col * CELL_SIZE, clicked_row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                is_static_obstacle = False
                for obs_tile in sprite_col:
                    if obs_tile.rect.colliderect(clicked_rect):
                        is_static_obstacle = True
                        break

                if not is_static_obstacle:
                    user_goal_cell = (clicked_row, clicked_col)
                    user_goal_rect = pygame.Rect(clicked_col * CELL_SIZE, clicked_row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                    print(f"New goal set: {user_goal_cell}")
                    recalculation_needed = True # Force path recalculation
                else:
                    print("Clicked on a static obstacle.")
            else:
                print("Clicked outside map bounds or on a border obstacle.")


    # --- Game State Logic ---
    if game_run == "menu":
        screen.fill((24, 24, 24))
        if playBtn.draw(screen):
            game_run = "game"
            # Reset car position and path when starting
            car = Car(Start_X, Start_Y, car_img_original) # Recreate to reset state fully
            current_path_cells = []
            user_goal_cell = None
            user_goal_rect = None
            pedestrian_sprites.empty() # Clear pedestrians
            spawn_timer = current_time # Reset spawn timer
            next_spawn_interval = random.randint(min_time_pedes_spawn, max_time_pedes_spawn)

        pygame.display.update()
        clock.tick(60)
        continue # Skip rest of the loop

    elif game_run == "col" or game_run == "finish":
        screen.fill((24, 24, 24))
        state_text = "CRASHED!" if game_run == "col" else "PARKED!"
        button_text = "RETRY" if game_run == "col" else "NEXT MAP" # Or just RETRY/PLAY AGAIN

        # Center text more accurately
        text_surf = font.render(state_text, True, TEXT_COL)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, button_y))
        screen.blit(text_surf, text_rect)

        # Position button text relative to button
        btn_text_surf = font.render(button_text, True, TEXT_COL)
        btn_text_rect = btn_text_surf.get_rect(center=emptyBtn.rect.center)
        screen.blit(btn_text_surf, btn_text_rect)

        keys = pygame.key.get_pressed()
        action_key = pygame.K_r if game_run == "col" else pygame.K_n # R for Retry, N for Next

        if emptyBtn.draw(screen) or keys[action_key]:
            game_run = "game" # Go back to game state
            # Reset car and game state (same as when starting from menu)
            car = Car(Start_X, Start_Y, car_img_original)
            current_path_cells = []
            user_goal_cell = None
            user_goal_rect = None
            pedestrian_sprites.empty()
            spawn_timer = current_time
            next_spawn_interval = random.randint(min_time_pedes_spawn, max_time_pedes_spawn)

        pygame.display.update()
        clock.tick(60)
        continue # Skip rest of the loop


    # --- Main Game Logic (game_run == "game") ---

    # --- Pedestrian Spawning ---
    if current_time - spawn_timer > next_spawn_interval and pedestrian_paths:
        spawn_random_pedestrian(pedestrian_paths, pedestrian_sprites)
        spawn_timer = current_time
        next_spawn_interval = random.randint(min_time_pedes_spawn, max_time_pedes_spawn)

    # --- Pedestrian Updates ---
    pedestrian_sprites.update() # Move pedestrians

    # --- Pathfinding ---
    # Check if recalculation is needed (new goal, or path blocked)
    # Limit frequency of recalculations to avoid performance issues
    if user_goal_cell and (recalculation_needed or check_pedestrian_on_path(current_path_cells, pedestrian_sprites, CELL_SIZE)) \
       and current_time - last_path_recalc_time > RECALC_COOLDOWN:

        print("Recalculating path...")
        # Create a temporary grid reflecting current pedestrian positions
        temp_grid = [row[:] for row in grid] # Copy base grid
        for ped in pedestrian_sprites:
             ped_col = ped.rect.centerx // CELL_SIZE
             ped_row = ped.rect.centery // CELL_SIZE
             if 0 <= ped_row < len(temp_grid) and 0 <= ped_col < len(temp_grid[0]):
                  temp_grid[ped_row][ped_col] = 1 # Mark pedestrian cell as blocked

        # Get car's current grid cell
        car_col = int(car.center_x) // CELL_SIZE
        car_row = int(car.center_y) // CELL_SIZE
        start_cell = (car_row, car_col)

        # Ensure start cell is valid (sometimes car might slightly exit grid)
        if not (0 <= start_cell[0] < len(temp_grid) and 0 <= start_cell[1] < len(temp_grid[0])):
             print("Warning: Car outside grid bounds, cannot calculate path.")
             # Optionally try to find nearest valid cell or stop car
        elif temp_grid[start_cell[0]][start_cell[1]] == 1:
             print("Warning: Car started in an obstacle cell? Stopping.")
             car.speed = 0 # Stop car if stuck
             car.set_path([]) # Clear path
        else:
             # Run A*
             new_path = a_star(temp_grid, start_cell, user_goal_cell)

             if new_path:
                  # A* returns path including the goal, maybe exclude start?
                  # If A* includes start cell: current_path_cells = new_path[1:]
                  # If A* starts from neighbor: current_path_cells = new_path
                  current_path_cells = new_path # Assume path starts from first step TO goal
                  car.set_path(current_path_cells)
                  print(f"Path found: {len(current_path_cells)} steps.")
             else:
                  print("No path found to goal.")
                  car.set_path([]) # Clear path if none found
                  # Optionally clear user_goal_cell too? Or keep trying?

        recalculation_needed = False # Reset flag
        last_path_recalc_time = current_time


    # --- Car Update and Movement ---
    keys = pygame.key.get_pressed()
    space_pressed = keys[pygame.K_SPACE]
    car.move_towards_path(pedestrian_sprites, space_pressed) # Pass only pedestrians for dynamic avoidance

    # --- Collision Checks (After Movement) ---
    collision_occurred = False
    # 1. Borders (Simple Rect Collision)
    for border in border_rects:
        if car.rect.colliderect(border):
            print("Collision with border!")
            collision_occurred = True
            break
    # 2. Static Obstacles (Mask Collision)
    if not collision_occurred:
        collided_obstacles = pygame.sprite.spritecollide(car, sprite_col, False, pygame.sprite.collide_mask)
        if collided_obstacles:
            print(f"Collision with static obstacle(s): {collided_obstacles}")
            collision_occurred = True
    # 3. Pedestrians (Mask Collision - re-check after both moved)
    if not collision_occurred:
         collided_peds = pygame.sprite.spritecollide(car, pedestrian_sprites, False, pygame.sprite.collide_mask)
         if collided_peds:
             print(f"Collision with pedestrian(s): {collided_peds}")
             collision_occurred = True

    if collision_occurred:
        game_run = "col" # Change state, reset happens in the next loop iteration

    # --- Check Goal Arrival ---
    # Check if the car's center is within the goal cell rectangle
    if user_goal_rect and user_goal_rect.collidepoint(car.center_x, car.center_y):
         # More robust check: Is the path list exhausted?
         if not car.path or car.target_index >= len(car.path):
              print("Goal reached!")
              game_run = "finish"


    # --- Drawing ---
    screen.fill((100, 100, 100)) # Background color

    # Draw map tiles
    sprite_group.draw(screen)

    # Draw static obstacles (already in sprite_group, but could draw separately)
    # sprite_col.draw(screen)

    # Draw goal marker
    if user_goal_rect:
        pygame.draw.rect(screen, (0, 255, 0, 150), user_goal_rect, 0) # Semi-transparent green fill
        pygame.draw.rect(screen, (255, 255, 255), user_goal_rect, 2) # White border

    # Draw A* path (optional debug)
    if current_path_cells:
        for i, (r, c) in enumerate(current_path_cells):
            x = c * CELL_SIZE + CELL_SIZE // 2
            y = r * CELL_SIZE + CELL_SIZE // 2
            color = (255, 0, 0) if i >= car.target_index else (255, 150, 150) # Highlight remaining path
            pygame.draw.circle(screen, color, (x, y), 4)


    # Draw pedestrians
    pedestrian_sprites.draw(screen)

    # Draw car
    car.draw(screen)

    # --- Display Update ---
    pygame.display.flip()
    clock.tick(60) # Limit FPS