import pygame as pg
from math import ceil
import consts as c
from line_profiler_pycharm import profile


class Tile:
    def __init__(self, x, y, col=c.WHITE):
        self.x = x
        self.y = y
        self.col = col

    def draw(self, surface, cam):
        rect = pg.Rect(self.x * c.CELL_SIZE, self.y * c.CELL_SIZE, c.CELL_SIZE,
                       c.CELL_SIZE)
        rect = cam.apply(rect)
        pg.draw.rect(surface, self.col, rect)
        pg.draw.rect(surface, c.BLACK, rect, 1)


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


@profile
def main():
    pg.init()
    screen = pg.display.set_mode((c.WIDTH, c.HEIGHT))

    tiles = []
    for x in range(c.ROWS):
        line = []
        for y in range(c.COLS):
            line.append(Tile(x, y))
        tiles.append(line)

    camera = Camera(c.WIDTH, c.HEIGHT)

    texture_image = pg.image.load('sourses/tileset.png')  # загружаем изображение
    texture = texture_image.subsurface(
        pg.Rect(0, 0, 64, 64))  # получаем текстуру из области 0,0 - 64x64
    texture_rect = texture.get_rect()
    texture_rect.x = 100
    texture_rect.y = 100

    clock = pg.time.Clock()

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

    last_drawed = None

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

            if pg.mouse.get_pressed(3)[0]:
                x, y = camera.apply_inverse(pg.mouse.get_pos())
                tile = tiles[x][y]
                if last_drawed != tile:
                    last_drawed = tile
                    if tile.col == c.WHITE:
                        tile.col = c.GREEN
                    else:
                        tile.col = c.WHITE

            if event.type == pg.KEYDOWN:
                if move_dir := controls.get(event.key, False):
                    move_dir['state'] = True
                else:
                    x, y = camera.apply_inverse(pg.mouse.get_pos())
                    print(x, y)

            if event.type == pg.KEYUP:
                if move_dir := controls.get(event.key, False):
                    move_dir['state'] = False

        for val in controls.values():
            if val['state'] is True:
                camera.move(*val['args'])

        screen.fill((0, 0, 0))

        screen.blit(texture, texture_rect)

        # for line in tiles:
        #     for tile in line:
        #         tile.draw(screen, camera)

        pg.display.flip()

        clock.tick(60)

    pg.quit()


if __name__ == '__main__':
    main()
