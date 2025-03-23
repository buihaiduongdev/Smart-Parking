import pytmx
import pygame
import os
import heapq

def load_map_data(map_file):
    tmx_data = pytmx.load_pygame(map_file)
    width = tmx_data.width
    height = tmx_data.height
    grid = [[0] * width for _ in range(height)]

    for obj in tmx_data.objects:
        if obj.name == 'Border' or obj.name == 'RandomCar':
            x = obj.x
            y = obj.y
            w = obj.width
            h = obj.height
            for i in range(width):
                for j in range(height):
                    tile_x = i * tmx_data.tilewidth
                    tile_y = j * tmx_data.tileheight
                    if x < tile_x + tmx_data.tilewidth and x + w > tile_x and \
                       y < tile_y + tmx_data.tileheight and y + h > tile_y:
                        grid[j][i] = 1

    start = None
    finish = None
    for obj in tmx_data.objects:
        if obj.name == 'Start':
            start = (int(obj.x / tmx_data.tilewidth), int(obj.y / tmx_data.tileheight))
        elif obj.name == 'Finish':
            finish = (int(obj.x / tmx_data.tilewidth), int(obj.y / tmx_data.tileheight))

    return grid, start, finish

def a_star(grid, start, goal):
    """Tìm đường đi ngắn nhất từ start đến goal sử dụng thuật toán A*."""

    height = len(grid)
    width = len(grid[0])

    def heuristic(a, b):
        """Ước lượng khoảng cách từ a đến b."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def get_neighbors(node):
        """Lấy các ô lân cận của node."""
        neighbors = []
        for i, j in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            x, y = node[0] + i, node[1] + j
            if 0 <= x < width and 0 <= y < height and grid[y][x] == 0:
                neighbors.append((x, y))
        return neighbors

    open_set = [(0, start)]
    came_from = {}
    cost_so_far = {start: 0}

    while open_set:
        current_cost, current = heapq.heappop(open_set)

        if current == goal:
            break

        for next in get_neighbors(current):
            new_cost = cost_so_far[current] + 1
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(next, goal)
                heapq.heappush(open_set, (priority, next))
                came_from[next] = current

    if goal not in came_from:
        return None

    path = []
    current = goal
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()

    return path

pygame.init()
pygame.display.set_mode((1, 1))

map_grid, start_pos, finish_pos = load_map_data('./map.tmx')

path = a_star(map_grid, start_pos, finish_pos)

if path:
    print("Đường đi tìm được:")
    for x, y in path:
        print(f"({x}, {y})", end=" -> ")
    print("Finish")
else:
    print("Không tìm thấy đường đi.")

if path:
    for y, row in enumerate(map_grid):
        line = ''
        for x, cell in enumerate(row):
            if (x, y) in path:
                line += '* '
            elif cell == 0:
                line += '. '
            else:
                line += '# '
        print(line)

pygame.quit()