from random import randint
from typing import List

import pygame as pg
from math import ceil, sin
import consts as c
from parse_tiles import Tiles
from pprint import pprint
from gifer import GifSaver


class Tile:
    tiler = Tiles()
    status = {
        "wall": tiler.get_random_wall,
        "way": tiler.get_random_way,
        "checked_way": tiler.get_random_checked_way,
        "unchecked_way": tiler.get_random_unchecked_way
    }

    def __init__(self, x, y, status="unchecked_way", weight=None):
        self.x = x
        self.y = y
        self.status = status
        self.texture = Tile.status[self.status]()
        self.weight = weight
        self.f_weight = {}
        self.neighbours = []

    def draw(self, surface, cam):
        rect = pg.Rect(self.x * c.CELL_SIZE, self.y * c.CELL_SIZE, c.CELL_SIZE,
                       c.CELL_SIZE)
        rect = cam.apply(rect)
        if self.status == "wall":
            rect.y -= int((42 - 26) * (rect.h / 26))
            transformed = pg.transform.scale(self.texture,
                                             (rect.w, int(42 * rect.h / 26)))
        else:
            transformed = pg.transform.scale(self.texture, rect[2:])

        surface.blit(transformed, rect)

        if self.f_weight != {} and self.status != "wall":
            weights = " ".join(map(str, self.f_weight.values()))
            text = pg.font.SysFont("Comic Sans", 12) \
                .render(weights, True, c.YELLOW)

            text_rect = text.get_rect(center=(rect.centerx, rect.y))
            surface.blit(text, text_rect)

        # pg.draw.rect(surface, self.col, rect)
        # pg.draw.rect(surface, c.BLACK, rect, 1)

    def upd_texture(self, new_status):
        self.status = new_status
        self.texture = Tile.status[self.status]()

    def __hash__(self):
        return hash((self.x, self.y))

    def __eq__(self, other):
        if self.x == other.x and self.y == other.y:
            return True
        return False

    def __repr__(self):
        if self.status == "wall" and self.weight is None:
            status = "border_wall"
        elif self.status == "wall" and self.weight is not None:
            status = "maze_wall"
        else:
            status = self.status

        return f"Tile(({self.x}, {self.y}), {status}" \
               f"{f', {self.weight}' if self.weight is not None else ''})"


class Camera:
    def __init__(self, width, height):
        self.x = 0
        self.y = 0
        self.width = width
        self.height = height
        self.zoom = 1.0

    def move(self, dx, dy):
        self.x += dx
        self.y += dy

    def zoom_in(self):
        self.zoom *= 1.1

    def zoom_out(self):
        self.zoom /= 1.1

    def apply(self, rect):
        return pg.Rect(
            ceil(rect.x * self.zoom - self.x),
            ceil(rect.y * self.zoom - self.y),
            ceil(rect.width * self.zoom),
            ceil(rect.height * self.zoom)
        )

    def apply_inverse(self, pos):
        x_sc, y_sc = (pos[0] + self.x) / self.zoom, (pos[1] + self.y) / self.zoom
        return int(x_sc / c.CELL_SIZE), int(y_sc / c.CELL_SIZE)


class DisjointSet:
    def __init__(self, n):
        self.parent = [i for i in range(n)]
        self.rank = [0] * n

    def find(self, i):
        if self.parent[i] != i:
            self.parent[i] = self.find(self.parent[i])
        return self.parent[i]

    def union(self, i, j):
        x, y = self.find(i), self.find(j)
        if x == y:
            return
        if self.rank[x] > self.rank[y]:
            self.parent[y] = x
        else:
            self.parent[x] = y
            if self.rank[x] == self.rank[y]:
                self.rank[y] += 1


