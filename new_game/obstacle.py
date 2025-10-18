# obstacle.py
import pygame
from .settings import OBSTACLE_WIDTH, OBSTACLE_HEIGHT

class Obstacle:
    def __init__(self, x, y, rock_img=None, size=None):
        self.x = x
        self.y = y
        self.rock_img = rock_img
        if size:
            self.width, self.height = int(size[0]), int(size[1])
        elif rock_img:
            self.width, self.height = rock_img.get_width(), rock_img.get_height()
        else:
            self.width, self.height = OBSTACLE_WIDTH, OBSTACLE_HEIGHT
        self.counted = False

    def update(self, dy):
        self.y += dy

    def draw(self, screen):
        if self.rock_img:
            screen.blit(self.rock_img, (self.x, self.y))
        else:
            pygame.draw.rect(screen, (100,170,120),
                             (self.x, self.y, self.width, self.height),
                             border_radius=6)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def offscreen(self, h):
        return self.y > h + 40
