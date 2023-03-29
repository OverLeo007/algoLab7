WIDTH = 800
HEIGHT = 600

CELL_SIZE = 32  # Размер клетки

ROWS = WIDTH // CELL_SIZE if WIDTH // CELL_SIZE % 2 != 0 else WIDTH // CELL_SIZE - 1
COLS = HEIGHT // CELL_SIZE if HEIGHT // CELL_SIZE % 2 != 0 else HEIGHT // CELL_SIZE - 1

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

tileset_path = "sources"
