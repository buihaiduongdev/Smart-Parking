import pygame, math, sys
import Button


pygame.init()
from pytmx.util_pygame import load_pygame
import random

from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.diagonal_movement import DiagonalMovement

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Tự động lấy độ phân giải màn hình
screen_width, screen_height = pygame.display.get_surface().get_size()

img = pygame.image.load("car.png").convert_alpha()
play_img = pygame.image.load("PlayButton.png")
emptyBtnImg = pygame.image.load("SmallEmptyButton.png")
button_width, button_height = play_img.get_size()

pygame.display.set_caption("car game")

img = pygame.image.load("car.png").convert_alpha()

matrix = [[39,32,32,32,32,32,32,32,32,45],
[19,87,87,87,87,87,87,87,87,135],
[87,87,87,87,87,87,87,87,87,135],
[87,87,87,87,87,87,87,87,87,135],
[148,87,87,87,87,87,87,87,87,135],
[135,87,87,87,87,87,87,87,87,135],
[135,108,108,108,108,108,99,112,108,135],
[135,159,133,133,133,133,125,138,17,135],
[52,32,32,32,32,32,32,32,32,58],
]

button_x = (screen_width - button_width) // 2
button_y = (screen_height - button_height) // 2
playBtn = Button.Button(button_x, button_y, play_img, 0.4)
emptyBtn = Button.Button(button_x, button_y + 100, emptyBtnImg, 0.4)

font = pygame.font.SysFont("calibri", 72)
TEXT_COL = (255,255,255)
def changedata():
    arab = 2
    return arab
print(";;;;;;;;;;;;;;;;;;;")
arab = 1
print(arab)
print(";;;;;;;;;;;;;;;;;;;")
arab = changedata()
print(arab)
print(";;;;;;;;;;;;;;;;;;;")

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

def RandomCell(matrix, startx, starty):
    candidates = []
    for y in range(len(matrix)):
        for x in range(len(matrix[y])):
            if matrix[y][x] == 87:
                if startx != x and starty != y:
                    candidates.append((x, y))
    x, y = random.choice(candidates)
    return x, y

class Pathfinder:
    def __init__(self, matrix):
        self.matrix = matrix
        self.grid = Grid(matrix=matrix)
        self.startx = 5
        self.starty = 5
    def crate_path(self):
        start = self.grid.node(x=self.startx, y=self.starty)

        endx, endy = RandomCell(self.matrix, self.startx, self.startx)
        end = self.grid.node(endx, endy)

        finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
        self.path,_ = finder.find_path(start, end, self.grid)
        self.grid.cleanup()
        print(self.path)
    def draw_path(self):
         if self.path:
            points = []
            for point in self.path:
                x = point[0] * 64
                y = point[1] * 64
                points.append((x, y))
            pygame.draw.lines(screen, '#4a4a4a', False, points, 5)

    def update(self):
        if hasattr(self, 'path'):
            self.draw_path()
class Car:
    def __init__(self, x, y, height, width):
        self.x = x - width / 2
        self.y = y - height / 2
        self.height = height
        self.width = width
        self.rect = pygame.Rect(x, y, height, width)
        self.surface = pygame.Surface((height, width), pygame.SRCALPHA)
        self.surface.blit(img, (0, 0))
        self.angle = 0
        self.speed = 0 # 2
        self.mask = pygame.mask.from_surface(pygame.transform.rotate(self.surface, self.angle))
        self.sensor_angles = [0, 30, -30]
        self.sensor_distances = [0] * len(self.sensor_angles)

    def draw(self): # 3
        self.rect.topleft = (int(self.x), int(self.y))
        rotated = pygame.transform.rotate(self.surface, self.angle)
        surface_rect = self.surface.get_rect(topleft = self.rect.topleft)
        new_rect = rotated.get_rect(center = surface_rect.center)
        screen.blit(rotated, new_rect.topleft)
        border_color = (255, 0, 0)  # Red color
        border_width = 2
        pygame.draw.rect(screen, border_color, new_rect, border_width)

class Person:
    def __init__(self, x, y, image):
        self.x = x
        self.y = y
        self.image = image

person_img = pygame.image.load('person.png').convert_alpha()
person = Person(0, 0, person_img)

class MapData:
    def __init__(self):
        self.tmx_data = load_pygame('map.tmx')
        self.sprite_group = pygame.sprite.Group()
        self.sprite_col = pygame.sprite.Group()

mapData = MapData()

clock = pygame.time.Clock()

