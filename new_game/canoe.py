# canoe.py
import pygame
from .settings import CANOE_WIDTH, CANOE_HEIGHT, BLACK

class Canoe:
    def __init__(self, x, y, boat_img=None):
        self.x, self.y = x, y
        self.width, self.height = CANOE_WIDTH, CANOE_HEIGHT
        self.speed = 5
        self.boat_img = boat_img

    def move(self, direction: str):
        if direction == "LEFT":  self.x -= self.speed
        elif direction == "RIGHT": self.x += self.speed

    def draw(self, screen):
        if self.boat_img:
            screen.blit(self.boat_img, (self.x, self.y))
        else:
            pygame.draw.rect(screen, (245,240,230),
                             (self.x, self.y, self.width, self.height), border_radius=8)
            pygame.draw.rect(screen, BLACK,
                             (self.x, self.y, self.width, self.height), 2, border_radius=8)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_collision_rect(self):
        mx, my = self.width*0.15, self.height*0.15
        return pygame.Rect(self.x+mx, self.y+my, self.width-2*mx, self.height-2*my)
