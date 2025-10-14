import pygame, os
from .settings import *
from .game_core import Game

BASE_DIR = os.path.dirname(__file__)

class Menu:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Canoe Game - Menu")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)

        # Background
        menu_bg = pygame.image.load(os.path.join(BASE_DIR,'images','menu.png')).convert()
        self.menu_bg = pygame.transform.scale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # Music
        pygame.mixer.init()
        pygame.mixer.music.load(os.path.join(BASE_DIR,'sounds','menu.mp3'))
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        # Buttons
        self.buttons = {
            "start": pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2, 200, 50),
            "config": pygame.Rect(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 + 80, 200, 50)
        }

        self.start_enabled = False

    def draw_buttons(self):
        for key, rect in self.buttons.items():
            # Start button is grayish before sensor configuration
            if key == "start":
                color = (100,100,100) if not self.start_enabled else (0,150,0)
            else:
                color = (0,150,0)
            pygame.draw.rect(self.screen, color, rect)
            text = self.small_font.render(key.capitalize(), True, (255,255,255))
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def configure_sensors(self):
        sensors = ["Left Paddle", "Right Paddle"]
        for sensor in sensors:
            configuring = True
            while configuring:
                self.screen.fill((0, 0, 50))
                # Background dim
                self.screen.blit(self.menu_bg, (0,0))
                # Messeage
                text = self.font.render(f"Configuring {sensor}...", True, (255, 255, 0))
                self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2))
                status_text = self.small_font.render("Press SPACE when connected", True, (200, 200, 200))
                self.screen.blit(status_text, (SCREEN_WIDTH//2 - status_text.get_width()//2, SCREEN_HEIGHT//2 + 50))
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            configuring = False  
        self.start_enabled = True  # After configuring the sensors the start button gets enabled 

    def run(self):
        menu_active = True
        while menu_active:
            self.screen.blit(self.menu_bg, (0,0))
            self.draw_buttons()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.start_enabled:
                        menu_active = False  # Start Game
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        return
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.buttons["start"].collidepoint(mouse_pos) and self.start_enabled:
                        menu_active = False
                    elif self.buttons["config"].collidepoint(mouse_pos):
                        self.configure_sensors()

            # Buttons title
            title_text = self.font.render("CANOE ROWING GAME", True, (255, 255, 255))
            instr_text = self.small_font.render("Press ENTER to Start or Q to Quit", True, (255, 255, 0))
            self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//3))
            self.screen.blit(instr_text, (SCREEN_WIDTH//2 - instr_text.get_width()//2, SCREEN_HEIGHT//3 + 60))

            pygame.display.flip()
            self.clock.tick(30)

        # Stop menu music and start game
        pygame.mixer.music.stop()
        game = Game()
        game.run()
