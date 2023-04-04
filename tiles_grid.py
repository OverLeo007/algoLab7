"""
Файл с реализацией поля клеток лабиринта и камеры для его отображения
"""

from math import ceil
from typing import List, Union
import pygame as pg
import pygame_menu as pgm
from random import randint, choice
from functools import reduce

from PIL import Image

from pg_menus import Events

from parse_tiles import Tiles
import consts as c


class Camera:
    def __init__(self, screen: pg.Surface,
                 width: Union[int, float],
                 height: Union[int, float]) -> None:
        """
        Класс камеры, позволяющий передвигаться по полю и зумить
        :param screen: экран камеры
        :param width: его ширина
        :param height: его высота
        """
        self.screen = screen
        self.x = 0
        self.y = 0
        self.default_wh = width, height
        self.width = width
        self.height = height
        self.zoom = 1.0

    def move(self, dx: Union[int, float], dy: Union[int, float]) -> None:
        """
        Передвижение камеры на определенное расстояние
        :param dx: расстояние по оси x
        :param dy: расстояние по оси y
        """
        self.x += dx
        self.y += dy

    def zoom_in(self) -> None:
        """
        Приближение камеры
        """
        self.zoom *= 1.1

    def zoom_out(self) -> None:
        """
        Отдаление камеры
        """
        self.zoom /= 1.1

    def apply(self, rect: pg.Rect) -> pg.Rect:
        """
        Метод перевода ректа клетки в рект, с учетом смещения и зума
        :param rect: рект клетки
        :return: измененный рекн
        """
        return pg.Rect(
            ceil(rect.x * self.zoom - self.x),
            ceil(rect.y * self.zoom - self.y),
            ceil(rect.width * self.zoom),
            ceil(rect.height * self.zoom)
        )

    def apply_inverse(self, pos) -> tuple[int, int]:
        """
        Метод перевода глобальных координат в координаты на поле
        :param pos: позиция в глобальных координатах
        :return: координаты клетки на которую был произведен клик
        """
        sub_pos = self.screen.get_abs_offset()
        rel_pos = pos[0] - sub_pos[0], pos[1] - sub_pos[1]
        x_sc, y_sc = (rel_pos[0] + self.x) / self.zoom, (
                rel_pos[1] + self.y) / self.zoom
        return int(x_sc / c.CELL_SIZE), int(y_sc / c.CELL_SIZE)

    def reset(self) -> None:
        """
        Сброс к начальным значениям
        """
        self.x = 0
        self.y = 0
        self.zoom = 1.0
        self.width, self.height = self.default_wh