def move_event_handler(event, camera):
    if event.type == pg.MOUSEBUTTONDOWN:
        if event.button == 4:  # колесико мыши вверх
            camera.zoom_in()
        elif event.button == 5:  # колесико мыши вниз
            camera.zoom_out()

    if event.type == pg.KEYDOWN:
        if move_dir := c.CONTROLS.get(event.key, False):
            move_dir['state'] = True

    if event.type == pg.KEYUP:
        if move_dir := c.CONTROLS.get(event.key, False):
            move_dir['state'] = False

    for val in c.CONTROLS.values():
        if val['state'] is True:
            camera.move(*val['args'])


def render_tiles(tiles, screen, camera, clock):
    screen.fill(c.BLACK)
    for line in tiles:
        for tile in line:
            tile.draw(screen, camera)
    pg.display.flip()
    clock.tick(120)


def generate_start():
    ways = []
    walls = []
    full_tiles = []
    max_weight = c.ROWS * c.COLS
    for y in range(c.ROWS):
        line = []
        for x in range(c.COLS):
            if x == 0 or x == c.COLS - 1 or y == 0 or y == c.ROWS - 1:
                new_tile = Tile(x, y, status="wall")
            elif x % 2 == 0 or y % 2 == 0:
                new_tile = Tile(x, y, status="wall", weight=randint(0, max_weight))
                walls.append(new_tile)
            else:
                new_tile = Tile(x, y)
                ways.append(new_tile)
            line.append(new_tile)
        full_tiles.append(line)

    return full_tiles, walls, set(ways)


def unite_sets(s_list):
    done = False
    while not done:
        done = True
        for i in range(len(s_list)):
            for j in range(i + 1, len(s_list)):
                if s_list[i].intersection(s_list[j]):
                    s_list[i].update(s_list[j])
                    s_list.pop(j)
                    done = False
                    break
            if not done:
                break
    return s_list


def generate_maze(screen, camera, clock):
    full_tiles, walls, ways = generate_start()

    def get_verts(edge: Tile):
        ex, ey = edge.x, edge.y
        neighbours = [
            full_tiles[ey][ex - 1],
            full_tiles[ey][ex + 1],
            full_tiles[ey - 1][ex],
            full_tiles[ey + 1][ex]
        ]
        # return set(filter(lambda x: x.status != "wall", neighbours))
        return set([tile for tile in neighbours if tile.status != "wall"])

    edges = []
    for wall in walls:
        verts = get_verts(wall)
        if verts:
            edges.append((verts, wall))
    edges.sort(key=lambda x: x[1].weight)

    vert_sets: List[set] = []

    idx = 0
    if c.SAVE_GIF:
        gifer = GifSaver("images", c.WIDTH, c.HEIGHT)
    else:
        gifer = None

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                del gifer
                exit()

            move_event_handler(event, camera)

        edge = edges[idx]
        cycle = False
        for v_set in vert_sets:
            if edge[0].intersection(v_set):
                if edge[0].issubset(v_set):
                    cycle = True
                else:
                    v_set.update(edge[0])
                break
        else:
            vert_sets.append(edge[0])
        if not cycle:
            edge[1].upd_texture("unchecked_way")
            edge[1].weight = None
        unite_sets(vert_sets)

        if gifer:
            gifer.add_img(pg.image.tostring(screen, "RGBA"))
        if c.REALTIME_GEN:
            render_tiles(full_tiles, screen, camera, clock)

        idx += 1
        if vert_sets[0] == ways:
            break

    if gifer:
        del gifer
    return full_tiles


