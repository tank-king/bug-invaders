import asyncio
import time

import pygame

from config import *
from scene import SceneManager
from utils import *

from pygame._sdl2.video import Window, Renderer, Texture, Image

from pathlib import Path

parent = Path(__file__).parent
sys.path.append(parent.absolute().__str__())

pygame.init()

# pygame.key.set_repeat(500, 50)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT)) # , pygame.SCALED | pygame.FULLSCREEN)
        # self.window = Window("save the crabs", (WIDTH, HEIGHT))
        # self.renderer = Renderer(self.window, target_texture=True)
        # self.renderer.logical_size = (WIDTH, HEIGHT)
        self.full_screen = False
        self.manager = SceneManager()
        self.clock = pygame.time.Clock()

    def toggle_full_screen(self):
        self.full_screen = not self.full_screen
        if self.full_screen:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

    async def run(self):
        while True:
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    sys.exit(0)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_f:
                        self.toggle_full_screen()
            await asyncio.sleep(0)
            self.screen.fill((247, 213, 147))
            # self.screen.fill(0)
            self.manager.update(events)
            self.manager.draw(self.screen)
            # fps = self.clock.get_fps()
            # self.screen.blit(text('FPS', 64), (10, 20))
            # self.screen.blit(text(f'{round(fps)}', 64), (10, 80))
            # pygame.draw.rect(self.screen, 'black', VIEWPORT_RECT, 2)
            pygame.display.update()
            # self.renderer.present()
            self.clock.tick(FPS)
            # print(self.clock.get_fps())