class TileField(List[List["TileField.Tile"]]):
    class Tile:
        tiler = Tiles()
        textures_status = {
            "wall": tiler.get_random_wall,
            "way": tiler.get_random_way,
            "checked_way": tiler.get_random_checked_way,
            "unchecked_way": tiler.get_random_unchecked_way
        }

        def __init__(self, x, y, status="unchecked_way", weight=None) -> None:
            """
            Класс клетки обладающей своей текстурой,
            зависящей от статуса и координатами
            :param x: координато по оси x
            :param y: координато по оси y
            :param status: статус клетки
            :param weight: для генерации стен
            """
            self.x = x
            self.y = y
            self.status = status
            self.texture = TileField.Tile.textures_status[self.status]()
            self.weight = weight
            self.f_weight = {}
            self.neighbours = []

        def render(self, surface, cam) -> None:
            """
            Метод отрисовки клетки на холст
            :param surface: холст, куда отрисовываем
            :param cam: камера, для корректного отображения
            """
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

        def upd_texture(self, new_status) -> None:
            """
            Метод обновления текстуры клетки исходя из статуса
            :param new_status: новый статус
            """
            self.status = new_status
            self.texture = TileField.Tile.textures_status[self.status]()

        def __hash__(self) -> int:
            return hash((self.x, self.y))

        def __eq__(self, other) -> bool:
            if self.x == other.x and self.y == other.y:
                return True
            return False

        def __repr__(self) -> str:
            if self.status == "wall" and self.weight is None:
                status = "border_wall"
            elif self.status == "wall" and self.weight is not None:
                status = "maze_wall"
            else:
                status = self.status

            return f"Tile(({self.x}, {self.y}), {status}" \
                   f"{f', {self.weight}' if self.weight is not None else ''})"

    def __init__(self, screen, camera, clock, gifer=None) -> None:
        """
        Класс поля для клеток, наследованный от двумерного списка
        :param screen: холст, для отрисовки поля
        :param camera: камера
        :param clock: pygame clock для поддержания fps
        :param gifer: экземпляр GifSaver для записи гифки
        """
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

    def render(self) -> None:
        """
        Метод отрисовки поля на холст
        """
        self.screen.fill(c.BLACK)
        for line in self:
            for tile in line:
                tile.render(self.screen, self.camera)
        pg.display.flip()
        self.clock.tick(30)

    def pred_gen(self) -> None:
        """
        Метод генерации поля, где у каждой клетки соседи - стены
        """
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

    def get_not_wall_neighbours(self, tile: "TileField.Tile") -> \
            List["TileField.Tile"]:
        """
        Метод получения соседей клетки, не являющихся стенами
        :param tile: клетка
        :return: список клеток
        """
        neighbours = [
            self[tile.x - 1, tile.y],
            self[tile.x + 1, tile.y],
            self[tile.x, tile.y - 1],
            self[tile.x, tile.y + 1]

        ]
        return [tile for tile in neighbours if tile.status != "wall"]

    def generate_maze(self) -> None:
        """
        Метод генерации лабиринта по алгоритму Краскала
        """
        def unite_sets(s_list) -> List[set]:
            """
            Функция объединения пересекающихся множеств в списке
            :param s_list: список с множествами
            :return: список без пересекающихся множеств
            """
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

        if not c.REALTIME_GEN:
            menu = pgm.Menu("Generating...",
                            width=self.screen.get_width(),
                            height=self.screen.get_height(),
                            theme=pgm.themes.THEME_DARK,
                            menu_id="gen_bar",
                            position=(0, 0))
            prog_bar = menu.add.progress_bar("", default=0,
                                             width=int(
                                                 self.screen.get_width() * 0.8))

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
                Events.pygame_events_handler(
                    {
                        "handler": Events.move_event_handler,
                        "args": [self.camera]
                    }
                )
                self.render()
            else:
                percentage = round(
                    len(reduce(
                        lambda x, y: x.union(y),
                        vert_sets
                    )) / len(ways) * 100, 2
                )
                prog_bar.set_value(percentage)
                events = pg.event.get()
                menu.update(events)
                menu.draw(self.screen)
                pg.display.flip()

            idx += 1
            if vert_sets[0] == ways:
                break

    def find_way(self, routes) -> None:
        """
        Метод поиска пути в лабиринте используя
        алгоритм Ли (Волновой алгоритм)
        :param routes: список точек, в который нужно прийти по порядку
        """
        def mark_tiles(from_tile: TileField.Tile, to_tile: TileField.Tile) -> bool:
            """
            Функция отметки клеток, который просмотрены алгоритмом
            :param from_tile: начальная клетка пути
            :param to_tile: конечная клетка пути
            :return: True при наличии пути, False в обратном случае
            """
            from_tile.f_weight[to_tile] = 1
            weighted = {1: [from_tile]}

            while isinstance(to_tile.f_weight.get(to_tile, False), bool):
                cur_weight = max(weighted.keys())
                cur_wave = weighted[cur_weight]

                weighted[cur_weight + 1] = []
                appends = 0
                for cur_tile in cur_wave:
                    for n_tile in cur_tile.neighbours:

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

                Events.pygame_events_handler(
                    {
                        "handler": Events.move_event_handler,
                        "args": [self.camera]
                    }
                )

                self.render()

                if self.gifer:
                    self.gifer.add_img(pg.image.tostring(self.screen, "RGBA"))
            return True

        def find_way_in_marked(from_tile: TileField.Tile, to_tile: TileField.Tile) \
            -> List[TileField.Tile]:
            """
            Функция поиска пути в пространстве отмеченных клеток
            :param from_tile: начальная клетка
            :param to_tile: конечная клетка
            :return: список клеток, входящих в путь
            """
            way = [to_tile]
            cur_tile = to_tile
            while cur_tile != from_tile:
                neighbours = self.get_not_wall_neighbours(cur_tile)
                cur_marked = list(
                    filter(lambda c_tile: c_tile.f_weight.get(to_tile, False),
                           neighbours))

                lowest = \
                    min(cur_marked,
                        key=lambda c_tile: c_tile.f_weight[to_tile]).f_weight[
                        to_tile]
                lowest_list = [c_tile for c_tile in cur_marked if
                               c_tile.f_weight[to_tile] == lowest]
                try:
                    res_tile = choice(lowest_list)
                except Exception:
                    break

                way.append(res_tile)
                cur_tile = res_tile

                Events.pygame_events_handler(
                    {
                        "handler": Events.move_event_handler,
                        "args": [self.camera]
                    }
                )

            way.reverse()
            return way

        def render_ways(ways: List[List[TileField.Tile]]) -> None:
            """
            Функция отрисовки клеток путей на холст
            :param ways:
            """
            for way in ways:
                if way is None:
                    continue
                for tile in way:

                    tile.upd_texture("way")

                    Events.pygame_events_handler(
                        {
                            "handler": Events.move_event_handler,
                            "args": [self.camera]
                        }
                    )
                    self.render()

                    if self.gifer:
                        self.gifer.add_img(pg.image.tostring(self.screen, "RGBA"))

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

    def save_to_txt(self, wall="▓▓", way="░░", filename="maze.txt") -> None:
        """
        Функция сохранения лабиринта в txt формат
        :param wall: символы для обозначения стены
        :param way: символы для обозначения пути
        :param filename: название файла
        """
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

    def save_to_png(self, filename="maze_sources\\maze.png") -> None:
        """
        Функция сохранения лабиринта в png формат
        :param filename: название файла
        """
        f_w, f_h = TileField.Tile.tiler.floor_tile_size
        save_surface = pg.Surface((f_w * c.COLS, f_w * c.ROWS))
        surf_rect = save_surface.get_rect()

        for y, line in enumerate(self):
            for x, tile in enumerate(line):
                rect = pg.Rect(x * f_w, y * f_h, f_w, f_h)
                if self[x, y].status == "wall":
                    pg.draw.rect(save_surface, c.BLACK, rect)
                else:
                    pg.draw.rect(save_surface, c.WHITE, rect)
                # save_surface.blit(texture_surface, rect)
        img = Image.frombytes('RGBA', (surf_rect.w, surf_rect.h),
                              pg.image.tostring(save_surface, 'RGBA'))
        img.save(filename)
        img.close()

    def load_from_txt(self, filename="maze_sources/maze.txt") -> None:
        """
        Функция загрузки лабиранта из текстового файла
        :param filename: название файла
        """
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

    def load_from_png(self, filename="maze_sources/test2.png") -> None:
        """
        Функция загрузки лабиринта из картинки
        :param filename: название файла картинки
        """
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

    def regen(self) -> None:
        """
        Метод регенерации лабиринта
        """
        self.walls.clear()
        self.ways.clear()
        super().clear()
        self.pred_gen()
        self.generate_maze()
