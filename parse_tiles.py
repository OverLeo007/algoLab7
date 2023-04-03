"""
Файл, содержащий класс для парсинга текстур тайлов
"""
from random import choice

import pygame as pg


class Tiles:
    floor_tile_size = 26, 26
    wall_tile_size = 26, 42

    def __init__(self, texture_folder="sources"):
        """
        Метод получения тайлов из файлов текстур и парсинга их в pygame.Surface
        :param texture_folder: папка с текстурами
        """
        floors_image = pg.image.load(f"{texture_folder}/floors.png")
        walls_image = pg.image.load(f"{texture_folder}/walls.png")
        self.unchecked_way_textures = [
            floors_image.subsurface(pg.Rect(0, 52 + 26 * i, 26, 26)) for i in
            range(3)
        ]
        self.checked_way_textures = [
            floors_image.subsurface(pg.Rect(26, 26, 26, 26)),
            floors_image.subsurface(pg.Rect(104, 26, 26, 26)),
        ]
        self.way_floor_textures = [
            floors_image.subsurface(pg.Rect(156 + 26 * i, 182, 26, 26)) for i in
            range(3)

        ]
        self.wall_textures = [
            pg.transform.scale(
                walls_image.subsurface(
                    pg.Rect(i * 24, 0, 24, 42)
                ), (26, 42)
            )
            for i in range(16)
        ]

    def get_random_wall(self) -> pg.Surface:
        """
        Метод получения случайного холста стены
        :return:
        """
        return choice(self.wall_textures)

    def get_random_way(self) -> pg.Surface:
        """
        Метод получения случайного холста пути
        :return:
        """
        return choice(self.way_floor_textures)

    def get_random_unchecked_way(self) -> pg.Surface:
        """
        Метод получения случайного холста непроверенного пути
        :return:
        """
        return choice(self.unchecked_way_textures)

    def get_random_checked_way(self) -> pg.Surface:
        """
        Метод получения случайного холста проверенного
        :return:
        """
        return choice(self.checked_way_textures)
