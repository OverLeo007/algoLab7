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


def generate_start():
    ways = []
    walls = []
    full_tiles = []
    max_weight = c.ROWS * c.COLS
    for x in range(c.ROWS):
        line = []
        for y in range(c.COLS):
            if x == 0 or x == c.ROWS - 1 or y == 0 or y == c.COLS - 1:
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

    # print(*full_tiles, sep='\n')
    # return full_tiles

    def get_verts(edge: Tile):
        ex, ey = edge.x, edge.y
        neighbours = [
            full_tiles[ex][ey - 1],
            full_tiles[ex][ey + 1],
            full_tiles[ex - 1][ey],
            full_tiles[ex + 1][ey]
        ]
        return set(filter(lambda x: x.status != "wall", neighbours))

    edges = []
    for wall in walls:
        verts = get_verts(wall)
        if verts:
            edges.append((verts, wall))
    edges.sort(key=lambda x: x[1].weight)

    vert_sets: List[set] = []

    to_del_edges = []

    idx = 0
    gifer = GifSaver("images", c.WIDTH, c.HEIGHT)

    while True:
        edge = edges[idx]
        # print(vert_sets)
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
            to_del_edges.append(edge)
        unite_sets(vert_sets)
        idx += 1

        for edge_to_del in edges:
            if edge_to_del in to_del_edges:
                edge_to_del[1].upd_texture("unchecked_way")
        to_del_edges.clear()

        gifer.add_img(pg.image.tostring(screen, "RGBA"))
        for line in full_tiles:
            for tile in line:
                tile.draw(screen, camera)
        pg.display.flip()

        clock.tick(60)

        if vert_sets[0] == ways:
            break

    print(len(edges), len(to_del_edges))
    del gifer
    return full_tiles


def main():
    pg.init()
    screen = pg.display.set_mode((c.WIDTH, c.HEIGHT))

    # print(*tiles, sep="\n")
    camera = Camera(c.WIDTH, c.HEIGHT)
    clock = pg.time.Clock()

    tiles = generate_maze(screen, camera, clock)


    controls = {
        pg.K_w: {
            'state': False,
            'args': [0, -c.CELL_SIZE]
        },
        pg.K_s: {
            'state': False,
            'args': [0, c.CELL_SIZE]
        },
        pg.K_a: {
            'state': False,
            'args': [-c.CELL_SIZE, 0]
        },
        pg.K_d: {
            'state': False,
            'args': [c.CELL_SIZE, 0]
        }
    }

    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 4:  # колесико мыши вверх
                    camera.zoom_in()
                elif event.button == 5:  # колесико мыши вниз
                    camera.zoom_out()

            if event.type == pg.MOUSEBUTTONDOWN:
                x, y = camera.apply_inverse(pg.mouse.get_pos())

            if event.type == pg.KEYDOWN:
                if move_dir := controls.get(event.key, False):
                    move_dir['state'] = True
                else:
                    x, y = camera.apply_inverse(pg.mouse.get_pos())
                    if event.key == pg.K_1:
                        tiles[x][y].upd_texture("way")
                    if event.key == pg.K_2:
                        tiles[x][y].upd_texture("checked_way")
                    if event.key == pg.K_3:
                        tiles[x][y].upd_texture("unchecked_way")
                    if event.key == pg.K_4:
                        tiles[x][y].upd_texture("wall")

                    if event.key == pg.K_UP:
                        c.ROWS += 2
                        c.COLS += 2

                    if event.key == pg.K_DOWN:
                        c.ROWS -= 2
                        c.COLS -= 2

                    if event.key == pg.K_r:
                        tiles = generate_maze(screen, camera, clock)

            if event.type == pg.KEYUP:
                if move_dir := controls.get(event.key, False):
                    move_dir['state'] = False

        for val in controls.values():
            if val['state'] is True:
                camera.move(*val['args'])

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
