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
SPRITE_SIZE = 16
PLAYER_SPEED = 120 / FPS

# Считываем координаты для анимированных декораций из json
with open('maps/level1/elements_pos.json', 'r', encoding='utf8') as jsonf:
    coordinates = json.load(jsonf)

decorative = pg.sprite.Group()
chests = pg.sprite.Group()
coins = pg.sprite.Group()
animated_sprites = pg.sprite.Group()


def terminate() -> None:
    pg.quit()
    sys.exit()


class AnimatedObject(pg.sprite.Sprite):
    def __init__(self, group: list, directory: str, x: int, y: int, filename: str) -> None:
        super().__init__(*group)
        self.filename = filename
        self.pos = x, y
        self.flip = False
        self.images = [directory + f'/{filename}_{i}.png' for i in range(1, 5)]
        self.current_image = 0
        self.image = pg.image.load(self.images[self.current_image])
        self.last_tick = pg.time.get_ticks()
        self.animation_delay = 100
        self.rect = self.image.get_rect()
        screen.blit(self.image, (x, y))

    def animate(self) -> None:
        tick = pg.time.get_ticks()
        if tick - self.last_tick >= self.animation_delay:
            self.current_image = (self.current_image + 1) % 4
            if not self.flip:
                self.image = pg.image.load(self.images[self.current_image])
            else:
                self.image = pg.transform.flip(
                    pg.image.load(self.images[self.current_image]), flip_x=True, flip_y=False)
            self.last_tick = pg.time.get_ticks()
        screen.blit(self.image, self.pos)


class Torch(AnimatedObject):
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([decorative, animated_sprites], TORCHES_DIR, x, y, filename)


class Coin(AnimatedObject):
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([coins, animated_sprites], COINS_DIR, x, y, filename)


class Chest(AnimatedObject):
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([chests, animated_sprites], CHESTS_DIR, x, y, filename)


class Player(AnimatedObject):
    def __init__(self, x: int, y: int, filename: str) -> None:
        super().__init__([animated_sprites], PLAYERS_DIR, x, y, filename)

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


class Pointer(AnimatedObject):
    def __init__(self, x: int, y: int, filename) -> None:
        super().__init__([animated_sprites, decorative], POINTER_DIR, x, y, filename)


class Castle:
    def __init__(self, foldername, filename) -> None:
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

    def find_path_step(self, start, target):
        inf = 1000
        x, y = start
        distance = [[inf] * self.width for _ in range(self.height)]
        distance[y][x] = 0
        prev = [[None] * self.width for _ in range(self.height)]
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


def move_by_key(keys: pg.key.ScancodeWrapper) -> None:
    current_pos_rd = player.get_right_down_cell()
    current_pos_lu = player.get_left_up_cell()
    current_pos_ru = player.get_right_up_cell()
    current_pos_ld = player.get_left_down_cell()
    if keys[pg.K_s]:
        if castle.is_free(current_pos_rd) and castle.is_free(current_pos_ld) and \
                castle.is_free((current_pos_rd[0], (player.pos[1] + PLAYER_SPEED) // SPRITE_SIZE + 1)) and \
                castle.is_free((current_pos_ld[0], (player.pos[1] + PLAYER_SPEED) // SPRITE_SIZE + 1)):
            player.move_by_delta(dx=0, dy=PLAYER_SPEED)
    if keys[pg.K_w]:
        if castle.is_free(current_pos_ru) and castle.is_free(current_pos_lu) and \
                castle.is_free((current_pos_ru[0], (player.pos[1] - PLAYER_SPEED) // SPRITE_SIZE)) and \
                castle.is_free((current_pos_lu[0], (player.pos[1] - PLAYER_SPEED) // SPRITE_SIZE)):
            player.move_by_delta(dx=0, dy=-PLAYER_SPEED)
    if keys[pg.K_a]:
        if castle.is_free(current_pos_lu) and castle.is_free(current_pos_ld) and \
                castle.is_free(((player.pos[0] - PLAYER_SPEED) // SPRITE_SIZE, current_pos_lu[1])) and \
                castle.is_free(((player.pos[0] - PLAYER_SPEED) // SPRITE_SIZE, current_pos_ld[1])):
            player.move_by_delta(dx=-PLAYER_SPEED, dy=0)
            player.flip = True
    if keys[pg.K_d]:
        if castle.is_free(current_pos_ru) and castle.is_free(current_pos_rd) and \
                castle.is_free(((player.pos[0] + PLAYER_SPEED) // SPRITE_SIZE + 1, current_pos_ru[1])) and \
                castle.is_free(((player.pos[0] + PLAYER_SPEED) // SPRITE_SIZE + 1, current_pos_rd[1])):
            player.move_by_delta(dx=PLAYER_SPEED, dy=0)
            player.flip = False


def move_by_pointer(to: tuple[int, int], obj: Player) -> None:
    current_cell = obj.get_center_cell()
    next_pos = castle.find_path_step(current_cell, to)
    delta_x, delta_y = next_pos[0] - current_cell[0], next_pos[1] - current_cell[1]
    obj.flip = delta_x < 0
    obj.move_by_delta(dx=delta_x * PLAYER_SPEED, dy=delta_y * PLAYER_SPEED)


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
    move_to = None
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
                    move_to = event.pos[0] // SPRITE_SIZE, event.pos[1] // SPRITE_SIZE
                    if len([i for i in animated_sprites if i.filename == 'arrow']):
                        kill_arrow()
                    Pointer(move_to[0] * SPRITE_SIZE, move_to[1] * SPRITE_SIZE, 'arrow')
        move_by_key(pressed)
        if pointed:
            move_by_pointer(move_to, player)
        if player.get_center_cell() == move_to:
            pointed = False
            kill_arrow()
        castle.render()
        for sprite in animated_sprites:
            sprite.animate()
        pg.display.flip()
        clock.tick(FPS)
        screen.fill(pg.Color('black'))
