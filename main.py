import pygame as pg
import sys
import pytmx
import json
FPS = 50
TORCHES_DIR = 'tiles/2D Pixel Dungeon Asset Pack/items and trap_animation/torch'
COINS_DIR = 'tiles/2D Pixel Dungeon Asset Pack/items and trap_animation/coin'
CHESTS_DIR = 'tiles/2D Pixel Dungeon Asset Pack/items and trap_animation/chest'
PLAYERS_DIR = 'tiles/2D Pixel Dungeon Asset Pack/Character_animation/priests_idle/priest3/v2'
SPRITE_SIZE = 16

with open('maps/level1/elements_pos.json', 'r', encoding='utf8') as jsonf:
    coordinates = json.load(jsonf)

decorative = pg.sprite.Group()
chests = pg.sprite.Group()
coins = pg.sprite.Group()
animated_sprites = pg.sprite.Group()


def terminate():
    pg.quit()
    sys.exit()


class AnimatedObject(pg.sprite.Sprite):
    def __init__(self, group, directory, x, y, filename, **kwargs):
        super().__init__(group)
        self.pos = x, y
        self.images = [directory + f'/{filename}_{i}.png' for i in range(1, 5)]
        self.current_image = 0
        self.image = pg.image.load(self.images[self.current_image])
        self.last_tick = pg.time.get_ticks()
        self.animation_delay = 90
        screen.blit(self.image, (x, y))

    def animate(self):
        tick = pg.time.get_ticks()
        if tick - self.last_tick >= self.animation_delay:
            self.current_image = (self.current_image + 1) % 4
            self.image = pg.image.load(self.images[self.current_image])
            self.last_tick = pg.time.get_ticks()
        screen.blit(self.image, self.pos)


class Torch(AnimatedObject):
    def __init__(self, x, y, filename):
        super().__init__([decorative, animated_sprites], TORCHES_DIR, x, y, filename)


class Coin(AnimatedObject):
    def __init__(self, x, y, filename):
        super().__init__([coins, animated_sprites], COINS_DIR, x, y, filename)


class Chest(AnimatedObject):
    def __init__(self, x, y, filename):
        super().__init__([chests, animated_sprites], CHESTS_DIR, x, y, filename)


class Player(AnimatedObject):
    def __init__(self, x, y, filename):
        super().__init__(animated_sprites, PLAYERS_DIR, x, y, filename)


class Castle:
    def __init__(self, foldername,  filename):
        self.map = pytmx.load_pygame(f'maps/{foldername}/{filename}')
        self.height, self.width = self.map.height, self.map.width
        self.tile_size = self.map.tilewidth

    def render(self):
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)
                screen.blit(image, (x * self.tile_size, y * self.tile_size))


if __name__ == '__main__':
    pg.init()
    pg.display.set_caption("Devil's Massacre")
    screen = pg.display.set_mode((WIDTH := 800, HEIGHT := 640))
    screen.fill(pg.Color('black'))
    castle = Castle('level1', 'level1.tmx')
    running = True
    clock = pg.time.Clock()
    castle.render()
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
    player = Player(2 * SPRITE_SIZE, 2 * SPRITE_SIZE, 'priest3_v2')
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                terminate()
                running = False
        castle.render()
        for sprite in animated_sprites:
            sprite.animate()
        pg.display.flip()
        clock.tick(FPS)
        screen.fill(pg.Color('black'))

