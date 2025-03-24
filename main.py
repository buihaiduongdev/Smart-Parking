import pygame, math, sys
import Button
import random
from pytmx.util_pygame import load_pygame
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

# Khởi tạo Pygame
pygame.init()

# Thiết lập màn hình
screen = pygame.display.set_mode((1920, 1080))
screen_width, screen_height = pygame.display.get_surface().get_size()
pygame.display.set_caption("Car Game")

# Tải hình ảnh
img = pygame.image.load("car.png").convert_alpha()
play_img = pygame.image.load("PlayButton.png")
emptyBtnImg = pygame.image.load("SmallEmptyButton.png")
button_width, button_height = play_img.get_size()

# Ma trận bản đồ
matrix = [
    [39, 32, 32, 32, 32, 32, 32, 32, 32, 45],
    [19, 87, 87, 87, 87, 87, 87, 87, 87, 135],
    [87, 87, 87, 87, 87, 87, 87, 87, 87, 135],
    [87, 87, 87, 87, 87, 87, 87, 87, 87, 135],
    [148, 87, 87, 87, 87, 87, 87, 87, 87, 135],
    [135, 87, 87, 87, 87, 87, 87, 87, 87, 135],
    [135, 108, 108, 108, 108, 108, 99, 112, 108, 135],
    [135, 159, 133, 133, 133, 133, 125, 138, 17, 135],
    [52, 32, 32, 32, 32, 32, 32, 32, 32, 58],
]

# Tọa độ cổng
gates = {
    "top_left": ((72.8814, 22.0339), (810.1624, 44.0678)),
    "top_right": ((1061.02, 23.7288), (1857.63, 45.7627)),
    "bottom_left": ((66.1017, 977.966), (815.2547, 1008.4745)),
    "bottom_right": ((1050.85, 977.966), (1888.138, 1001.6948)),
}

# Tải hình ảnh người đi bộ
pedestrian_images = [
    pygame.image.load(".\PNG\Other\Person_BlueBlack1.png").convert_alpha(),
    pygame.image.load(".\PNG\Other\person_BlueBlack2.png").convert_alpha(),
    pygame.image.load(".\PNG\Other\Person_BlueBlond1.png").convert_alpha(),
    pygame.image.load(".\PNG\Other\Person_BlueBlond2.png").convert_alpha(),
    pygame.image.load(".\PNG\Other\Person_BlueBrown1.png").convert_alpha(),
    pygame.image.load(".\PNG\Other\Person_BlueBrown2.png").convert_alpha(),
]

# Thiết lập nút bấm
button_x = (screen_width - button_width) // 2
button_y = (screen_height - button_height) // 2
playBtn = Button.Button(button_x, button_y, play_img, 0.4)
emptyBtn = Button.Button(button_x, button_y + 100, emptyBtnImg, 0.4)

# Font chữ
font = pygame.font.SysFont("calibri", 72)
TEXT_COL = (255, 255, 255)

# Hàm vẽ chữ
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Hàm chọn ô ngẫu nhiên trong ma trận
def RandomCell(matrix, startx, starty):
    candidates = []
    for y in range(len(matrix)):
        for x in range(len(matrix[y])):
            if matrix[y][x] == 87 and (startx != x or starty != y):
                candidates.append((x, y))
    return random.choice(candidates)

# Lớp tìm đường
class Pathfinder:
    def __init__(self, matrix):
        self.matrix = matrix
        self.grid = Grid(matrix=matrix)
        self.startx = 5
        self.starty = 5
    def crate_path(self):
        start = self.grid.node(x=self.startx, y=self.starty)
        endx, endy = RandomCell(self.matrix, self.startx, self.starty)
        end = self.grid.node(endx, endy)
        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        self.path, _ = finder.find_path(start, end, self.grid)
        self.grid.cleanup()
        print(self.path)
    def draw_path(self):
        if hasattr(self, 'path'):
            points = [(point[0] * 64, point[1] * 64) for point in self.path]
            pygame.draw.lines(screen, '#4a4a4a', False, points, 5)
    def update(self):
        self.draw_path()