def find_way(tiles, routes, screen, camera, clock):
    def find_way_neighbours(tile):
        neighbours = [
            tiles[tile.y][tile.x - 1],
            tiles[tile.y][tile.x + 1],
            tiles[tile.y - 1][tile.x],
            tiles[tile.y + 1][tile.x]
        ]
        return [tile for tile in neighbours if tile.status != "wall"]

    # def find_way_inner(from_tile: Tile, to_tile: Tile):
    #     cur_weight = 1
    #     weighted = []
    #
    #     if to_tile in weighted:
    #         return
    #
    #     stack = [from_tile]
    #     found = False
    #     while stack:
    #         print(cur_weight)
    #         if found:
    #             print("fin by find")
    #             break
    #         curr_tile = stack.pop()
    #
    #         for tile in curr_tile.neighbours:
    #             if tile.weight is not None:
    #                 continue
    #
    #             tile.weight = cur_weight
    #             weighted.append(tile)
    #
    #             if tile == to_tile:
    #                 found = True
    #                 break
    #
    #             if tile not in [from_tile, to_tile]:
    #                 tile.upd_texture("checked_way")
    #
    #             stack.append(tile)
    #             render_tiles(tiles, screen, camera, clock)
    #             for event in pg.event.get():
    #                 if event.type == pg.QUIT:
    #                     exit()
    #         cur_weight += 1

    def find_way_inner(from_tile: Tile, to_tile: Tile):
        from_tile.f_weight[to_tile] = 1
        weighted = {1: [from_tile]}

        while isinstance(to_tile.f_weight.get(to_tile, False), bool):
            cur_weight = max(weighted.keys())
            cur_wave = weighted[cur_weight]

            weighted[cur_weight + 1] = []
            appends = 0
            for tile in cur_wave:
                for n_tile in tile.neighbours:

                    if n_tile.f_weight.get(to_tile, False):
                        continue

                    n_tile.f_weight[to_tile] = cur_weight + 1

                    if n_tile.status != "way":
                        n_tile.upd_texture("checked_way")

                    weighted[cur_weight + 1].append(n_tile)
                    appends += 1
            if appends == 0:
                print("NO WAY")
                break
            render_tiles(tiles, screen, camera, clock)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    exit()

    for y in range(1, c.ROWS - 1):
        for x in range(1, c.COLS - 1):
            tile = tiles[y][x]
            tile.f_weight = {}
            if tile.status != "wall":
                tile.neighbours = find_way_neighbours(tile)
                if tile.status != "way":
                    tile.upd_texture("unchecked_way")

    pairs = [(routes[i], routes[i + 1]) for i in range(len(routes) - 1)]

    for pair in pairs:
        find_way_inner(*pair)
    print("fin")


def main():
    pg.init()
    screen = pg.display.set_mode((c.WIDTH, c.HEIGHT), display=1)

    # print(*tiles, sep="\n")
    camera = Camera(c.WIDTH, c.HEIGHT)
    clock = pg.time.Clock()

    # tiles = generate_start()[0]
    tiles = generate_maze(screen, camera, clock)

    route = []

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                exit()

            move_event_handler(event, camera)

            left_mb, mid_mb, right_mb = pg.mouse.get_pressed()

            if event.type == pg.MOUSEBUTTONDOWN and event.button not in (4, 5):

                x, y = camera.apply_inverse(pg.mouse.get_pos())
                if x <= c.COLS and y <= c.ROWS:
                    tile = tiles[y][x]
                    if tile.status != "wall":
                        if left_mb:
                            tile.upd_texture("way")
                            route.append(tile)
                        if right_mb:
                            tile.upd_texture("unchecked_way")
                            tile.f_weight = {}
                            if tile in route:
                                route.remove(tile)
                # print(route)

            if event.type == pg.KEYDOWN:
                if event.key in [pg.K_RETURN, pg.K_KP_ENTER]:
                    if len(route) > 1:
                        find_way(tiles, route, screen, camera, clock)

                if event.key == pg.K_1:
                    x, y = camera.apply_inverse(pg.mouse.get_pos())
                    tile = tiles[y][x]
                    if tile.status == "wall":
                        tile.upd_texture("unchecked_way")
                    else:
                        tile.upd_texture("wall")

                if event.key == pg.K_r:
                    tiles = generate_maze(screen, camera, clock)
                    route.clear()

        screen.fill((0, 0, 0))

        # screen.blit(texture, texture_rect)

        for line in tiles:
            for tile in line:
                tile.draw(screen, camera)

        pg.display.flip()

        clock.tick(60)

    pg.quit()


if __name__ == '__main__':
    main()
