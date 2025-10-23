# game/menu.py
import pygame, os

from game.input_schemes import BLEScheme, KeyboardScheme
from game.player import Player
from .settings import *
from .ble_message import Message

BASE_DIR = os.path.dirname(__file__)

class Menu:
    def __init__(self, ble_message: Message):
        self.ble_message = ble_message
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
        }

    def draw_buttons(self, buttons = None):
        if buttons == None:
            buttons = self.buttons

        for key, rect in buttons.items():
            color = (0, 150, 0)
            pygame.draw.rect(self.screen, color, rect)
            text = self.small_font.render(key.capitalize(), True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def configure_player(self):
        configuring = True
        selected_config = "NONE"
        player = None
        buttons = {
            "Paddles": pygame.Rect(SCREEN_WIDTH//4 - 100, 2*SCREEN_HEIGHT//3, 200, 50),
            "Keyboard": pygame.Rect(3*SCREEN_WIDTH//4 - 100, 2*SCREEN_HEIGHT//3, 200, 50),
        }
        selected_keys = []

        while configuring:
            pygame.event.pump()
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if buttons["Paddles"].collidepoint(mouse_pos):
                        selected_config = "PADDLES"
                    elif buttons["Keyboard"].collidepoint(mouse_pos):
                        selected_config = "KEYBOARD"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_k and selected_config == "NONE":
                        selected_config = "KEYBOARD"
                    elif event.key == pygame.K_p and selected_config == "NONE":
                        selected_config = "PADDLES"
                    elif event.key == pygame.K_RETURN and player != None:
                        return "start", player
                    elif event.key == pygame.K_q:
                        return "quit"
                    elif selected_config == "KEYBOARD":
                        selected_keys.append(event.key)

            self.screen.blit(self.menu_bg, (0, 0))

            match(selected_config):
                case("NONE"):
                    t0 = self.small_font.render("Choose how to play:", True, (255, 255, 255))
                    t1 = self.small_font.render("To play with paddles, press p.", True, (255, 255, 255))
                    t2 = self.small_font.render("To play with a keyboard, press k.", True, (255, 255, 255))
                    self.screen.blit(t0, (SCREEN_WIDTH//2 - t0.get_width()//2, SCREEN_HEIGHT//3 - 40))
                    self.screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, SCREEN_HEIGHT//3))
                    self.screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, SCREEN_HEIGHT//3 + 40))
                    self.draw_buttons(buttons)
                case("PADDLES"):
                    if player == None:
                        player = Player(BLEScheme(self.ble_message))
                    t0 = self.small_font.render("Row with the left paddle to activate the left circle", True, (255, 255, 255))
                    t1 = self.small_font.render("or row with the right paddle to activate the blue circle.", True, (255, 255, 255))
                    t2 = self.small_font.render("To continue, press ENTER.", True, (255, 255, 255))
                    self.screen.blit(t0, (SCREEN_WIDTH//2 - t0.get_width()//2, SCREEN_HEIGHT//3 - 40))
                    self.screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, SCREEN_HEIGHT//3))
                    self.screen.blit(t2, (SCREEN_WIDTH//2 - t2.get_width()//2, SCREEN_HEIGHT//3 + 40))
                    left_ok  = bool(self.ble_message.LEFT)
                    right_ok = bool(self.ble_message.RIGHT)


                    # Cyrcles: at the start they are greyish and after configuring they are red and blue
                    pygame.draw.circle(self.screen, (200, 0, 0) if left_ok else (100, 100, 100),
                                    (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2), 30)
                    ltxt = self.small_font.render("Left (Red)", True, (255, 255, 255))
                    self.screen.blit(ltxt, (SCREEN_WIDTH//2 - 170, SCREEN_HEIGHT//2 + 50))

                    pygame.draw.circle(self.screen, (0, 0, 200) if right_ok else (100, 100, 100),
                                    (SCREEN_WIDTH//2 + 120, SCREEN_HEIGHT//2), 30)
                    rtxt = self.small_font.render("Right (Blue)", True, (255, 255, 255))
                    self.screen.blit(rtxt, (SCREEN_WIDTH//2 + 60, SCREEN_HEIGHT//2 + 50))
                case("KEYBOARD"):
                    if len(selected_keys) == 0:
                        t1 = self.small_font.render("Press a key (except for q) to use as the left paddle.", True, (255, 255, 255))
                    elif len(selected_keys) == 1:
                        t1 = self.small_font.render("Press a key (except for q) to use as the right paddle.", True, (255, 255, 255))
                    else:
                        if (player == None):
                            player = Player(KeyboardScheme(selected_keys[0], selected_keys[1]))
                        t1 = self.small_font.render("To continue, press ENTER.", True, (255, 255, 255))
                    self.screen.blit(t1, (SCREEN_WIDTH//2 - t1.get_width()//2, SCREEN_HEIGHT//3))

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
                    if event.key == pygame.K_RETURN:
                        menu_active = False 
                    elif event.key == pygame.K_q:
                        pygame.mixer.music.stop()
                        return "quit"
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.buttons["start"].collidepoint(mouse_pos):
                        menu_active = False


            title_text = self.font.render("CANOE ROWING GAME", True, (255, 255, 255))
            instr = "Press ENTER to Start or Q to Quit"
            instr_text = self.small_font.render(instr, True, (255, 255, 0))

            self.screen.blit(title_text, (SCREEN_WIDTH//2 - title_text.get_width()//2, SCREEN_HEIGHT//3))
            self.screen.blit(instr_text, (SCREEN_WIDTH//2 - instr_text.get_width()//2, SCREEN_HEIGHT//3 + 60))

            pygame.display.flip()
            self.clock.tick(30)

        res, player = self.configure_player()
        pygame.mixer.music.stop()
        return res, player
