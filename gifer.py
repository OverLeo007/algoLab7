"""
Файл с классом сохраняющим гифки
"""

import os

from PIL import Image


def mk_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


class GifSaver:
    """
    Класс, сохраняющий гифки
    """

    def __init__(self, directory, screen_width, screen_height) -> None:
        # TODO: Починить создание папки для файлов
        """
        Конструктор сохранялки гифок
        :param directory: путь к директории с результирующей гифкой
        :param screen_width: ширина экрана
        :param screen_height: высота экрана
        """
        self.gif_dir = directory
        mk_dir(self.gif_dir)
        index = len(list(filter(lambda x: x.startswith("res"), os.listdir(self.gif_dir))))
        self.res_gif_path = self.gif_dir + f"\\res{index}.gif"
        self.frames = []
        self.frames_count = 0
        self.size = (screen_width, screen_height)
        self.gif_num = 1

    def add_img(self, data) -> None:
        """
        Метод добавления кадра к гифке
        :param data: bytearray картинки
        """
        img = Image.frombytes("RGBA", self.size, data)
        self.frames_count += 1
        self.frames.append(img)

        if self.frames_count:
            self.save_to_gif()

    def save_to_gif(self) -> None:
        """
        Метод сохранения гифки в директорию
        """
        self.frames[0].save(f"{self.gif_dir}\\part_gif{self.gif_num}.gif",
                            save_all=True,
                            append_images=self.frames[1:],
                            optimize=True,
                            duration=20,
                            loop=1)

        self.frames[0].close()
        self.frames.clear()
        self.frames_count = 0
        self.gif_num += 1

    def __del__(self) -> None:
        """
        Метод, вызываемый при удалении экземпляра GifSaver,
        закрывает все открытые доступы к temp гифкам и удаляет их,
        оставляя только результирующую гифку
        """
        gif_paths_list = list(map(lambda y: self.gif_dir + f"\\{y}",
                                  filter(lambda x: x.startswith("part_gif"),
                                         os.listdir(self.gif_dir))))
        gif_paths_list.sort(key=lambda x: int(x.split("\\")[-1][8:].split(".")[0]))
        gif_list = list(map(lambda x: Image.open(x), gif_paths_list))
        if not gif_list:
            return
        gif_list[0].save(self.res_gif_path,
                         save_all=True,
                         append_images=gif_list[1:],
                         optimize=True,
                         duration=20,
                         loop=0)
        for gif in gif_list:
            gif.close()
        for gif in gif_paths_list:
            os.remove(gif)
        print(f"Гифка сохранена по адресу {self.res_gif_path}")