tmx_data = mapData.tmx_data
sprite_group = pygame.sprite.Group()
sprite_col = pygame.sprite.Group()

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups, border_color=None, border_width=0,):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)
        self.mask = pygame.mask.from_surface(surf)

        if border_color is not None and border_width > 0:
            border_surf = pygame.Surface(self.image.get_size(), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, border_color, border_surf.get_rect(), border_width)
            self.image.blit(border_surf, (0, 0))



for layer in tmx_data.visible_layers:
    if hasattr(layer, 'data'):
        for x, y, surf in layer.tiles():
            pos = (x * 64, y * 64)
            Tile(pos=pos, surf=surf, groups=sprite_group)


border_rects = []
for obj in mapData.tmx_data.objects:
    pos = obj.x, obj.y
    if obj.name == 'RandomCar':
        print ("random car object exists")
        if obj.image is not None:
            Tile(pos=pos, surf=obj.image, groups=sprite_col, border_color='red', border_width=2)
    if obj.name == 'Border':
        print("border object exists")
        rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
        border_rects.append(rect)
    if obj.name == "Finish":
        print("Finish object exists")
        finish_rect = pygame.Rect(obj.x, obj.y, obj.width, obj.height)
for obj in tmx_data.objects:
    print(obj.name)

#get start position
for obj in tmx_data.objects:
    pos = obj.x, obj.y
    if obj.name == 'Start':
        Start_Y = obj.y
        Start_X = obj.x

car1 = Car(Start_X, Start_Y, 43, 74) # 4
pathfinder = Pathfinder(matrix)
game_run = "menu"
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if game_run == "game":
        for Colide in sprite_col:
            offset_x = Colide.rect[0] - car1.rect.left
            offset_y = Colide.rect[1] - car1.rect.top
            if  car1.mask.overlap(pygame.mask.from_surface(Colide.image), (offset_x, offset_y)):
                print("Collision detected with car!")
                car1.x = Start_X
                car1.y = Start_Y
                car1.speed = 0
                car1.angle = 0
                game_run = "col"

            # check for collisions with borders
        for border_rect in border_rects:
            if car1.rect.colliderect(border_rect):
                print("Collision detected with border!")
                car1.x = Start_X
                car1.y = Start_Y
                car1.speed = 0
                car1.angle = 0
                game_run = "col"
            #check if car is inside finish zone
        if finish_rect and car1.rect.colliderect(finish_rect) and finish_rect.contains(car1.rect):
            print("Car has reached the finish zone!")
            game_run = "finish"

        pressed = pygame.key.get_pressed()
        ACCELERATION = 0.1  # Tăng tốc từ từ
        DECELERATION = 0.05  # Giảm tốc từ từ
        FRICTION = 0.98      # Ma sát
        if pressed[pygame.K_UP]: 
            car1.speed += ACCELERATION  
        if pressed[pygame.K_DOWN]: 
            car1.speed -= DECELERATION  
        car1.speed *= FRICTION  # Giúp xe không dừng đột ngột
        TURN_SPEED = 2  # Góc quay mượt hơn

        if pressed[pygame.K_LEFT]: 
            car1.angle += TURN_SPEED * (car1.speed / 5)  # Giảm góc quay khi xe chậm
        if pressed[pygame.K_RIGHT]: 
            car1.angle -= TURN_SPEED * (car1.speed / 5)
        car1.x -= car1.speed * math.sin(math.radians(car1.angle)) # 8
        car1.y -= car1.speed * math.cos(math.radians(-car1.angle)) # 8


        screen.fill((0, 0, 0)) # 9
        sprite_group.draw(screen)
        sprite_col.draw(screen)

        screen.blit(person.image, (person.x, person.y))


        car1.draw()
        if pressed[pygame.K_b]:
            pathfinder.crate_path()
            pathfinder.draw_path()
        pathfinder.update()
        pygame.display.flip()
        clock.tick(60) # 10
    elif game_run == "menu":
        screen.fill((24,24,24))
        if playBtn.draw(screen):
            game_run = "game"
        pygame.display.update()
        clock.tick(60)
    elif game_run == "col":
        draw_text("C R A S H E D", font, TEXT_COL, button_x, button_y)
        draw_text("RETRY", font, TEXT_COL, button_x, button_y + 100)
        if emptyBtn.draw(screen):
            game_run = "game"
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_r]: game_run = "game"

        pygame.display.update()
    elif game_run == "finish":
        draw_text("P A R K E D", font, TEXT_COL, button_x, button_y)
        draw_text("NEXT", font, TEXT_COL, button_x, button_y + 100)
        if emptyBtn.draw(screen):
            game_run = "game"
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_n]: game_run = "game"

        pygame.display.update()

pygame.quit()