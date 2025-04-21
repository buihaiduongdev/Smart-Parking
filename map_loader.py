import pygame
from pytmx.util_pygame import load_pygame
from config import CELL_SIZE

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, surf, groups):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)

def create_grid_from_map(tmx_data, cell_size):
    width = tmx_data.width * tmx_data.tilewidth
    height = tmx_data.height * tmx_data.tileheight
    grid_cols = width // cell_size
    grid_rows = height // cell_size
    grid = [[0 for _ in range(grid_cols)] for _ in range(grid_rows)]

    for obj in tmx_data.objects:
        if obj.name in ["Border", "RandomCar", "DespawnArea", "PedestrianPaths"] or obj.type == "Border":
            left = int(obj.x) // cell_size
            top = int(obj.y) // cell_size
            right = int((obj.x + obj.width) // cell_size)
            bottom = int((obj.y + obj.height) // cell_size)
            for row in range(top, bottom + 1):
                for col in range(left, right + 1):
                    if 0 <= row < grid_rows and 0 <= col < grid_cols:
                        grid[row][col] = 1
                        

    return grid

def load_map_objects(tmx_data, sprite_group, sprite_col):
    border_rects = []
    pedestrian_paths = []
    Start_X, Start_Y = 0, 0

    for layer in tmx_data.visible_layers:
        if hasattr(layer, 'data'):
            for x, y, surf in layer.tiles():
                Tile(pos=(x * CELL_SIZE, y * CELL_SIZE), surf=surf, groups=sprite_group)

    for obj in tmx_data.objects:
        if obj.name == 'Border':
            border_rects.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
        elif obj.name == 'Start':
            Start_X, Start_Y = obj.x, obj.y
        elif obj.name == 'RandomCar' and obj.image:
            Tile(pos=(obj.x, obj.y), surf=obj.image, groups=sprite_col)
        elif obj.name in ["PedestrianPaths1", "PedestrianPaths2"]:
            if hasattr(obj, 'points'):
                offset_x, offset_y = 0, -576 if obj.name.endswith("1") else -565
                path_points = [(point.x + obj.x + offset_x, point.y + obj.y + offset_y) for point in obj.points]
                pedestrian_paths.append(path_points)

    return border_rects, pedestrian_paths, Start_X, Start_Y