import pygame as pg
import sys
import pytmx
import json

# Константы
FPS = 60
TORCHES_DIR = 'tiles/2D Pixel Dungeon Asset Pack/items and trap_animation/torch'
COINS_DIR = 'tiles/2D Pixel Dungeon Asset Pack/items and trap_animation/coin'
CHESTS_DIR = 'tiles/2D Pixel Dungeon Asset Pack/items and trap_animation/chest'
PLAYERS_DIR = 'tiles/2D Pixel Dungeon Asset Pack/Character_animation/priests_idle/priest3/v2'
POINTER_DIR = 'tiles/2D Pixel Dungeon Asset Pack/interface'
FLASKS_DIR = 'tiles/2D Pixel Dungeon Asset Pack/items and trap_animation/flasks'
SPRITE_SIZE = 16
PLAYER_SPEED = 120 / FPS

# Считываем координаты для анимированных декораций из json
with open('maps/level1/elements_pos.json', 'r', encoding='utf8') as jsonf:
    coordinates = json.load(jsonf)

decorative = pg.sprite.Group()
chests = pg.sprite.Group()
coins = pg.sprite.Group()
animated_sprites = pg.sprite.Group()
flasks = pg.sprite.Group()
can_be_opened = pg.sprite.Group()


def terminate() -> None:
    pg.quit()
    sys.exit()


