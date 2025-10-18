# main.py — entrypoint
import pygame, sys
from .menu import Menu
from .game_core import Game

def main():
    pygame.init()
    menu = Menu()
    settings = menu.run()
    if settings is None:
        pygame.quit(); sys.exit()
    Game(settings).run()

if __name__ == "__main__":
    main()