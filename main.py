import pygame as pg
from math import ceil
import consts as c
from gifer import GifSaver
from tiles_grid import TileField
from pg_menus import Menus, Events


class Camera:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.x = 0
        self.y = 0
        self.default_wh = width, height
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

    def reset(self):
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.width, self.height = self.default_wh


class Window:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((c.WIDTH, c.HEIGHT), display=1)
        self.maze_surface = self.screen.subsurface((0, 0, c.MAZE_W, c.MAZE_H))
        self.menu_surface = self.screen.subsurface(c.MENU_RECT)
        self.menu = Menus(self.menu_surface)
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

    def way_point_pick_handler(self, event):
        status = False
        left_mb, mid_mb, right_mb = pg.mouse.get_pressed()

        if event.type == pg.MOUSEBUTTONDOWN and event.button not in (4, 5):

            x, y = self.camera.apply_inverse(pg.mouse.get_pos())
            if x <= c.COLS and y <= c.ROWS:
                try:
                    tile = self.field[x, y]
                except IndexError:
                    return status
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

    def custom_event_handler(self, event):
        if event.type == pg.USEREVENT:
            if event.name == "regen":
                self.camera.reset()
                self.field.regen()
                self.route.clear()
            elif event.name == "find_way":
                if len(self.route) > 1:
                    for line in self.field:
                        for tile in line:
                            if tile not in self.route and tile.status != "wall":
                                tile.upd_texture("unchecked_way")

                    self.field.find_way(self.route)
            elif event.name == "load_from":
                if event.kind == "txt":
                    self.camera.reset()
                    self.field.load_from_txt(event.path)
                    self.route.clear()
                elif event.kind == "png":
                    self.camera.reset()
                    self.field.load_from_png(event.path)
                    self.route.clear()
            elif event.name == "save_to":
                if event.kind == "txt":
                    self.field.save_to_txt(filename=event.path)
                elif event.kind == "png":
                    self.field.save_to_png(event.path)
            elif event.name == "gif_change":
                if c.SAVE_GIF:
                    print("Запись гифки закончена")
                    del self.gifer
                    self.gifer = None
                    self.field.gifer = None
                else:
                    print("Начата запись гифки")
                    self.gifer = GifSaver("images", c.MAZE_W, c.MAZE_H)
                    self.field.gifer = self.gifer
                c.SAVE_GIF = not c.SAVE_GIF

    def main_loop(self):

        while True:
            returns, events = Events.pygame_events_handler(
                {
                    "handler": Events.move_event_handler,
                    "args": [self.camera]
                },
                {
                    "handler": self.way_point_pick_handler,
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
