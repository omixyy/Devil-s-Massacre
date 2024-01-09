import pygame as pg
from random import choice
import sys
import pytmx
import json
from datetime import datetime
from constants import *

list_of_levels = ['level1', 'level2', 'level3', 'level4', 'level5']
available_levels = ['level1']
n_level = 0
level = list_of_levels[n_level]

chests = pg.sprite.Group()
coins = pg.sprite.Group()
animated_sprites = pg.sprite.Group()
flasks = pg.sprite.Group()
can_be_opened = pg.sprite.Group()
keys_group = pg.sprite.Group()
can_be_picked_up = pg.sprite.Group()
in_chests = pg.sprite.Group()


class AnimatedObject(pg.sprite.Sprite):
    """
    Базовый класс для всех анимированных объектов

    Атрибуты
    ------
    filename : str
        Общая часть названий группы файлов.
        Например, нужно сделать анимацию по трём кадрам: frame_1_1.png, frame_1_2.png, frame_1_3.png.
        Переменная будет хранить строку 'frame_1'
    dir : str
        Путь к кадрам для анимации
    images : list
        Список путей к кадрам вместе с их названиями
    do_blit : bool
        Отвечает за продолжение или прекращение отрисовки объекта.
        Прекратить нужно, например, в том случае, если игрок поднял объект и он оказался в инвентаре
    current_image : int
        Индекс пути к изображению в списке images.
        Нужен для смены кадра в анимации
    last_tick : int
        Миллисекунда, когда была совершена последняя смена кадра анимации.
        Нужен для измерения времени до изменения кадра
    animation_delay : int
        Количество миллисекунд, на которые нужно задерживать смену кадра анимации
    pos : tuple
        Координаты левого верхнего угла прямоугольника, описанного около изображения объекта
    image : Surface
        Текущий кадр анимации объекта
    mask : Mask
        Маска объекта.
        Нужна для определения столкновения с игроком
    rect : Rect
        Прямоугольник, в который вписано изображение объекта.

    Методы
    ------
    animate() :
        Изменяет кадр анимации.
    """

    def __init__(self, group: list | None, directory: str, x: int | None, y: int | None, filename: str) -> None:
        """
        Если x и y - None, то объект не должен появиться на карте.
        Это сделано для того, чтобы объект можно было "положить" в сундук,
        при этом не потерять возможность работать с ним как с полноценным объектом
        """
        super().__init__(*group)
        self.filename = filename
        self.dir = directory
        self.images = [directory + f'/{filename}_{i}.png' for i in range(1, 5)]
        if x is not None and y is not None:
            self.do_blit = True
            self.current_image = 0
            self.last_tick = pg.time.get_ticks()
            self.animation_delay = 100
            self.flip = False
            self.do_animation = True
            self.pos = x, y
            self.image = pg.image.load(self.images[self.current_image])
            self.mask = pg.mask.from_surface(self.image)
            self.rect = self.image.get_rect()
            self.rect.topleft = self.pos
            screen.blit(self.image, (x, y))

    def animate(self) -> None:
        if self.do_animation:
            tick = pg.time.get_ticks()
            if tick - self.last_tick >= self.animation_delay:
                self.current_image = (self.current_image + 1) % 4
                if not self.flip:
                    self.image = pg.image.load(self.images[self.current_image])
                else:
                    self.image = pg.transform.flip(
                        pg.image.load(self.images[self.current_image]), flip_x=True, flip_y=False)
                self.last_tick = pg.time.get_ticks()
        if self.do_blit:
            screen.blit(self.image, self.pos)


