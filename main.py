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
img = pygame.image.load("car7.png").convert_alpha()
play_img = pygame.image.load("PlayButton.png")
emptyBtnImg = pygame.image.load("SmallEmptyButton.png")
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
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    if 0 <= row < grid_rows and 0 <= col < grid_cols:
                        grid[row][col] = 1
    return grid


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

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

# === Classes ===
class Car:
    def __init__(self, x, y, height, width):
        self.x = x - width / 2
        self.y = y - height / 2
        self.height = height
        self.width = width
        self.rect = pygame.Rect(self.x, self.y, height, width)
        self.surface = pygame.Surface((height, width), pygame.SRCALPHA)
        self.surface.blit(img, (0, 0))
        self.angle = 0
        self.speed = 0
        self.mask = pygame.mask.from_surface(pygame.transform.rotate(self.surface, self.angle))

    def draw(self):
        self.rect.topleft = (int(self.x), int(self.y))
        rotated = pygame.transform.rotate(self.surface, self.angle)
        surface_rect = self.surface.get_rect(topleft=self.rect.topleft)
        new_rect = rotated.get_rect(center=surface_rect.center)
        screen.blit(rotated, new_rect.topleft)

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

class Pedestrian(pygame.sprite.Sprite):
    def __init__(self, x, y, surface, path_points, speed=1):
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.path_points = path_points
        self.target_point_index = 1
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        if self.target_point_index < len(self.path_points):
            target_x, target_y = self.path_points[self.target_point_index]
            dx = target_x - self.rect.centerx
            dy = target_y - self.rect.centery
            distance = math.sqrt(dx**2 + dy**2)
            if distance > self.speed:
                direction = pygame.math.Vector2(dx, dy).normalize()
                self.rect.x += self.speed * direction.x
                self.rect.y += self.speed * direction.y
            else:
                self.target_point_index += 1
        else:
            self.kill()
def check_pedestrian_on_path(path):
    if path is None:
        return False  # Không có đường đi, không cần kiểm tra
    for ped in pedestrian_sprites:
        ped_row = int(ped.rect.centery) // CELL_SIZE
        ped_col = int(ped.rect.centerx) // CELL_SIZE
        for (row, col) in path:
            if (ped_row, ped_col) == (row, col):
                return True
    return False



MAX_PEDESTRIANS = 5  # Giới hạn số lượng người đi bộ

def spawn_random_pedestrian(paths):
    if len(pedestrian_sprites) >= MAX_PEDESTRIANS:
        return
    if not paths:
        return
    path = random.choice(paths)
    direction_forward = random.choice([True, False])
    if direction_forward:
        start_x, start_y = path[0]
        path_points = path
    else:
        start_x, start_y = path[-1]
        path_points = path[::-1]
    image = random.choice(pedestrian_images)
    pedestrian = Pedestrian(start_x, start_y, image, path_points)
    pedestrian_sprites.add(pedestrian)


# === Map ===
tmx_data = load_pygame("map.tmx")
sprite_group = pygame.sprite.Group()
sprite_col = pygame.sprite.Group()
pedestrian_sprites = pygame.sprite.Group()
pedestrian_paths = []

for layer in tmx_data.visible_layers:
    if hasattr(layer, 'data'):
        for x, y, surf in layer.tiles():
            Tile(pos=(x * CELL_SIZE, y * CELL_SIZE), surf=surf, groups=sprite_group)

border_rects = []
Start_X, Start_Y = 0, 0
for obj in tmx_data.objects:
    if obj.name == 'Border':
        border_rects.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    elif obj.name == 'Start':
        Start_X, Start_Y = obj.x, obj.y
    elif obj.name == 'RandomCar' and obj.image:
        Tile(pos=(obj.x, obj.y), surf=obj.image, groups=sprite_col)
    elif obj.name in ["PedestrianPaths1", "PedestrianPaths2"]:
        if hasattr(obj, 'points'):
            offset_x, offset_y = 0, -576 if obj.name.endswith("1") else -576
            path_points = [(point.x + obj.x + offset_x, point.y + obj.y + offset_y) for point in obj.points]
            pedestrian_paths.append(path_points)

# === Biến game ===
grid = create_grid_from_map(tmx_data, CELL_SIZE)

car = Car(Start_X, Start_Y, 43, 74)
path = []
user_goal_cell = None
user_goal_rect = None
game_run = "menu"
spawn_timer = 0
min_time_pedes_spawn = 6000
max_time_pedes_spawn = 12000
next_spawn_interval = random.randint(min_time_pedes_spawn, max_time_pedes_spawn)