class AnimatedObject(pg.sprite.Sprite):
    """
    Базовый класс для всех анимированных объектов
    """
    def __init__(self, group: list, directory: str, x: int, y: int, filename: str) -> None:
        super().__init__(*group)
        self.filename = filename
        self.pos = x, y
        self.flip = False
        self.do_animation = True
        self.do_blit = True
        self.images = [directory + f'/{filename}_{i}.png' for i in range(1, 5)]
        self.current_image = 0
        self.image = pg.image.load(self.images[self.current_image])
        self.mask = pg.mask.from_surface(self.image)
        self.last_tick = pg.time.get_ticks()
        self.animation_delay = 100
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
    """
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([animated_sprites], PLAYERS_DIR, x, y, filename)
        self.current_dir = (0, 0)
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

    def get_center_coordinates(self) -> tuple[float, float]:
        return self.pos[0] + SPRITE_SIZE / 2, self.pos[1] + SPRITE_SIZE / 2


class Torch(AnimatedObject):
    """
    Заготовка под будущий класс
    """
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([decorative, animated_sprites], TORCHES_DIR, x, y, filename)


class Coin(AnimatedObject):
    """
    Заготовка под будущий класс
    """
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([coins, animated_sprites], COINS_DIR, x, y, filename)

    def update(self) -> None:
        if pg.sprite.collide_mask(self, player):
            self.do_blit = False
            self.do_animation = False


class Chest(AnimatedObject):
    """
    Заготовка под будущий класс
    """
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([chests, animated_sprites, can_be_opened, can_be_opened], CHESTS_DIR, x, y, filename)
        self.opened = False

    def update(self) -> None:
        if pg.sprite.collide_mask(self, player) and not self.opened:
            self.animate_opening()
            self.opened = True
        if self.images[self.current_image] == CHESTS_DIR + '/' + 'chest_open_4.png':
            self.do_animation = False

    def animate_opening(self) -> None:
        self.images = [CHESTS_DIR + f'/chest_open_{i}.png' for i in range(1, 5)]
        self.current_image = 0
        self.image = pg.image.load(self.images[self.current_image])
        self.animate()


class TeleportFlask(AnimatedObject):
    """
    Заготовка под будущий класс
    """
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([flasks, animated_sprites], FLASKS_DIR, x, y, filename)

    def update(self) -> None:
        if pg.sprite.collide_mask(self, player):
            self.do_blit = False
            self.do_animation = False


class HealFlask(AnimatedObject):
    """
    Заготовка под будущий класс
    """
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([flasks, animated_sprites], FLASKS_DIR, x, y, filename)

    def update(self) -> None:
        if pg.sprite.collide_mask(self, player):
            self.do_blit = False
            self.do_animation = False


class Player(MovingObject):
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__(x, y, filename)

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
        if self.current_dir[0] > 0:
            if (castle.get_distance_ox(self.get_left_up_cell())[1] <
                    castle.get_distance_ox(self.get_left_down_cell())[1]):
                self.collide_vertex = self.get_left_up_cell()
            elif (castle.get_distance_ox(self.get_left_up_cell())[1] >
                  castle.get_distance_ox(self.get_left_down_cell())[1]):
                self.collide_vertex = self.get_left_down_cell()
            else:
                self.collide_vertex = self.get_center_cell()

        if self.current_dir[0] < 0:
            if (castle.get_distance_ox(self.get_right_up_cell())[0] <
                    castle.get_distance_ox(self.get_right_down_cell())[0]):
                self.collide_vertex = self.get_right_up_cell()
            elif (castle.get_distance_ox(self.get_right_up_cell())[0] >
                  castle.get_distance_ox(self.get_right_down_cell())[0]):
                self.collide_vertex = self.get_right_down_cell()
            else:
                self.collide_vertex = self.get_center_cell()

        if self.current_dir[1] > 0:
            if (castle.get_distance_oy(self.get_left_up_cell())[1] <
                    castle.get_distance_oy(self.get_right_up_cell())[1]):
                self.collide_vertex = self.get_left_up_cell()
            elif (castle.get_distance_oy(self.get_left_up_cell())[1] >
                  castle.get_distance_oy(self.get_right_up_cell())[1]):
                self.collide_vertex = self.get_right_up_cell()
            else:
                self.collide_vertex = self.get_center_cell()

        if self.current_dir[1] < 0:
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
        self.current_dir = (dir_x, dir_y)
        self.flip = dir_x < 0
        self.move_by_delta(dx=dir_x * PLAYER_SPEED, dy=dir_y * PLAYER_SPEED)


class Pointer(AnimatedObject):
    def __init__(self, x: int, y: int, filename) -> None:
        super().__init__([animated_sprites, decorative], POINTER_DIR, x, y, filename)


class Castle:
    def __init__(self, foldername: str, filename: str) -> None:
        self.map = pytmx.load_pygame(f'maps/{foldername}/{filename}')
        self.height, self.width = self.map.height, self.map.width
        self.walls = [0, 1, 2, 3, 4, 5,
                      10, 15, 20, 25, 30, 35,
                      40, 41, 42, 43, 44, 45,
                      50, 51, 52, 53, 54, 55]

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

    def get_tile_id(self, position) -> int:
        return self.map.tiledgidmap[self.map.get_tile_gid(*position, layer=0)] - 1

    def is_free(self, position) -> bool:
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


def add_decor_elements() -> None:
    for elem, crd in coordinates.items():
        for pos in crd:
            pos_x, pos_y = pos[0] * SPRITE_SIZE, pos[1] * SPRITE_SIZE
            if elem == 'torches':
                Torch(pos_x, pos_y, 'torch')
            elif elem == 'side-torches':
                Torch(pos_x, pos_y, 'side_torch')
            elif elem == 'coins':
                Coin(pos_x, pos_y, 'coin')
            elif elem == 'big-chests':
                Chest(pos_x, pos_y, 'chest')
            elif elem == 'teleport-flasks':
                TeleportFlask(pos_x, pos_y, 'flasks_2')
            elif elem == 'heal-flasks':
                HealFlask(pos_x, pos_y, 'flasks_4')


def kill_arrow() -> None:
    for obj in animated_sprites:
        if obj.filename == 'arrow':
            obj.kill()


if __name__ == '__main__':
    pg.init()
    pg.display.set_caption("Devil's Massacre")
    screen = pg.display.set_mode((WIDTH := 800, HEIGHT := 640))
    screen.fill(pg.Color('black'))
    castle = Castle('level1', 'level1.tmx')
    running = True
    pointed = False
    move_to_cell = None
    clock = pg.time.Clock()
    castle.render()
    add_decor_elements()
    player = Player(2 * SPRITE_SIZE, 2 * SPRITE_SIZE, 'priest3_v2')
    while running:
        pressed = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                terminate()
                running = False
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 3:
                    pointed = True
                    move_to_cell = event.pos[0] // SPRITE_SIZE, event.pos[1] // SPRITE_SIZE
                    if len([i for i in animated_sprites if i.filename == 'arrow']):
                        kill_arrow()
                    if castle.is_free((move_to_cell[0], move_to_cell[1])):
                        Pointer(event.pos[0] - 10, event.pos[1] - 15, 'arrow')
        player.handle_keypress(pressed)
        if pointed:
            player.move_by_pointer(move_to_cell)
        if player.collide_vertex == move_to_cell:
            pointed = False
            kill_arrow()
        castle.render()
        for sprite in animated_sprites:
            sprite.animate()
        for chest in chests:
            chest.update()
        for coin in coins:
            coin.update()
        for flask in flasks:
            flask.update()
        pg.display.flip()
        clock.tick(FPS)
        screen.fill(pg.Color('black'))