# Lớp xe
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
        pygame.draw.rect(screen, (255, 0, 0), new_rect, 2)

# Lớp người đi bộ
class Pedestrian(pygame.sprite.Sprite):
    def __init__(self, x, y, surface, path_points, speed=3):
        super().__init__()
        self.image = surface
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = speed
        self.path_points = path_points
        self.target_point_index = 1
        self.mask = pygame.mask.from_surface(self.image)
        # Theo dõi các khu vực DespawnArea mà người đi bộ đã được kiểm tra
        self.checked_despawn_areas = set()

    def update(self):
        # Kiểm tra va chạm với FinalPath (chắc chắn despawn)
        if final_path and self.rect.colliderect(final_path):
            print(f"Pedestrian at {self.rect.topleft} despawned at FinalPath!")
            self.kill()
            return

        # Kiểm tra va chạm với các khu vực DespawnArea (ngẫu nhiên despawn)
        for i, area in enumerate(despawn_areas):
            if self.rect.colliderect(area) and i not in self.checked_despawn_areas:
                # Đánh dấu khu vực này đã được kiểm tra
                self.checked_despawn_areas.add(i)
                # Xác suất 50% để despawn
                if random.random() < 0.5:
                    print(f"Pedestrian at {self.rect.topleft} despawned at DespawnArea {i}!")
                    self.kill()
                    return

        # Di chuyển theo path nếu chưa despawn
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

# Hàm spawn người đi bộ
def spawn_random_pedestrian(path_points):
    if path_points:
        start_x, start_y = path_points[0]
        image = random.choice(pedestrian_images)
        pedestrian = Pedestrian(start_x, start_y, image, path_points)
        pedestrian_sprites.add(pedestrian)
        print(f"Spawning pedestrian at: ({start_x}, {start_y})")

# Lớp dữ liệu bản đồ
class MapData:
    def __init__(self):
        self.tmx_data = load_pygame('map.tmx')
        self.sprite_group = pygame.sprite.Group()
        self.sprite_col = pygame.sprite.Group()

# Khởi tạo các đối tượng
mapData = MapData()
tmx_data = mapData.tmx_data
sprite_group = pygame.sprite.Group()
sprite_col = pygame.sprite.Group()
pedestrian_sprites = pygame.sprite.Group()

# Lớp Tile
class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, border_color=None, border_width=0):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(surf)
        if border_color and border_width:
            border_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, border_color, border_surf.get_rect(), border_width)
            self.image.blit(border_surf, (0, 0))

# Tải dữ liệu bản đồ
for layer in tmx_data.visible_layers:
    if hasattr(layer, 'data'):
        for x, y, surf in layer.tiles():
            Tile(pos=(x * 64, y * 64), surf=surf, groups=sprite_group)

border_rects = []
for obj in tmx_data.objects:
    if obj.name == 'RandomCar' and obj.image:
        Tile(pos=(obj.x, obj.y), surf=obj.image, groups=sprite_col, border_color='red', border_width=2)
    elif obj.name == 'Border':
        border_rects.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    elif obj.name == 'Finish':
        finish_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
    elif obj.name == 'Start':
        Start_X, Start_Y = obj.x, obj.y

# Tải đường đi của người đi bộ (polyline)
pedestrian_paths = []
for obj in tmx_data.objects:
    if obj.name == "PedestrianPaths1":
        if hasattr(obj, 'points'):
            layer = next((layer for layer in tmx_data.layers if layer.name == obj.__class__.__name__), None)
            offset_x = layer.offsetx if layer else 0
            offset_y = layer.offsety if layer else 0
            path_points = [(point.x + obj.x + offset_x - 70, point.y + obj.y + offset_y - 250) for point in obj.points]
            pedestrian_paths.append(path_points)
            print("Pedestrian paths:", path_points)
        else:
            print(f"Object {obj.name} is not a polyline or polygon!")

# Tải các khu vực despawn và FinalPath
despawn_areas = []
final_path = None
for obj in tmx_data.objects:
    if obj.name and obj.name.startswith("DespawnArea"):
        despawn_areas.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    elif obj.name == "FinalPath":
        final_path = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

