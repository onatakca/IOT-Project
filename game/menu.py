# game/menu.py
import pygame, os
from .settings import *
from .ble_message import Message

BASE_DIR = os.path.dirname(__file__)

class Menu:
    def __init__(self, ble_message: Message):
        self.ble_paddles = ble_message
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Canoe Game - Menu")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 36)

        # Background
        menu_bg = pygame.image.load(os.path.join(BASE_DIR, 'images', 'menu.png')).convert()
        self.menu_bg = pygame.transform.scale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        # Music
        pygame.mixer.init()
        pygame.mixer.music.load(os.path.join(BASE_DIR, 'sounds', 'menu.mp3'))
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
            if key == "start":
                color = (100, 100, 100) if not self.start_enabled else (0, 150, 0)
            else:
                color = (0, 150, 0)
            pygame.draw.rect(self.screen, color, rect)
            text = self.small_font.render(key.capitalize(), True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def configure_sensors(self):
        configuring = True
        while configuring:
            pygame.event.pump()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_q]:
                return "quit"
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        configuring = False
                    elif event.key == pygame.K_l:
                        self.ble_paddles.LEFT = not self.ble_paddles.LEFT
                    elif event.key == pygame.K_r:
                        self.ble_paddles.RIGHT = not self.ble_paddles.RIGHT 
                    elif event.key == pygame.K_q:
                        return "quit"

            self.screen.blit(self.menu_bg, (0, 0))

            t1 = self.small_font.render("Left sensor is red.", True, (255, 255, 255))
            t2 = self.small_font.render("Right sensor is blue.", True, (255, 255, 255))
            self.screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, SCREEN_HEIGHT//3))
            self.screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, SCREEN_HEIGHT//3 + 40))

            left_ok  = bool(self.ble_paddles.LEFT)
            right_ok = bool(self.ble_paddles.RIGHT)
            self.start_enabled = bool(left_ok and right_ok)


            # Cyrcles: at the start they are greyish and after configuring they are red and blue
            pygame.draw.circle(self.screen, (200, 0, 0) if left_ok else (100, 100, 100),
                               (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2), 30)
            ltxt = self.small_font.render("Left (Red)", True, (255, 255, 255))
            self.screen.blit(ltxt, (SCREEN_WIDTH//2 - 170, SCREEN_HEIGHT//2 + 50))

            pygame.draw.circle(self.screen, (0, 0, 200) if right_ok else (100, 100, 100),
                               (SCREEN_WIDTH//2 + 120, SCREEN_HEIGHT//2), 30)
            rtxt = self.small_font.render("Right (Blue)", True, (255, 255, 255))
            self.screen.blit(rtxt, (SCREEN_WIDTH//2 + 60, SCREEN_HEIGHT//2 + 50))

            back = self.small_font.render("press ESC to go back to menu", True, (200, 200, 200))
            self.screen.blit(back, (SCREEN_WIDTH//2 - back.get_width()//2, SCREEN_HEIGHT - 80))

            pygame.display.flip()
            self.clock.tick(30)

    def run(self):
        menu_active = True
        while menu_active:
            pygame.event.pump()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_q]:
                pygame.mixer.music.stop()
                return "quit"

            self.screen.blit(self.menu_bg, (0, 0))
            self.draw_buttons()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.start_enabled:
                        menu_active = False  # returns "start"
                    elif event.key == pygame.K_q:
                        pygame.mixer.music.stop()
                        return "quit"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.buttons["start"].collidepoint(mouse_pos) and self.start_enabled:
                        menu_active = False
                    elif self.buttons["config"].collidepoint(mouse_pos):
                        res = self.configure_sensors()
                        if res == "quit":
                            pygame.mixer.music.stop()
                            return "quit"


            title_text = self.font.render("CANOE ROWING GAME", True, (255, 255, 255))
            if not self.start_enabled:
                instr = "Configure sensors"
            else:
                instr = "Press ENTER to Start or Q to Quit"
            instr_text = self.small_font.render(instr, True, (255, 255, 0))

            self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//3))
            self.screen.blit(instr_text, (SCREEN_WIDTH//2 - instr_text.get_width()//2, SCREEN_HEIGHT//3 + 60))

            pygame.display.flip()
            self.clock.tick(30)

        pygame.mixer.music.stop()
        return "start"
