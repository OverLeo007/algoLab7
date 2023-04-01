import pygame as pg

WIDTH = 1920
HEIGHT = 1035

MAZE_W = int(WIDTH * 0.7)
MAZE_H = int(HEIGHT)

# CELL_SIZE = int((MAZE_W + MAZE_H) // 2 * 0.05)  # Размер клетки
CELL_SIZE = 16
#
# COLS = int(MAZE_W // CELL_SIZE if MAZE_W // CELL_SIZE % 2 != 0 else MAZE_W // CELL_SIZE - 1)
# ROWS = int(MAZE_H // CELL_SIZE if MAZE_H // CELL_SIZE % 2 != 0 else MAZE_H // CELL_SIZE - 1)

ROWS = 25
COLS = 25

FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

tileset_path = "sources"

REALTIME_GEN = False
SAVE_GIF = False

CONTROLS = {
    pg.K_w: {
        'state': False,
        'args': [0, -CELL_SIZE]
    },
    pg.K_s: {
        'state': False,
        'args': [0, CELL_SIZE]
    },
    pg.K_a: {
        'state': False,
        'args': [-CELL_SIZE, 0]
    },
    pg.K_d: {
        'state': False,
        'args': [CELL_SIZE, 0]
    }
}