# === Game loop ===
prev_car_position = (int(car.y) // CELL_SIZE, int(car.x) // CELL_SIZE)
prev_temp_grid = None

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_run == "game":
            mx, my = pygame.mouse.get_pos()
            col, row = mx // CELL_SIZE, my // CELL_SIZE
            if 0 <= row < len(grid) and 0 <= col < len(grid[0]) and grid[row][col] == 0:
                user_goal_cell = (row, col)
                user_goal_rect = pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                car_row = int(car.y) // CELL_SIZE
                car_col = int(car.x) // CELL_SIZE
                path = a_star(grid, (car_row, car_col), user_goal_cell)
                
    if game_run == "menu":
        screen.fill((24, 24, 24))
        if playBtn.draw(screen):
            game_run = "game"
        pygame.display.update()
        clock.tick(60)
        continue

   # Thêm biến toàn cục

    # Trong game loop
    if game_run == "game":
        # Lấy vị trí hiện tại của xe
        car_row = int(car.y) // CELL_SIZE
        car_col = int(car.x) // CELL_SIZE
        current_position = (car_row, car_col)

        # Tạo lưới tạm thời để kiểm tra trạng thái hiện tại
        temp_grid = [row[:] for row in grid]  # Sao chép lưới gốc
        for ped in pedestrian_sprites:
            ped_row = int(ped.rect.centery) // CELL_SIZE
            ped_col = int(ped.rect.centerx) // CELL_SIZE
            if 0 <= ped_row < len(temp_grid) and 0 <= ped_col < len(temp_grid[0]):
                temp_grid[ped_row][ped_col] = 1

        # Kiểm tra xem đường đi hiện tại có còn hợp lệ không
        path_blocked = path is not None and check_pedestrian_on_path(path)
        path_invalid = path is not None and any(temp_grid[row][col] == 1 for row, col in path)

        # Kiểm tra xem có ô nào trên đường đi được giải phóng không
        path_needs_update = False
        if path and prev_temp_grid:
            for row, col in path:
                if (prev_temp_grid[row][col] == 1 and temp_grid[row][col] == 0 and grid[row][col] == 0):
                    path_needs_update = True
                    break

        # Nếu vị trí thay đổi, đường đi bị chặn, không hợp lệ, hoặc cần cập nhật, tính lại đường đi
        if current_position != prev_car_position or path_blocked or path_invalid or path_needs_update:
            if user_goal_cell and isinstance(user_goal_cell, tuple) and len(user_goal_cell) == 2:
                # Tìm đường đi mới trên lưới tạm thời
                path = a_star(temp_grid, current_position, user_goal_cell)
                if path:  # Nếu tìm thấy đường đi mới
                    prev_car_position = current_position
                else:
                    print("Hiện chưa tìm được đường đi hợp lý")
                    draw_text("Hiện chưa tìm được đường đi hợp lý", font, (255, 0, 0), SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2)
            else:
                print("Lỗi: user_goal_cell không hợp lệ hoặc không tồn tại.")

        # Cập nhật prev_temp_grid cho khung tiếp theo
        prev_temp_grid = [row[:] for row in temp_grid]
        keys = pygame.key.get_pressed()
        ACCEL, DECEL, FRICTION, TURN = 0.1, 0.05, 0.98, 2
        if keys[pygame.K_UP]: car.speed += ACCEL
        if keys[pygame.K_DOWN]: car.speed -= DECEL
        car.speed *= FRICTION
        if keys[pygame.K_LEFT]: car.angle += TURN * (car.speed / 5)
        if keys[pygame.K_RIGHT]: car.angle -= TURN * (car.speed / 5)

        car.x -= car.speed * math.sin(math.radians(car.angle))
        car.y -= car.speed * math.cos(math.radians(-car.angle))

        car.rect.topleft = (int(car.x), int(car.y))
        for border in border_rects:
            if car.rect.colliderect(border):
                car.x, car.y = Start_X, Start_Y
                car.speed, car.angle = 0, 0
                game_run = "col"

        for col_sprite in sprite_col:
            offset_x = col_sprite.rect.x - car.rect.x
            offset_y = col_sprite.rect.y - car.rect.y
            if car.mask.overlap(pygame.mask.from_surface(col_sprite.image), (offset_x, offset_y)):
                car.x, car.y = Start_X, Start_Y
                car.speed, car.angle = 0, 0
                game_run = "col"

        for ped in pedestrian_sprites:
            offset_x = ped.rect.x - car.rect.x
            offset_y = ped.rect.y - car.rect.y
            if car.mask.overlap(ped.mask, (offset_x, offset_y)):
                car.x, car.y = Start_X, Start_Y
                car.speed, car.angle = 0, 0
                game_run = "col"

        if user_goal_rect and car.rect.colliderect(user_goal_rect):
            if user_goal_rect.contains(car.rect):
                game_run = "finish"

        screen.fill((0, 0, 0))
        sprite_group.draw(screen)
        sprite_col.draw(screen)
        car.draw()

        current_time = pygame.time.get_ticks()
        if current_time - spawn_timer > next_spawn_interval and pedestrian_paths:
            spawn_random_pedestrian(pedestrian_paths)
            spawn_timer = current_time
            next_spawn_interval = random.randint(min_time_pedes_spawn, max_time_pedes_spawn)

        pedestrian_sprites.update()
        pedestrian_sprites.draw(screen)

        if user_goal_rect:
            pygame.draw.rect(screen, (255, 0, 0), user_goal_rect, 3)

        if path:
            for i in range(1, len(path)):
                prev_row, prev_col = path[i - 1]
                curr_row, curr_col = path[i]
                x = curr_col * CELL_SIZE + CELL_SIZE // 2
                y = curr_row * CELL_SIZE + CELL_SIZE // 2
                # Vẽ hình tròn màu đỏ tại vị trí đường dẫn
                pygame.draw.circle(screen, (255, 0, 0), (x, y), 8)


        pygame.display.flip()
        clock.tick(60)

    elif game_run == "col":
        screen.fill((24, 24, 24))
        draw_text("CRASHED", font, TEXT_COL, button_x, button_y)
        draw_text("RETRY", font, TEXT_COL, button_x, button_y + 100)
        if emptyBtn.draw(screen) or pygame.key.get_pressed()[pygame.K_r]:
            game_run = "game"
        pygame.display.update()
        clock.tick(60)

    elif game_run == "finish":
        screen.fill((24, 24, 24))
        draw_text("PARKED", font, TEXT_COL, button_x, button_y)
        draw_text("NEXT", font, TEXT_COL, button_x, button_y + 100)
        if emptyBtn.draw(screen) or pygame.key.get_pressed()[pygame.K_n]:
            game_run = "game"
        pygame.display.update()
        clock.tick(60)
        

