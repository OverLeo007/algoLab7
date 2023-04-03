import pygame as pg
import pygame_menu as pgm
import os
import consts as c


class Events:
    regen_event = pg.event.Event(pg.USEREVENT, name="regen")
    find_way_event = pg.event.Event(pg.USEREVENT, name="find_way")
    load_from_png_event = pg.event.Event(pg.USEREVENT, name="load_from", kind="png")
    save_to_png_event = pg.event.Event(pg.USEREVENT, name="save_to", kind="png")
    load_from_txt_event = pg.event.Event(pg.USEREVENT, name="load_from", kind="txt")
    save_to_txt_event = pg.event.Event(pg.USEREVENT, name="save_to", kind="txt")
    gif_toggled_event = pg.event.Event(pg.USEREVENT, name="gif_change")

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


class Menus:
    def __init__(self, surface: pg.Surface):
        self.main_menu = pgm.Menu("Maze", surface.get_width(),
                                  surface.get_height(),
                                  theme=pgm.themes.THEME_GREEN,
                                  menu_id="main_menu",
                                  position=(0, 0))
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
                                         toggleswitch_id="save_gif",
                                         onchange=self.toggle_gifer)
        self.main_menu.add.button("Regen", self.regen_handler)
        self.main_menu.add.button("Find Way", self.find_way_post)
        self.main_menu.add.button("IO options", self.open_io)

        self.io_menu = pgm.Menu("IO options",
                                surface.get_width(),
                                surface.get_height(),
                                theme=pgm.themes.THEME_BLUE,
                                menu_id="io_menu",
                                position=(0, 0))
        # self.io_menu.set_relative_position(100 / c.MENU_X, c.MENU_Y)
        self.io_menu.add.label("PNG IO", max_char=0, font_size=50)
        self.io_menu.add.text_input("File path: ",
                                    default="maze_sources/maze.png",
                                    maxchar=0,
                                    textinput_id="png_io",
                                    input_underline="_")
        self.io_menu.add.toggle_switch("Type", True,
                                       state_text=("Input", "Output"),
                                       toggleswitch_id="png_io_toggle")
        self.io_menu.add.button("Submit", self.png_submit)
        self.io_menu.add.label("TXT IO", max_char=0, font_size=50)
        self.io_menu.add.text_input("File path:",
                                    default="maze_sources/maze.txt",
                                    maxchar=0,
                                    textinput_id="txt_io",
                                    input_underline="_")
        self.io_menu.add.toggle_switch("Type", True,
                                       state_text=("Input", "Output"),
                                       toggleswitch_id="txt_io_toggle")
        self.io_menu.add.button("Submit", self.txt_submit)
        self.io_menu.add.button("Go back", self.to_main_handler)

    def regen_handler(self):
        data = self.main_menu.get_input_data()
        c.COLS = int(data["maze_cols"])
        c.ROWS = int(data["maze_rows"])
        c.CELL_SIZE = int(data["maze_cell_size"])
        c.REALTIME_GEN = data["realtime"]
        pg.event.post(Events.regen_event)

    def toggle_gifer(self, state):
        pg.event.post(Events.gif_toggled_event)

    def find_way_post(self):
        pg.event.post(Events.find_way_event)

    def open_io(self):
        self.main_menu._open(self.io_menu)

    def png_submit(self):
        data = self.io_menu.get_input_data()
        file = data["png_io"]
        toggle = data["png_io_toggle"]
        if toggle:
            Events.save_to_png_event.path = file
            pg.event.post(Events.save_to_png_event)
        else:
            if os.path.exists(file):
                Events.load_from_png_event.path = file
                pg.event.post(Events.load_from_png_event)

    def txt_submit(self):
        data = self.io_menu.get_input_data()
        file = data["txt_io"]
        toggle = data["txt_io_toggle"]
        if toggle:
            Events.save_to_txt_event.path = file
            pg.event.post(Events.save_to_txt_event)

        else:
            if os.path.exists(file):
                Events.load_from_txt_event.path = file
                pg.event.post(Events.load_from_txt_event)

    def to_main_handler(self):
        self.main_menu.reset(1)