class MovingObject(AnimatedObject):
    """
    Базовый класс для объектов, способных двигаться (игрок, враги)

    Атрибуты
    ------
    current_direction : tuple[int, int]
        Показывает направление движения по осям x и y
    collide_vertex : tuple[int, int]
        Вершина, относительно которой рассчитывается положение объекта на карте

    Методы
    ------
    move_by_delta() :
        Изменяет положение объекта на dx и dy по осям x и y соответственно за один кадр
    get_left_up_cell() :
        Возвращает клетку, в которой находится левый верхний угол объекта
    get_left_down_cell() :
        Возвращает клетку, в которой находится левый нижний угол объекта
    get_right_up_cell() :
        Возвращает клетку, в которой находится правый верхний угол объекта
    get_right_down_cell() :
        Возвращает клетку, в которой находится правый нижний угол объекта
    get_center_cell() :
        Возвращает клетку, в которой находится центр объекта.
    """

    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([animated_sprites], PLAYERS_DIR, x, y, filename)
        self.current_direction = (0, 0)
        self.collide_vertex = self.get_center_cell()

    def move_by_delta(self, dx=1.0, dy=1.0) -> None:
        self.pos = self.pos[0] + dx, self.pos[1] + dy
        self.rect.x, self.rect.y = self.pos[0], self.pos[1]
        screen.blit(self.image, self.pos)

    def get_left_up_cell(self) -> tuple[int, int]:
        return int(self.pos[0] // SPRITE_SIZE), int(self.pos[1] // SPRITE_SIZE)

    def get_left_down_cell(self) -> tuple[int, int]:
        return int(self.pos[0] // SPRITE_SIZE), int(self.pos[1] // SPRITE_SIZE + 1)

    def get_right_up_cell(self) -> tuple[int, int]:
        return int(self.pos[0] // SPRITE_SIZE + 1), int(self.pos[1] // SPRITE_SIZE)

    def get_right_down_cell(self) -> tuple[int, int]:
        return int(self.pos[0] // SPRITE_SIZE + 1), int(self.pos[1] // SPRITE_SIZE + 1)

    def get_center_cell(self) -> tuple[int, int]:
        return (int((self.pos[0] + SPRITE_SIZE // 2) // SPRITE_SIZE),
                int((self.pos[1] + SPRITE_SIZE // 2) // SPRITE_SIZE))

    def get_center_coordinates(self):
        return self.pos[0] + SPRITE_SIZE // 2, self.pos[1] + SPRITE_SIZE // 2


class Torch(AnimatedObject):
    """
    Класс для анимирования факелов
    """

    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([animated_sprites], TORCHES_DIR, x, y, filename)


class Flag(AnimatedObject):
    """
        Класс для анимирования флагов
        """

    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([animated_sprites], FLAG_DIR, x, y, filename)


class Key(AnimatedObject):
    """
    Класс, реализующий объект "Ключ"

    Методы
    ------
    update() :
        Прекращает анимацию, если есть пересечение с игроком.
    """

    def __init__(self, x: int | None, y: int | None, filename: str) -> None:
        if x is not None and y is not None:
            group = [keys_group, animated_sprites, can_be_picked_up]
        else:
            group = [in_chests]
        super().__init__(group, KEYS_DIR, x, y, filename)

    def update(self) -> None:
        if pg.sprite.collide_mask(self, player) and player.has_free_space(KEYS_DIR + '/' + self.filename) and not throw:
            self.do_blit = False
            self.do_animation = False
            player.inventory.add(self, KEYS_DIR)


class Coin(AnimatedObject):
    """
    Класс, реализующий объект "Монета"

    Методы
    ------
    update() :
        Прекращает анимацию, если есть пересечение с игроком.
    """

    def __init__(self, x: int | None, y: int | None, filename: str) -> None:
        if x is not None and y is not None:
            group = [coins, animated_sprites, can_be_picked_up]
        else:
            group = [in_chests]
        super().__init__(group, COINS_DIR, x, y, filename)

    def update(self) -> None:
        if (pg.sprite.collide_mask(self, player) and
                player.has_free_space(COINS_DIR + '/' + self.filename) and not throw):
            self.do_blit = False
            self.do_animation = False
            player.inventory.add(self, COINS_DIR)


class TeleportFlask(AnimatedObject):
    """
    Класс, реализующий объект "Пузырёк с телепортирующей жидкостью"

    Методы
    ------
    update() :
        Прекращает анимацию, если есть пересечение с игроком.
    """

    def __init__(self, x: int | None, y: int | None, filename: str) -> None:
        if x is not None and y is not None:
            group = [flasks, animated_sprites, can_be_picked_up]
        else:
            group = [in_chests]
        super().__init__(group, FLASKS_DIR, x, y, filename)

    def update(self) -> None:
        if (pg.sprite.collide_mask(self, player) and
                player.has_free_space(FLASKS_DIR + '/' + self.filename) and not throw):
            self.do_blit = False
            self.do_animation = False
            player.inventory.add(self, FLASKS_DIR)


class HealFlask(AnimatedObject):
    """
    Класс, реализующий объект "Пузырёк с лечащей жидкостью"

    Методы
    ------
    update() :
        Прекращает анимацию, если есть пересечение с игроком.
    """

    def __init__(self, x: int | None, y: int | None, filename: str) -> None:
        if x is not None and y is not None:
            group = [flasks, animated_sprites, can_be_picked_up]
        else:
            group = [in_chests]
        super().__init__(group, FLASKS_DIR, x, y, filename)

    def update(self) -> None:
        if (pg.sprite.collide_mask(self, player) and
                player.has_free_space(FLASKS_DIR + '/' + self.filename) and not throw):
            self.do_blit = False
            self.do_animation = False
            player.inventory.add(self, FLASKS_DIR)


class Chest(AnimatedObject):
    """
    Класс, реализующий объект "Сундук"

    Атрибуты
    ------
    opened : bool
        Показывает, был ли сундук открыт или нет
    dropped : bool
        Показывает, выдавал ли сундук дроп или нет

    Методы
    ------
    update() :
        Запускает анимацию открытия при пересечении с игроком
    animate_opening() :
        Запускает анимацию открытия
    get_drop() :
        "Выдаёт" дроп из сундука
    """

    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([chests, animated_sprites, can_be_opened], CHESTS_DIR, x, y, filename)
        self.opened = False
        self.dropped = False

    def update(self) -> None:
        if pg.sprite.collide_mask(self, player) and not self.opened:
            self.animate_opening()
            self.opened = True
        if self.images[self.current_image] == CHESTS_DIR + '/chest_open_4.png':
            self.do_animation = False

    def animate_opening(self) -> None:
        self.images = [CHESTS_DIR + f'/chest_open_{i}.png' for i in range(1, 5)]
        self.current_image = 0
        self.image = pg.image.load(self.images[self.current_image])
        self.animate()

    def get_drop(self) -> pg.sprite.Sprite:
        if not self.dropped:
            self.dropped = True
            return choice([HealFlask(None, None, 'flasks_4'),
                           TeleportFlask(None, None, 'flasks_2'),
                           Key(None, None, 'keys_2')])


class Player(MovingObject):
    """
    Класс, реализующий объект игрока

    Аттрибуты
    ------
    current_slash : int
        Показывает текущий какой кадр удара
    slash_tick : int
        Показывает, сколько миллисекунд назад был изменён кадр слэша
    do_slash : bool
        Показывает, нужно ли начинать анимацию слэша, или же нет
    health : int
        Количество здоровья игрока;
    inventory : Inventory
        Объект, в котором содержатся предметы из инвентаря игрока,
        а так же отрисовываются сердечки, обозначающие здоровье.
    """

    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__(x, y, filename)
        self.current_slash = -1
        self.slash_tick = pg.time.get_ticks()
        self.do_slash = False
        self.health = 4
        self.inventory = Inventory()

    def handle_keypress(self, keys: pg.key.ScancodeWrapper) -> None:
        current_pos_rd = self.get_right_down_cell()
        current_pos_lu = self.get_left_up_cell()
        current_pos_ru = self.get_right_up_cell()
        current_pos_ld = self.get_left_down_cell()
        if keys[pg.K_s]:
            if castle.is_free(current_pos_rd) and castle.is_free(current_pos_ld) and \
                    castle.is_free((current_pos_rd[0], (self.pos[1] + PLAYER_SPEED) // SPRITE_SIZE + 1)) and \
                    castle.is_free((current_pos_ld[0], (self.pos[1] + PLAYER_SPEED) // SPRITE_SIZE + 1)):
                self.move_by_delta(dx=0, dy=PLAYER_SPEED)
        if keys[pg.K_w]:
            if castle.is_free(current_pos_ru) and castle.is_free(current_pos_lu) and \
                    castle.is_free((current_pos_ru[0], (self.pos[1] - PLAYER_SPEED) // SPRITE_SIZE)) and \
                    castle.is_free((current_pos_lu[0], (self.pos[1] - PLAYER_SPEED) // SPRITE_SIZE)):
                self.move_by_delta(dx=0, dy=-PLAYER_SPEED)
        if keys[pg.K_a]:
            if castle.is_free(current_pos_lu) and castle.is_free(current_pos_ld) and \
                    castle.is_free(((self.pos[0] - PLAYER_SPEED) // SPRITE_SIZE, current_pos_lu[1])) and \
                    castle.is_free(((self.pos[0] - PLAYER_SPEED) // SPRITE_SIZE, current_pos_ld[1])):
                self.move_by_delta(dx=-PLAYER_SPEED, dy=0)
                self.flip = True
        if keys[pg.K_d]:
            if castle.is_free(current_pos_ru) and castle.is_free(current_pos_rd) and \
                    castle.is_free(((self.pos[0] + PLAYER_SPEED) // SPRITE_SIZE + 1, current_pos_ru[1])) and \
                    castle.is_free(((self.pos[0] + PLAYER_SPEED) // SPRITE_SIZE + 1, current_pos_rd[1])):
                self.move_by_delta(dx=PLAYER_SPEED, dy=0)
                self.flip = False

    def move_by_pointer(self, to_where: tuple[int, int]) -> None:
        if self.current_direction[0] > 0:
            if (castle.get_distance_ox(self.get_left_up_cell())[1] <
                    castle.get_distance_ox(self.get_left_down_cell())[1]):
                self.collide_vertex = self.get_left_up_cell()
            elif (castle.get_distance_ox(self.get_left_up_cell())[1] >
                  castle.get_distance_ox(self.get_left_down_cell())[1]):
                self.collide_vertex = self.get_left_down_cell()
            else:
                self.collide_vertex = self.get_center_cell()

        if self.current_direction[0] < 0:
            if (castle.get_distance_ox(self.get_right_up_cell())[0] <
                    castle.get_distance_ox(self.get_right_down_cell())[0]):
                self.collide_vertex = self.get_right_up_cell()
            elif (castle.get_distance_ox(self.get_right_up_cell())[0] >
                  castle.get_distance_ox(self.get_right_down_cell())[0]):
                self.collide_vertex = self.get_right_down_cell()
            else:
                self.collide_vertex = self.get_center_cell()

        if self.current_direction[1] > 0:
            if (castle.get_distance_oy(self.get_left_up_cell())[1] <
                    castle.get_distance_oy(self.get_right_up_cell())[1]):
                self.collide_vertex = self.get_left_up_cell()
            elif (castle.get_distance_oy(self.get_left_up_cell())[1] >
                  castle.get_distance_oy(self.get_right_up_cell())[1]):
                self.collide_vertex = self.get_right_up_cell()
            else:
                self.collide_vertex = self.get_center_cell()

        if self.current_direction[1] < 0:
            if (castle.get_distance_oy(self.get_left_down_cell())[0] <
                    castle.get_distance_oy(self.get_right_down_cell())[0]):
                self.collide_vertex = self.get_left_down_cell()
            elif (castle.get_distance_oy(self.get_left_down_cell())[0] >
                  castle.get_distance_oy(self.get_right_down_cell())[0]):
                self.collide_vertex = self.get_right_down_cell()
            else:
                self.collide_vertex = self.get_center_cell()
        next_pos = castle.find_path_step(self.collide_vertex, to_where)
        dir_x, dir_y = next_pos[0] - self.collide_vertex[0], next_pos[1] - self.collide_vertex[1]
        self.current_direction = (dir_x, dir_y)
        self.flip = dir_x < 0
        self.move_by_delta(dx=dir_x * PLAYER_SPEED, dy=dir_y * PLAYER_SPEED)

    def slash(self, foldername: str, frames=6) -> None:
        slash_delay = self.animation_delay
        if 'Group' in foldername:
            slash_delay = 110
        elif 'Thin' in foldername:
            slash_delay = 50
        elif 'Wide' in foldername:
            slash_delay = 80
        if self.do_slash:
            images = [SLASH_DIR + '/' + foldername + f'/File{i}.png' for i in range(1, frames + 1)]
            tick = pg.time.get_ticks()
            image = pg.transform.scale(pg.image.load(images[self.current_slash]), (32, 32))
            if tick - self.slash_tick >= slash_delay:
                self.current_slash = (self.current_slash + 1) % frames
                image = pg.transform.scale(pg.image.load(images[self.current_slash]), (32, 32))
                self.slash_tick = pg.time.get_ticks()
            if not self.flip:
                screen.blit(image, (self.pos[0], self.pos[1] - 10))
            else:
                screen.blit(pg.transform.flip(image, flip_x=True, flip_y=False),
                            (self.pos[0] - SPRITE_SIZE, self.pos[1] - 10))
        if self.current_slash == frames - 1:
            self.current_slash = -1
            self.do_slash = False

    def use_current_item(self) -> None:
        items = self.inventory.items_images[self.inventory.current_item]
        if items and 'flasks_4' in items[0]:
            self.health += 1 if self.health < 5 else 0
            del self.inventory.items_images[self.inventory.current_item][0]

    def has_free_space(self, file: str) -> bool:
        file += '_1.png'
        return (any([file in i[0] and len(i) < 4 for i in self.inventory.items_images if i]) or
                any([len(i) == 0 for i in self.inventory.items_images]))


class Pointer(AnimatedObject):
    """
    Класс, реализующий указатель, к которому объект игрока будет идти.
    """

    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([animated_sprites], INTERFACE_DIR, x, y, filename)


class Inventory:
    """
    Класс, реализующий инвентарь игрока и хранящий информацию о его здоровье.

    Атрибуты
    ------
    items_images : list
        Хранит пути к картинкам объектов в каждой ячейке инвентаря
    image : Surface
        Изображение инвентаря
    health_image : Surface
        Изображение сердечка
    y_pos : int
        Позиция нижней панели по оси y.
        Нужна для плавного выдвижения панели
    mouse_collide : bool
        Показывает, пересекается ли изображение инвентаря с мышкой
    throwing : Surface
        Изображение выкидываемого предмета
    thrown_elem : None | str
        Путь к картинке выкинутого объекта
    current_item : int
        Показывает индекс выбранного предмета в инвентаре.

    Методы
    ------
    draw() :
        Прорисовывает сердечки и инвентарь
    update() :
        Уменьшает или увеличивает y_pos при приближении курсора к нижней части экрана
    add() :
        Добавляет объект в инвентарь
    remove() :
        Удаляет объект из инвентаря
    spawn_thrown_object() :
        Создаёт выкинутый объект на карте
    """

    def __init__(self) -> None:
        self.items_images = [[ITEMS_DIR + '/sword12.png'], [], [], []]
        self.image = pg.transform.scale(pg.image.load(INTERFACE_DIR + '/inventory1.png'), (170, 50))
        self.health_image = pg.transform.scale(pg.image.load(INTERFACE_DIR + '/heart.png'), (32, 32))
        self.y_pos = HEIGHT
        self.mouse_collide = False
        self.throwing = None
        self.thrown_elem = None
        self.current_item = 0

    def draw(self) -> None:
        screen.blit(self.image, (315, self.y_pos))
        for i in range(player.health):
            screen.blit(self.health_image, (20 + 50 * i, self.y_pos + 10))
        for ind, cell in enumerate(self.items_images):
            for item in cell:
                item_image = pg.transform.scale(pg.image.load(item), (30, 30))
                screen.blit(item_image, (331 + item_image.get_width() * ind + 6 * ind, self.y_pos + 13))
                amount = len(cell)
                if amount > 1:
                    font = pg.font.Font(None, 15)
                    rendered = font.render(f'x{amount}', 1, pg.Color('white'))
                    screen.blit(rendered, (348 + item_image.get_width() * ind + 7 * ind, self.y_pos + 35))
        cur_item_mark = pg.transform.scale(pg.image.load(INTERFACE_DIR + '/square_right_2.png'), (33, 33))
        screen.blit(cur_item_mark, (328 + cur_item_mark.get_width() *
                                    self.current_item + 4 * self.current_item, self.y_pos + 13))

    def update(self) -> None:
        if self.mouse_collide and self.y_pos >= 590:
            self.y_pos -= PLAYER_SPEED
        elif self.y_pos <= HEIGHT and not self.mouse_collide:
            self.y_pos += PLAYER_SPEED

    def add(self, obj: AnimatedObject, direct: str) -> None:
        if not throw:
            for cell in range(len(self.items_images)):
                file = direct + '/' + obj.filename + '_1.png'
                if not self.items_images[cell] and not any([file in i for i in self.items_images]):
                    self.items_images[cell].append(file)
                    break
                elif self.items_images[cell] and self.items_images[cell][0] == file and len(
                        self.items_images[cell]) < 4:
                    self.items_images[cell].append(file)
            for i in can_be_picked_up:
                if i is obj:
                    i.kill()

    def remove(self) -> None:
        del self.items_images[self.current_item][0]

    def throw(self) -> None:
        if self.current_item != 0:
            if self.items_images[self.current_item]:
                self.throwing = pg.image.load(self.items_images[self.current_item][0])
            mx, my = pg.mouse.get_pos()
            if self.throwing is not None:
                screen.blit(self.throwing, (mx - 15, my - 15))
            if self.items_images[self.current_item]:
                self.thrown_elem = self.items_images[self.current_item][0]

    def spawn_thrown_object(self) -> None:
        pos_x, pos_y = player.get_center_cell()
        spawn_pos = (pos_x + 1) * SPRITE_SIZE, (pos_y + 1) * SPRITE_SIZE
        for x, y in [(pos_x + 1, pos_y + 1), (pos_x, pos_y + 1), (pos_x - 1, pos_y + 1),
                     (pos_x + 1, pos_y), (pos_x - 1, pos_y),
                     (pos_x - 1, pos_y - 1), (pos_x, pos_y - 1), (pos_x + 1, pos_y - 1)]:
            if castle.is_free((x, y)):
                spawn_pos = list(map(int, (x * SPRITE_SIZE, y * SPRITE_SIZE)))
                break
        if 'coin' in self.thrown_elem:
            Coin(spawn_pos[0], spawn_pos[1], 'coin')
        elif 'flasks_2' in self.thrown_elem:
            TeleportFlask(spawn_pos[0], spawn_pos[1], 'flasks_2')
        elif 'flasks_4' in self.thrown_elem:
            HealFlask(spawn_pos[0], spawn_pos[1], 'flasks_4')
        elif 'keys_2' in self.thrown_elem:
            Key(spawn_pos[0], spawn_pos[1], 'keys_2')


class Castle:
    """
    Класс, реализующий объект карты

    Атрибуты
    ------
    map : TiledMap
        Сама загруженная карта
    height : int
        Высота карты в клетках
    width : int
        Ширина карты в клетках
    walls : list
        Хранит индексы тайлов, обозначающих стены

    Методы
    ------
    render() :
        Отрисовывает карту на экране
    find_path_step() :
        Алгоритм пошагового поиска клеток пути
    get_tile_id() :
        Определяет id тайла по координатам клетки
    is_free() :
        Определяет, является ли клетка стеной, или нет по её координатам
    get_distance_oy() :
        Ищет расстояние до ближайшей стены по вертикали
    get_distance_ox() :
        Ищет расстояние до ближайшей стены по горизонтали
    """

    def __init__(self, foldername: str, filename: str) -> None:
        self.map = pytmx.load_pygame(f'maps/{foldername}/{filename}')
        self.height, self.width = self.map.height, self.map.width
        self.walls = [0, 1, 2, 3, 4, 5,
                      10, 15, 20, 25, 30, 35,
                      40, 41, 42, 43, 44, 45,
                      50, 51, 52, 53, 54, 55,
                      136, 137]

    def render(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                wall_image = self.map.get_tile_image(x, y, 0)
                decoration_image = self.map.get_tile_image(x, y, 1)
                screen.blit(wall_image, (x * SPRITE_SIZE, y * SPRITE_SIZE))
                if decoration_image is not None:
                    screen.blit(decoration_image, (x * SPRITE_SIZE, y * SPRITE_SIZE))

    def find_path_step(self, start: tuple[int, int], target: tuple[int, int]) -> tuple[int, int]:
        inf = 1000
        x, y = start
        distance = [[inf] * self.width for _ in range(self.height)]
        distance[y][x] = 0
        prev = [[(None, None)] * self.width for _ in range(self.height)]
        queue = [(x, y)]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in (1, 0), (0, 1), (-1, 0), (0, -1):
                next_x, next_y = x + dx, y + dy
                if 0 <= next_x <= self.width and 0 <= next_y <= self.height and \
                        self.is_free((next_x, next_y)) and distance[next_y][next_x] == inf:
                    distance[next_y][next_x] = distance[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))
        x, y = target
        if distance[y][x] == inf or start == target:
            return start
        while prev[y][x] != start:
            x, y = prev[y][x]
        return x, y

    def get_tile_id(self, position: tuple[int, int]) -> int:
        return self.map.tiledgidmap[self.map.get_tile_gid(*position, layer=0)] - 1

    def is_free(self, position: tuple[int, int]) -> bool:
        return self.get_tile_id(position) not in self.walls

    def get_distance_oy(self, position: tuple[int, int]) -> tuple[int, int]:
        dist_up, dist_down = -1, -1
        meet_player = False
        for i in range(self.height):
            if (position[0], i) == position:
                meet_player = True
            if not meet_player:
                if not self.is_free((position[0], i)):
                    dist_up = 0
                else:
                    dist_up += 1
            else:
                if (position[0], i) == position:
                    dist_down = 0
                elif self.is_free((position[0], i)):
                    dist_down += 1
                else:
                    break
        return dist_up, dist_down

    def get_distance_ox(self, position: tuple[int, int]) -> tuple[int, int]:
        dist_right, dist_left = -1, -1
        meet_player = False
        for i in range(self.width):
            if (i, position[1]) == position:
                meet_player = True
            if not meet_player:
                if not self.is_free((i, position[1])):
                    dist_left = 0
                else:
                    dist_left += 1
            else:
                if (i, position[1]) == position:
                    dist_right = 0
                elif self.is_free((i, position[1])):
                    dist_right += 1
                else:
                    break
        return dist_left, dist_right


class Button:
    """
    Класс, реализовывающий кнопку

    Атрибуты
    ------
    image : Surface
        Изображение ненажатой кнопки
    pressed_image : Surface
        Изображение нажатой кнопки
    current_image : Surface
        Хранит то изображение, которое нужно отрисовать в данный момент
    y_pos : int
        Позиция кнопки по оси y
    rect : Rect
        Четырёхугольник, описанный около изображения
    mouse_collide : bool
        Есть ли пересечение с мышкой или нет
    pressed : bool
        Была ли кнопка нажата или нет
    unpause : bool
        Нужно ли убирать паузу или нет.
        (Если кнопка - кнопка паузы)
    clicks : int
        Количество нажатий на кнопку.

    Методы
    ------
    draw() :
        Отрисовывает кнопку
    update() :
        Меняет изображение кнопки в зависимости от количества нажатий и
        увеличивает или уменьшает y_pos.
    """

    def __init__(self, image: pg.Surface, pressed_image: pg.Surface,
                 x: int, y: int = None, select: pg.Surface = None) -> None:
        self.image = image
        self.pressed_image = pressed_image
        self.current_image = self.image
        self.select = select
        if y:
            self.y_pos = y
        else:
            self.y_pos = HEIGHT
        self.x = x
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x, self.y_pos)
        self.mouse_collide = False
        self.pressed = False
        self.unpause = True
        self.clicks = 0

    def draw(self) -> None:
        screen.blit(self.current_image, (self.x, self.y_pos))

    def draw_changing_pic(self) -> None:
        self.rect = self.current_image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y_pos
        if self.rect.collidepoint(pg.mouse.get_pos()) and self.select is not None:
            self.current_image = self.select.copy()
        else:
            self.current_image = self.image.copy()
        screen.blit(self.current_image, (self.x, self.y_pos))

    def update(self) -> None:
        if self.mouse_collide and self.y_pos >= 590:
            self.y_pos -= PLAYER_SPEED
        elif self.y_pos <= HEIGHT and not self.mouse_collide:
            self.y_pos += PLAYER_SPEED
        self.rect.topleft = (self.x, self.y_pos)
        if self.clicks % 2 == 1:
            self.current_image = self.pressed_image.copy()
            self.unpause = False
        else:
            self.current_image = self.image.copy()
            self.unpause = True
        screen.blit(self.current_image, (self.x, self.y_pos))


class ScreenDesigner:
    """
    Класс, реализующий конструктор для создания экранов (старт, выбор уровня, пауза, финиш).

    Атрибуты
    ------
    font : Font
        Пиксельный шрифт
    not_pressed : Surface
        Изображение кнопки в ненажатом состоянии
    pressed : Surface
        Изображение кнопки в нажатом состоянии
    start_button : Button
        Кнопка, запускающая уровень
    level_button : Button
        Кнопка, дающая выбрать уровень
    next_button : Button
        Кнопка, запускающая следующий уровень
    menu_button : Button
        Кнопка, выхода на стартовый экран
    exit_button : Button
        Кнопка, выхода из игры

    Методы
    ------
    render_start_window() :
        Отрисовка стартового экрана
    render_pause_window() :
        Отрисовка экрана паузы
    render_finish_window() :
        Отрисовка экрана после прохождения уровня
    render_level_window() :
        Отрисовка экрана выбора уровней
    draw_choose_level_button() :
        Отрисовка кнопки для перехода на выбранный уровень
    draw_items() :
        На экране после прохождения уровней отрисовка предметов инвентаря
    draw_next_button() :
        Отрисовка кнопки для перехода на следующий уровень
    draw_menu_button() :
        Отрисовка кнопки для перехода на стартовый экран
    draw_title() :
        Отрисовка заголовка
    draw_start_button() :
        Отрисовка кнопки для запуска уровня
    draw_level_button() :
        Отрисовка кнопки для перехода на экран выбора уровней
    draw_exit_button() :
        Отрисовка кнопки для выхода из игры
    """

    def __init__(self) -> None:
        self.font = pg.font.Font(INTERFACE_DIR + '/EpilepsySans.ttf', 50)
        self.not_pressed = pg.image.load(INTERFACE_DIR + '/UI_Flat_Banner_01_Upward.png')
        self.pressed = pg.image.load(INTERFACE_DIR + '/UI_Flat_Banner_01_Downward.png')
        self.start_button = Button(pg.transform.scale(self.not_pressed, (200, 100)),
                                   pg.transform.scale(self.pressed, (200, 100)), WIDTH // 2 - 100, HEIGHT // 2 - 50,
                                   select=pg.transform.scale(self.pressed, (200, 100)))
        self.level_button = Button(pg.transform.scale(self.not_pressed, (200, 100)),
                                   pg.transform.scale(self.pressed, (200, 100)), WIDTH // 2 - 100, HEIGHT // 2 + 50,
                                   select=pg.transform.scale(self.pressed, (200, 100)))
        self.next_button = Button(pg.transform.scale(self.not_pressed, (350, 100)),
                                  pg.transform.scale(self.pressed, (350, 100)), WIDTH // 2 - 175, HEIGHT // 4 + 150,
                                  select=pg.transform.scale(self.pressed, (350, 100)))
        self.menu_button = Button(pg.transform.scale(self.not_pressed, (200, 100)),
                                  pg.transform.scale(self.pressed, (200, 100)), WIDTH // 2 - 100, HEIGHT // 2 - 25,
                                  select=pg.transform.scale(self.pressed, (200, 100)))
        self.exit_button = Button(pg.transform.scale(self.not_pressed, (200, 100)),
                                  pg.transform.scale(self.pressed, (200, 100)), WIDTH // 2 - 100, HEIGHT // 2 + 150,
                                  select=pg.transform.scale(self.pressed, (200, 100)))
        self.list_levels_buttons = []

    def render_start_window(self) -> None:
        screen.blit(pg.transform.scale(pg.image.load(INTERFACE_DIR + '/start_screen_3.jpg'), (WIDTH, HEIGHT)), (0, 0))
        self.draw_title("Devil`s Massacre", WIDTH // 2, HEIGHT // 4)
        self.draw_exit_button(WIDTH // 2 - 100, HEIGHT // 2 + 150)
        self.draw_start_button()
        self.draw_level_button()

    def render_pause_window(self) -> None:
        self.draw_exit_button(WIDTH // 2 - 100, HEIGHT // 2 - 25)
        self.draw_menu_button(WIDTH // 2 - 100, HEIGHT // 2 - 125)

    def render_finish_window(self, play_time):
        self.draw_title("Level complete!", WIDTH // 2, HEIGHT // 4)  # title
        self.draw_title(f"Time: {play_time} seconds", WIDTH // 2, HEIGHT // 4 + 50)  # time
        self.draw_items(WIDTH // 2 - 100, HEIGHT // 4 + 75)
        self.draw_next_button()
        self.draw_menu_button(WIDTH // 2 + 50, HEIGHT // 4 + 225)
        self.draw_exit_button(WIDTH // 2 - 250, HEIGHT // 4 + 225)

    def render_level_window(self) -> None:
        screen.blit(pg.transform.scale(pg.image.load(INTERFACE_DIR + '/start_screen_3.jpg'), (WIDTH, HEIGHT)), (0, 0))
        self.draw_title('Choose level', WIDTH // 2, HEIGHT // 4)
        for i in range(5):
            self.draw_choose_level_button(i, WIDTH // 2 - 240 + (i // 3) * 240,
                                          HEIGHT // 4 + 70 * (i + 1) - (i // 3) * 211)
        self.draw_menu_button(WIDTH // 2 - 100, HEIGHT // 4 + 70 * 3 + 80)

    def draw_choose_level_button(self, i: int, x: int, y: int) -> None:
        text = self.font.render(f'Level {i + 1} ', 1, (0, 0, 0))
        self.level_button = Button(pg.transform.scale(self.not_pressed, (225, 100)),
                                   pg.transform.scale(self.pressed, (225, 100)), x, y,
                                   select=pg.transform.scale(self.pressed, (225, 100)))
        self.level_button.draw_changing_pic()
        screen.blit(text, (x + 48, y + 21))
        self.list_levels_buttons.append(self.level_button)

    def draw_items(self, x: int, y: int) -> None:
        inv = player.inventory.items_images[1::]
        unique = sum([i != [] for i in inv])
        for i in range(len(inv)):
            if not inv[i]:
                continue
            item_image = pg.transform.scale(pg.image.load(inv[i][0]), (90, 90))
            amount = len(inv[i])
            if amount > 1:
                font = pg.font.Font(None, 20)
                rendered = font.render(f'x{amount}', 1, pg.Color('white'))
                item_image.blit(rendered, (item_image.get_width() - 20, 5))
            screen.blit(item_image, (x + item_image.get_width() * i + (
                45 if unique == 1 else -45 if unique == 3 else 0), y))

    def draw_next_button(self) -> None:
        self.next_button.draw_changing_pic()
        screen.blit(self.font.render('NEXT LEVEL', 1, (0, 0, 0)),
                    (self.next_button.x + 64, self.next_button.y_pos + 21))

    def draw_menu_button(self, x: int, y: int) -> None:
        self.menu_button.x = x
        self.menu_button.y_pos = y
        self.menu_button.draw_changing_pic()
        screen.blit(self.font.render('MENU', 1, (0, 0, 0)), (x + 43, y + 21))

    def draw_title(self, text_in: str, x: int, y: int) -> None:
        text = self.font.render(text_in, True, pg.Color('bisque'))
        text_rect = text.get_rect(center=(x, y))
        screen.blit(text, text_rect)

    def draw_start_button(self) -> None:
        self.start_button.draw_changing_pic()
        screen.blit(self.font.render('START', 1, (0, 0, 0)),
                    (self.start_button.x + 42, self.start_button.y_pos + 21))

    def draw_level_button(self) -> None:
        self.level_button.draw_changing_pic()
        screen.blit(self.font.render('LEVEL', 1, (0, 0, 0)),
                    (self.level_button.x + 42, self.level_button.y_pos + 21))

    def draw_exit_button(self, x: int, y: int) -> None:
        self.exit_button.x = x
        self.exit_button.y_pos = y
        self.exit_button.draw_changing_pic()
        screen.blit(self.font.render('EXIT', 1, (0, 0, 0)),
                    (x + 65, y + 21))


def start_window() -> None:
    """
    Работа стартового экрана
    :returns: None
    """
    start_menu = ScreenDesigner()  # exit, title, start, level
    while True:
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                terminate()
                break
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if start_menu.start_button.rect.collidepoint(evt.pos):
                    run_level(level)
                if start_menu.level_button.rect.collidepoint(evt.pos):
                    level_window()
                if start_menu.exit_button.rect.collidepoint(evt.pos):
                    terminate()
                    break
        start_menu.render_start_window()
        pg.display.flip()


def finish_window(play_time: float) -> None:
    """
    Работа экрана после прохождения уровня

    Параметры
    ------
    play_time : float
        Время, за которое пройден уровень
    :returns: None
    """
    global level, available_levels, n_level
    window = ScreenDesigner()
    screen_cpy = screen.copy()
    surf_alpha = pg.Surface((WIDTH, HEIGHT))
    surf_alpha.set_alpha(128)
    available_levels.append(level)
    try:
        available_levels.append(list_of_levels[list_of_levels.index(level) + 1])
        level = available_levels[-1]
    except IndexError:
        pass
    while True:
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                terminate()
                break
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if window.menu_button.rect.collidepoint(evt.pos):
                    start_window()
                if window.exit_button.rect.collidepoint(evt.pos):
                    terminate()
                    break
                if window.next_button.rect.collidepoint(evt.pos):
                    if level in ['level4', 'level5']:
                        n_level = 0
                        level = list_of_levels[0]
                        start_window()
                    else:
                        n_level += 1
                        run_level(level)
        window.render_finish_window(play_time)
        pg.display.flip()
        clock.tick(FPS)
        screen.blit(screen_cpy, (0, 0))
        screen.blit(surf_alpha, (0, 0))


def level_window() -> None:
    """
    Работа экрана выбора уровней
    :returns: None
    """
    global level, n_level
    window = ScreenDesigner()
    while True:
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                terminate()
                break
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if window.menu_button.rect.collidepoint(evt.pos):
                    start_window()
                if any([i.rect.collidepoint(evt.pos) for i in window.list_levels_buttons]):
                    n_level = [i.rect.collidepoint(evt.pos) for i in window.list_levels_buttons].index(True)
                    level = list_of_levels[n_level]
                    if level in available_levels:
                        run_level(level)
        window.render_level_window()
        pg.display.flip()


def pause_window(pause_button: Button) -> None:
    """
    Работа экрана паузы
    :param Button pause_button: Кнопка паузы
    :returns: None
    """

    pause_menu = ScreenDesigner()
    screen_cpy = screen.copy()
    while True:
        for evt in pg.event.get():
            if evt.type == pg.QUIT:
                terminate()
                break
            elif evt.type == pg.KEYDOWN:
                if evt.key == pg.K_ESCAPE:
                    pause_button.clicks += 1
            elif evt.type == pg.MOUSEBUTTONDOWN:
                if pause_button.rect.collidepoint(evt.pos) and evt.button == 1:
                    pause_button.clicks += 1
                if pause_menu.menu_button.rect.collidepoint(evt.pos):
                    start_window()
                if pause_menu.exit_button.rect.collidepoint(evt.pos):
                    terminate()
                    break
        if pause_button.unpause:
            return
        screen.blit(screen_cpy, (0, 0))
        pause_menu.render_pause_window()
        pause_button.update()
        pg.display.flip()
        clock.tick(FPS)


def add_items() -> None:
    """
    Добавление различных элементов на карту.
    :returns: None
    """

    # Считываем координаты для анимированных декораций из json
    with open(f'maps/{level}/elements_pos.json', 'r', encoding='utf8') as jsonf:
        coordinates = json.load(jsonf)
    for elem, crd in coordinates.items():
        for pos in crd:
            pos_x, pos_y = pos[0] * SPRITE_SIZE, pos[1] * SPRITE_SIZE
            if elem == 'torches':
                Torch(pos_x, pos_y, 'torch')
            elif elem == 'side-torches':
                Torch(pos_x, pos_y, 'side_torch')
            elif elem == 'coins':
                Coin(pos_x, pos_y, 'coin')
            elif elem == 'teleport-flasks':
                TeleportFlask(pos_x, pos_y, 'flasks_2')
            elif elem == 'heal-flasks':
                HealFlask(pos_x, pos_y, 'flasks_4')
            elif elem == 'key':
                Key(pos_x, pos_y, 'keys_2')
            elif elem == 'big-chests':
                Chest(pos_x, pos_y, 'chest')
            elif elem == 'candle-stick':
                Torch(pos_x, pos_y, 'candlestick_2')
            elif elem == 'flag':
                Flag(pos_x, pos_y, 'flag')


def clear_all_groups() -> None:
    """
    Очистка групп от спрайтов
    :returns: None
    """

    chests.empty()
    coins.empty()
    animated_sprites.empty()
    flasks.empty()
    can_be_opened.empty()
    keys_group.empty()
    can_be_picked_up.empty()
    in_chests.empty()


def run_level(lvl: str) -> None:
    """
    Запуск уровня
    :returns: None
    """

    global throw, player, castle
    clear_all_groups()
    add_items()
    for i in animated_sprites:
        if isinstance(i, Player):
            i.kill()
    castle = Castle(lvl, lvl + '.tmx')
    player = Player(2 * SPRITE_SIZE, 2 * SPRITE_SIZE, 'priest3_v2')
    pause_button = Button(pg.transform.scale(
        pg.image.load(
            INTERFACE_DIR + '/UI_Flat_Button_Large_Lock_01a1.png'), (50, 50)),
        pg.transform.scale(pg.image.load(
            INTERFACE_DIR + '/UI_Flat_Button_Large_Lock_01a2.png'), (50, 50)), 745)
    slash_name = 'Blue Slash Thin'
    running = True
    pointed = False
    throw = False
    shift_pressed = False
    ctrl_pressed = False
    move_to_cell = None
    lmb_pressed = False
    inv_collide = False
    continued = False
    start = datetime.now()
    while running:
        pressed = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
                terminate()
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_LSHIFT:
                    shift_pressed = True
                elif event.key == pg.K_LCTRL:
                    ctrl_pressed = True
                elif event.key == pg.K_1:
                    player.inventory.current_item = 0
                elif event.key == pg.K_2:
                    player.inventory.current_item = 1
                elif event.key == pg.K_3:
                    player.inventory.current_item = 2
                elif event.key == pg.K_4:
                    player.inventory.current_item = 3
            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    lmb_pressed = True
                    inv_collide = pg.Rect((330 + 33 * player.inventory.current_item + 3 * player.inventory.current_item,
                                           player.inventory.y_pos + 15, 33, 33)).collidepoint(event.pos)
                    mouse_x, _ = event.pos
                    if inventory_rect.collidepoint(event.pos):
                        cur = (mouse_x - 330) // 36
                        if 0 <= cur <= 3:
                            player.inventory.current_item = cur
                    elif pause_button.rect.collidepoint(event.pos):
                        pause_button.clicks += 1
                    elif (not shift_pressed and not ctrl_pressed and
                          not player.do_slash and player.inventory.current_item == 0):
                        player.do_slash = True
                        slash_name = 'Blue Slash Thin'
                    elif shift_pressed and not player.do_slash and player.inventory.current_item == 0:
                        player.do_slash = True
                        slash_name = 'Blue Slash Wide'
                    elif ctrl_pressed and not player.do_slash and player.inventory.current_item == 0:
                        player.do_slash = True
                        slash_name = 'Blue Group Slashes'
                    elif player.inventory.current_item != 0:
                        player.use_current_item()
                elif event.button == 3:
                    pointed = True
                    move_to_cell = event.pos[0] // SPRITE_SIZE, event.pos[1] // SPRITE_SIZE
                    if len([i for i in animated_sprites if i.filename == 'arrow']):
                        kill_arrow()
                    if castle.is_free((move_to_cell[0], move_to_cell[1])):
                        Pointer(event.pos[0] - 10, event.pos[1] - 15, 'arrow')
            elif event.type == pg.MOUSEBUTTONUP:
                if event.button == 1:
                    lmb_pressed = False
                    throw = False
            elif event.type == pg.KEYUP:
                if event.key == pg.K_LSHIFT:
                    shift_pressed = False
                elif event.key == pg.K_LCTRL:
                    ctrl_pressed = False
            elif event.type == pg.MOUSEMOTION:
                collide = lower_rect.collidepoint(event.pos)
                player.inventory.mouse_collide = collide
                pause_button.mouse_collide = collide
                if inv_collide:
                    throw = lmb_pressed
        if pointed:
            player.move_by_pointer(move_to_cell)
        else:
            player.handle_keypress(pressed)
        if player.collide_vertex == move_to_cell:
            pointed = False
            kill_arrow()
        castle.render()
        if player.do_slash:
            if slash_name != 'Blue Group Slashes':
                player.slash(slash_name)
            else:
                player.slash(slash_name, frames=20)
        for sprite in animated_sprites:
            sprite.animate()
        for chest in chests:
            chest.update()
            if chest.opened and not chest.dropped:
                drop = chest.get_drop()
                player.inventory.add(drop, drop.dir)
        for sprite in can_be_picked_up:
            sprite.update()
        player.inventory.draw()
        player.inventory.update()
        pause_button.draw()
        pause_button.update()
        if throw:
            player.inventory.throw()
        elif player.inventory.throwing is not None:
            player.inventory.spawn_thrown_object()
            player.inventory.remove()
        if not throw:
            player.inventory.throwing = None
        pg.display.flip()
        clock.tick(FPS)
        if continued and not pause_button.unpause:
            pause_window(pause_button)
            continued = False
        if not pause_button.unpause:
            continued = True

        # TODO: Переделать условие окончания раунда
        if sum([i != [] for i in player.inventory.items_images]) == 4:
            finish = datetime.now()
            finish_window(round((finish - start).total_seconds(), 3))


def kill_arrow() -> None:
    """
    Убирает объект указателя из группы animated_sprites,
    тем самым он перестаёт отрисовываться.
    :returns: None
    """
    for obj in animated_sprites:
        if obj.filename == 'arrow':
            obj.kill()


def terminate() -> None:
    """
    Выход из игры.
    :returns: None
    """
    pg.quit()
    sys.exit()


# ЗАПУСК
if __name__ == '__main__':
    pg.init()
    pg.display.set_caption("Devil's Massacre")
    screen = pg.display.set_mode((WIDTH := 800, HEIGHT := 640))
    screen.fill(pg.Color('black'))
    lower_rect = pg.Rect(0, 590, 800, 50)
    inventory_rect = pg.Rect(315, 590, 170, 50)
    clock = pg.time.Clock()
    start_window()