print("Despawn areas:", despawn_areas)
print("Final path:", final_path)

# Khởi tạo xe và các biến
car1 = Car(Start_X, Start_Y, 43, 74)
pathfinder = Pathfinder(matrix)
clock = pygame.time.Clock()
spawn_timer = 0
spawn_interval = 2000  # 2 giây
game_run = "menu"

# Vòng lặp chính
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if game_run == "game":
        # Xử lý va chạm
        for Colide in sprite_col:
            offset_x = Colide.rect[0] - car1.rect.left
            offset_y = Colide.rect[1] - car1.rect.top
            if car1.mask.overlap(pygame.mask.from_surface(Colide.image), (offset_x, offset_y)):
                print("Collision detected with car!")
                car1.x, car1.y = Start_X, Start_Y
                car1.speed, car1.angle = 0, 0
                game_run = "col"

        for border_rect in border_rects:
            if car1.rect.colliderect(border_rect):
                print("Collision detected with border!")
                car1.x, car1.y = Start_X, Start_Y
                car1.speed, car1.angle = 0, 0
                game_run = "col"

        for pedestrian in pedestrian_sprites:
            offset_x = pedestrian.rect.left - car1.rect.left
            offset_y = pedestrian.rect.top - car1.rect.top
            if car1.mask.overlap(pedestrian.mask, (offset_x, offset_y)):
                print("Collision detected with pedestrian!")
                car1.x, car1.y = Start_X, Start_Y
                car1.speed, car1.angle = 0, 0
                game_run = "col"

        if 'finish_rect' in locals() and car1.rect.colliderect(finish_rect) and finish_rect.contains(car1.rect):
            print("Car has reached the finish zone!")
            game_run = "finish"

        # Điều khiển xe
        pressed = pygame.key.get_pressed()
        ACCELERATION, DECELERATION, FRICTION = 0.1, 0.05, 0.98
        TURN_SPEED = 2
        if pressed[pygame.K_UP]: car1.speed += ACCELERATION
        if pressed[pygame.K_DOWN]: car1.speed -= DECELERATION
        car1.speed *= FRICTION
        if pressed[pygame.K_LEFT]: car1.angle += TURN_SPEED * (car1.speed / 5)
        if pressed[pygame.K_RIGHT]: car1.angle -= TURN_SPEED * (car1.speed / 5)
        car1.x -= car1.speed * math.sin(math.radians(car1.angle))
        car1.y -= car1.speed * math.cos(math.radians(-car1.angle))
        if pressed[pygame.K_b]: pathfinder.crate_path()

        # Vẽ màn hình
        screen.fill((0, 0, 0))
        sprite_group.draw(screen)
        sprite_col.draw(screen)
        car1.draw()

        # Spawn và cập nhật người đi bộ
        current_time = pygame.time.get_ticks()
        if current_time - spawn_timer > spawn_interval and pedestrian_paths:
            path = random.choice(pedestrian_paths)
            spawn_random_pedestrian(path)
            spawn_timer = current_time

        pedestrian_sprites.update()
        pedestrian_sprites.draw(screen)
        pathfinder.update()

        pygame.display.flip()
        clock.tick(60)

    elif game_run == "menu":
        screen.fill((24, 24, 24))
        if playBtn.draw(screen):
            game_run = "game"
        pygame.display.update()
        clock.tick(60)

    elif game_run == "col":
        screen.fill((24, 24, 24))
        draw_text("C R A S H E D", font, TEXT_COL, button_x, button_y)
        draw_text("RETRY", font, TEXT_COL, button_x, button_y + 100)
        if emptyBtn.draw(screen) or pygame.key.get_pressed()[pygame.K_r]:
            game_run = "game"
        pygame.display.update()
        clock.tick(60)

    elif game_run == "finish":
        screen.fill((24, 24, 24))
        draw_text("P A R K E D", font, TEXT_COL, button_x, button_y)
        draw_text("NEXT", font, TEXT_COL, button_x, button_y + 100)
        if emptyBtn.draw(screen) or pygame.key.get_pressed()[pygame.K_n]:
            game_run = "game"
        pygame.display.update()
        clock.tick(60)

pygame.quit()