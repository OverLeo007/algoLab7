import os
from random import randint, choice
from typing import List

import cv2
import numpy as np
import pygame as pg
import pygame_menu as pgm
from math import ceil, sin
import consts as c
from parse_tiles import Tiles
from pprint import pprint
from gifer import GifSaver
import cProfile
from PIL import Image, ImageStat


class Camera:
    def __init__(self, screen, width, height):
        self.screen = screen
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
        sub_pos = self.screen.get_abs_offset()
        rel_pos = pos[0] - sub_pos[0], pos[1] - sub_pos[1]
        x_sc, y_sc = (rel_pos[0] + self.x) / self.zoom, (
                rel_pos[1] + self.y) / self.zoom
        return int(x_sc / c.CELL_SIZE), int(y_sc / c.CELL_SIZE)


class TileField(List[List["TileField.Tile"]]):
    class Tile:
        tiler = Tiles()
        textures_status = {
            "wall": tiler.get_random_wall,
            "way": tiler.get_random_way,
            "checked_way": tiler.get_random_checked_way,
            "unchecked_way": tiler.get_random_unchecked_way
        }

        def __init__(self, x, y, status="unchecked_way", weight=None):
            self.x = x
            self.y = y
            self.status = status
            self.texture = TileField.Tile.textures_status[self.status]()
            self.weight = weight
            self.f_weight = {}
            self.neighbours = []

        def render(self, surface, cam):
            rect = pg.Rect(self.x * c.CELL_SIZE, self.y * c.CELL_SIZE, c.CELL_SIZE,
                           c.CELL_SIZE)
            rect = cam.apply(rect)
            if pg.Rect(0, 0, c.MAZE_W, c.MAZE_H).colliderect(rect):
                if self.status == "wall":
                    w_w, w_h = TileField.Tile.tiler.wall_tile_size
                    rect.y -= int((w_h - w_w) * (rect.h / w_w))
                    transformed = pg.transform.scale(self.texture,
                                                     (rect.w,
                                                      int(w_h * rect.h / w_w)))
                else:
                    transformed = pg.transform.scale(self.texture, rect[2:])

                surface.blit(transformed, rect)

        def upd_texture(self, new_status):
            self.status = new_status
            self.texture = TileField.Tile.textures_status[self.status]()

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

    def __init__(self, screen, camera, clock, gifer=None):
        super().__init__()
        self.walls = []
        self.ways = []
        self.screen = screen
        self.camera = camera
        self.clock = clock
        self.gifer = gifer
        self.pred_gen()

    def __getitem__(self, item):
        if isinstance(item, tuple):
            x, y = item
            return super().__getitem__(y).__getitem__(x)
        else:
            return super().__getitem__(item)

    def __setitem__(self, key, value):
        if isinstance(key, tuple):
            x, y = key
            super().__getitem__(y).__setitem__(x, value)
        else:
            super().__setitem__(key, value)

    def render(self):
        self.screen.fill(c.BLACK)
        for line in self:
            for tile in line:
                tile.render(self.screen, self.camera)
        pg.display.flip()
        self.clock.tick(30)

    def pred_gen(self):
        max_weight = c.ROWS * c.COLS
        for y in range(c.ROWS):
            line = []
            for x in range(c.COLS):
                if x == 0 or x == c.COLS - 1 or y == 0 or y == c.ROWS - 1:
                    new_tile = TileField.Tile(x, y, status="wall")
                elif x % 2 == 0 or y % 2 == 0:
                    new_tile = TileField.Tile(x, y, status="wall",
                                              weight=randint(0, max_weight))
                    self.walls.append(new_tile)
                else:
                    new_tile = TileField.Tile(x, y)
                    self.ways.append(new_tile)
                line.append(new_tile)
            self.append(line)

    def get_not_wall_neighbours(self, tile: "TileField.Tile"):
        neighbours = [
            self[tile.x - 1, tile.y],
            self[tile.x + 1, tile.y],
            self[tile.x, tile.y - 1],
            self[tile.x, tile.y + 1]

        ]
        return [tile for tile in neighbours if tile.status != "wall"]

    def generate_maze(self):
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

        ways = set(self.ways)
        edges = []
        for wall in self.walls:
            verts = set(self.get_not_wall_neighbours(wall))
            if verts:
                edges.append((verts, wall))
        edges.sort(key=lambda x: x[1].weight)

        vert_sets: List[set] = []
        idx = 0
        while True:
            Window.pygame_events_handler(
                {
                    "handler": Window.move_event_handler,
                    "args": [self.camera]
                }
            )

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

            if self.gifer:
                self.gifer.add_img(pg.image.tostring(self.screen, "RGBA"))
            if c.REALTIME_GEN:
                self.render()

            idx += 1
            if vert_sets[0] == ways:
                break

    def find_way(self, routes):
        def mark_tiles(from_tile: TileField.Tile, to_tile: TileField.Tile):
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
                    return False

                Window.pygame_events_handler(
                    {
                        "handler": Window.move_event_handler,
                        "args": [self.camera]
                    }
                )

                self.render()

                if self.gifer:
                    self.gifer.add_img(pg.image.tostring(self.screen, "RGBA"))
            return True

        def find_way_in_marked(from_tile: TileField.Tile, to_tile: TileField.Tile):
            way = [to_tile]
            cur_tile = to_tile
            while cur_tile != from_tile:
                neighbours = self.get_not_wall_neighbours(cur_tile)
                cur_marked = list(
                    filter(lambda x: x.f_weight.get(to_tile, False), neighbours))

                lowest = \
                    min(cur_marked,
                        key=lambda tile: tile.f_weight[to_tile]).f_weight[
                        to_tile]
                lowest_list = [c_tile for c_tile in cur_marked if
                               c_tile.f_weight[to_tile] == lowest]
                try:
                    res_tile = choice(lowest_list)
                except Exception:
                    break

                way.append(res_tile)
                cur_tile = res_tile

                Window.pygame_events_handler(
                    {
                        "handler": Window.move_event_handler,
                        "args": [self.camera]
                    }
                )

            way.reverse()
            return way

        def render_ways(ways):
            for way in ways:
                if way is None:
                    continue
                for tile in way:

                    tile.upd_texture("way")

                    Window.pygame_events_handler(
                        {
                            "handler": Window.move_event_handler,
                            "args": [self.camera]
                        }
                    )
                    self.render()

                    if self.gifer:
                        self.gifer.add_img(pg.image.tostring(self.screen, "RGBA"))

        print(routes)

        for y in range(1, c.ROWS - 1):
            for x in range(1, c.COLS - 1):
                tile = self[x, y]
                tile.f_weight = {}
                if tile.status != "wall":
                    tile.neighbours = self.get_not_wall_neighbours(tile)
                    if tile.status != "way":
                        tile.upd_texture("unchecked_way")

        pairs = [(routes[i], routes[i + 1]) for i in range(len(routes) - 1)]

        ways = []
        for pair in pairs:
            if mark_tiles(*pair):
                ways.append(find_way_in_marked(*pair))

        render_ways(ways)

        print("fin")

    def save_to_txt(self, wall="▓▓", way="░░", filename="maze.txt"):
        if len(wall) != len(way):
            raise ValueError("Длина обозначения стены не может "
                             "отличаться от длины обозначения пути")
        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"wall={wall}\n")
            file.write(f"way={way}\n\n")
            for line in self:
                for tile in line:
                    if tile.status == "wall":
                        file.write(wall)
                    else:
                        file.write(way)
                file.write("\n")

    def save_to_png(self, filename="maze_sources\\maze.png"):
        save_surface = pg.Surface((26 * c.COLS, 26 * c.ROWS + 16))
        surf_rect = save_surface.get_rect()
        w_w, w_h = TileField.Tile.tiler.wall_tile_size
        f_w, f_h = TileField.Tile.tiler.floor_tile_size

        for y, line in enumerate(self):
            for x, tile in enumerate(line):
                texture_surface = tile.texture
                rect = texture_surface.get_rect()
                rect.x = x * w_w
                rect.y = y * w_w + (w_h - f_h)
                if tile.status == "wall":
                    rect.y -= int((w_h - w_w) * (w_h / w_w)) - (w_h - f_h) + 6
                save_surface.blit(texture_surface, rect)
        img = Image.frombytes('RGBA', (surf_rect.w, surf_rect.h),
                              pg.image.tostring(save_surface, 'RGBA'))
        img.save(filename)
        img.close()

    def load_from_txt(self, filename="maze_sources/maze.txt"):
        # if filename not in os.listdir():
        #     print("File Not Found")
        #     return
        with open(filename, "r", encoding="utf-8") as file:
            wall = file.readline().split("=")[-1].replace("\n", "")
            way = file.readline().split("=")[-1].replace("\n", "")
            if len(wall) != len(way):
                raise ValueError("Длина обозначения стены не может "
                                 "отличаться от длины обозначения пути")
            tile_len = len(wall)
            file.readline()
            self.clear()
            y = 0
            while (line := file.readline()) != "":
                field_line = []
                for x, inline_idx in enumerate(range(0, len(line), tile_len)):
                    if line[inline_idx:inline_idx + tile_len] == wall:
                        field_line.append(TileField.Tile(x, y, "wall"))
                    elif line[inline_idx:inline_idx + tile_len] == way:
                        field_line.append(TileField.Tile(x, y, "unchecked_way"))
                self.append(field_line)
                y += 1
            c.ROWS = y
            c.COLS = len(self[0])

    def load_from_png(self, filename="maze_sources/test2.png"):

        img = Image.open(filename)
        i_w, i_h = img.size
        img = img.resize((i_w // c.CELL_SIZE, i_h // c.CELL_SIZE),
                         resample=Image.NEAREST)
        img = img.convert('1')

        width, height = img.size
        self.clear()
        c.COLS = width
        c.ROWS = height

        for y in range(height):
            line = []
            for x in range(width):
                col = img.getpixel((x, y))
                if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                    line.append(TileField.Tile(x, y, status="wall"))
                elif col == 255:
                    line.append(TileField.Tile(x, y, "unchecked_way"))
                else:
                    line.append(TileField.Tile(x, y, "wall"))
            self.append(line)

        img.close()

    def regen(self):
        self.walls.clear()
        self.ways.clear()
        super().clear()
        self.pred_gen()
        self.generate_maze()


class Window:
    regen_event = pg.event.Event(pg.USEREVENT, name="regen")
    find_way_event = pg.event.Event(pg.USEREVENT, name="find_way")

    class Menus:
        def __init__(self, surface: pg.Surface):
            self.main_menu = pgm.Menu("Maze", surface.get_width(),
                                      surface.get_height(),
                                      theme=pgm.themes.THEME_GREEN,
                                      menu_id="main_menu")
            self.main_menu.add.label("Enter game parameters:")
            self.main_menu.add.text_input("Columns: ", default=str(c.COLS),
                                          maxchar=3,
                                          textinput_id="maze_cols",
                                          valid_chars=list("0123456789"))
            self.main_menu.add.text_input("Rows: ", default=str(c.ROWS),
                                          maxchar=3,
                                          textinput_id="maze_rows",
                                          valid_chars=list("0123456789"))
            self.main_menu.add.text_input("Cell size: ", default=str(c.CELL_SIZE),
                                          maxchar=3,
                                          textinput_id="maze_cell_size",
                                          valid_chars=list("0123456789"))
            self.main_menu.add.toggle_switch("Realtime Generation",
                                             default=c.REALTIME_GEN,
                                             toggleswitch_id="realtime")
            self.main_menu.add.toggle_switch("Do gif record",
                                             default=c.SAVE_GIF,
                                             toggleswitch_id="save_gif")
            self.main_menu.add.button("Regen", self.regen_handler)
            self.main_menu.add.button("Find Way", self.find_way_post)
            self.main_menu.add.button("IO options", self.open_io)

            self.main_menu.set_relative_position(100 / c.MENU_X, c.MENU_Y)

            self.io_menu = pgm.Menu("IO options",
                                    surface.get_width(),
                                    surface.get_height(),
                                    theme=pgm.themes.THEME_BLUE,
                                    menu_id="io_menu")
            self.io_menu.set_relative_position(100 / c.MENU_X, c.MENU_Y)

            self.io_menu.add.button("Go back", self.to_main_handler)

        def regen_handler(self):
            data = self.main_menu.get_input_data()
            c.COLS = int(data["maze_cols"])
            c.ROWS = int(data["maze_rows"])
            c.CELL_SIZE = int(data["maze_cell_size"])
            c.REALTIME_GEN = data["realtime"]
            c.SAVE_GIF = data["save_gif"]
            pg.event.post(Window.regen_event)

        def find_way_post(self):
            pg.event.post(Window.find_way_event)

        def open_io(self):
            self.main_menu._open(self.io_menu)

        def to_main_handler(self):
            self.main_menu.reset(1)

    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((c.WIDTH, c.HEIGHT), display=1)
        self.maze_surface = self.screen.subsurface((0, 0, c.MAZE_W, c.MAZE_H))
        self.menu_surface = self.screen.subsurface(c.MENU_RECT)
        self.menu = Window.Menus(self.menu_surface)
        if c.SAVE_GIF:
            self.gifer = GifSaver("images", c.MAZE_W, c.MAZE_H)
        else:
            self.gifer = None

        self.camera = Camera(self.maze_surface, c.MAZE_W, c.MAZE_H)
        self.clock = pg.time.Clock()
        self.field = TileField(
            self.maze_surface,
            self.camera,
            self.clock,
            self.gifer
        )
        self.field.generate_maze()
        self.route = []

    def pgm_events_handler(self, events):
        self.menu.main_menu.update(events)
        self.menu.main_menu.draw(self.menu_surface)

    @staticmethod
    def pygame_events_handler(*handlers):
        returns = {}
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                exit()
                pg.quit()

            for handler in handlers:
                resp = handler["handler"](event, *handler["args"])
                if resp is not None:
                    returns[handler["handler"]] = resp

        return returns, events

    @staticmethod
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

    def way_point_pick_handler(self, event):
        status = False
        left_mb, mid_mb, right_mb = pg.mouse.get_pressed()

        if event.type == pg.MOUSEBUTTONDOWN and event.button not in (4, 5):

            x, y = self.camera.apply_inverse(pg.mouse.get_pos())
            if x <= c.COLS and y <= c.ROWS:
                tile = self.field[x, y]
                if tile.status != "wall":
                    if left_mb:
                        tile.upd_texture("way")
                        self.route.append(tile)
                        status = True
                    if right_mb:
                        tile.upd_texture("unchecked_way")
                        tile.f_weight = {}
                        if tile in self.route:
                            self.route.remove(tile)
                            status = True
        return status

    def keyboard_events_handler(self, event):
        if event.type == pg.KEYDOWN:
            # if event.key in [pg.K_RETURN, pg.K_KP_ENTER]:
            #     if len(self.route) > 1:
            #         for line in self.field:
            #             for tile in line:
            #                 if tile not in self.route and tile.status != "wall":
            #                     tile.upd_texture("unchecked_way")
            #
            #         self.field.find_way(self.route)

            # if event.key == pg.K_1:
            #     x, y = self.camera.apply_inverse(pg.mouse.get_pos())
            #     tile = self.field[x, y]
            #     if tile.status == "wall":
            #         tile.upd_texture("unchecked_way")
            #     else:
            #         tile.upd_texture("wall")

            if event.key == pg.K_r:
                self.field.regen()
                self.route.clear()

            if event.key == pg.K_z:
                self.field.save_to_txt()

            if event.key == pg.K_x:
                self.field.load_from_txt()
                self.route.clear()

            if event.key == pg.K_c:
                self.field.save_to_png()

            if event.key == pg.K_v:
                self.field.load_from_png()
                self.route.clear()

    def custom_event_handler(self, event):
        if event.type == pg.USEREVENT:
            if event.name == "regen":
                self.field.regen()
                self.route.clear()
            if event.name == "find_way":
                if len(self.route) > 1:
                    for line in self.field:
                        for tile in line:
                            if tile not in self.route and tile.status != "wall":
                                tile.upd_texture("unchecked_way")

                    self.field.find_way(self.route)

    def main_loop(self):

        while True:
            returns, events = Window.pygame_events_handler(
                {
                    "handler": Window.move_event_handler,
                    "args": [self.camera]
                },
                {
                    "handler": self.way_point_pick_handler,
                    "args": []
                },
                {
                    "handler": self.keyboard_events_handler,
                    "args": []
                },
                {
                    "handler": self.custom_event_handler,
                    "args": []
                }
            )
            self.pgm_events_handler(events)

            self.field.render()
            # self.screen.fill(c.YELLOW)
            if returns.get(self.way_point_pick_handler, False) is True:
                if self.gifer:
                    self.gifer.add_img(pg.image.tostring(self.maze_surface, "RGBA"))


def main():
    window = Window()
    window.main_loop()


if __name__ == '__main__':
    main()
    # cProfile.run('main()')
