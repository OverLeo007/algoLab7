import pygame as pg

WIDTH = 800
HEIGHT = 600

CELL_SIZE = 32  # Размер клетки

COLS = WIDTH // CELL_SIZE if WIDTH // CELL_SIZE % 2 != 0 else WIDTH // CELL_SIZE - 1
ROWS = HEIGHT // CELL_SIZE if HEIGHT // CELL_SIZE % 2 != 0 else HEIGHT // CELL_SIZE - 1

# ROWS = 5
# COLS = 5

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
