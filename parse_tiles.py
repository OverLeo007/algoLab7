from random import choice

import pygame as pg
import consts as c


class Tiles:
    floor_tile_size = 26, 26
    wall_tile_size = 26, 42

    def __init__(self, texture_folder="sources"):
        floors_image = pg.image.load(f"{texture_folder}/floors.png")
        walls_image = pg.image.load(f"{texture_folder}/walls.png")
        self.unchecked_way_textures = [
            floors_image.subsurface(pg.Rect(0, 52 + 26 * i, 26, 26)) for i in range(3)
        ]
        self.checked_way_textures = [
            floors_image.subsurface(pg.Rect(26, 26, 26, 26)),
            floors_image.subsurface(pg.Rect(104, 26, 26, 26)),
        ]
        self.way_floor_textures = [
            floors_image.subsurface(pg.Rect(156 + 26 * i, 182, 26, 26)) for i in range(3)

        ]
        self.wall_textures = [
            pg.transform.scale(
                walls_image.subsurface(
                    pg.Rect(i * 24, 0, 24, 42)
                ), (26, 42)
            )
            for i in range(16)
        ]


    def get_random_wall(self):
        return choice(self.wall_textures)

    def get_random_way(self):
        return choice(self.way_floor_textures)

    def get_random_unchecked_way(self):
        return choice(self.unchecked_way_textures)

    def get_random_checked_way(self):
        return choice(self.checked_way_textures)


def main():
    pg.init()
    screen = pg.display.set_mode((c.WIDTH, c.HEIGHT))

    tiler = Tiles()

    scale = 3
    for i in range(10):
        # screen.blit(pg.transform.rotozoom(tiler.get_random_unchecked_way(), 0, scale),
        #             (i * 26 * scale, 26 * scale * 3, 26 * scale, 26 * scale))
        # screen.blit(pg.transform.rotozoom(tiler.get_random_checked_way(), 0, scale),
        #             (i * 26 * scale, 26 * scale, 26 * scale, 26 * scale))
        # screen.blit(pg.transform.rotozoom(tiler.get_random_way(), 0, scale),
        #             (i * 26 * scale, 26 * scale * 2, 26 * scale, 26 * scale))
        screen.blit(pg.transform.rotozoom(tiler.get_random_wall(), 0, scale),
                    (i * 26 * scale, 0, 26 * scale, 26 * scale))
        # screen.blit(pg.transform.rotozoom(tiler.get_random_way("checked"), 0, scale),
        #             (i * 26 * scale, 52 * scale, 26 * scale, 26 * scale))
        # screen.blit(pg.transform.rotozoom(tiler.get_random_way("way"), 0, scale),
        #             (i * 26 * scale, 78 * scale, 26 * scale, 26 * scale))
        # screen.blit(pg.transform.rotozoom(tiler.get_random_wall(), 0, scale),
        #             (i * 26 * scale, 0, 26 * scale, 26 * scale))

    pg.display.flip()
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit()


if __name__ == '__main__':
    main()
