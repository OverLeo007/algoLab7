"""
Основной файл - точка входа
"""
from typing import List

import pygame as pg
import consts as c
from gifer import GifSaver
from tiles_grid import TileField, Camera
from pg_menus import Menus, Events


class Window:
    def __init__(self) -> None:
        """
        Класс окна приложения
        """
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

    def pgm_events_handler(self, events: List[pg.event.Event]) -> None:
        """
        Метод передающий ивенты pygame в меню
        :param events: список ивентов
        """
        self.menu.main_menu.update(events)
        self.menu.main_menu.draw(self.menu_surface)

    def way_point_pick_handler(self, event: pg.event.Event) -> bool:
        """
        Метод поддрежки нажатий мыши на поле
        :param event: pygame ивент
        :return: True если список выбранных клеток был изменен
        """
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

    def custom_event_handler(self, event: pg.event.Event) -> None:
        """
        Метод поддержки кастомных ивентов, определенных в pg_menus.Events
        :param event: pygame ивент
        """
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

    def main_loop(self) -> None:
        """
        Метод главного цикла pygame
        """
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
