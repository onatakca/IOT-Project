# menu.py — bigger title + spacing; menu music follows Music Volume and stops when leaving
import pygame, os
from .settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, UI_BG, BTN_BG, BTN_OUT,
    UserSettings, load_settings, save_settings, IMAGES_DIR, SOUNDS_DIR
)

class Menu:
    def __init__(self, start_mode: str = "menu"):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Canoe Game — Menu")
        self.clock = pygame.time.Clock()

        # Fonts
        try:
            self.title_font = pygame.font.SysFont("Impact", 120)
        except:
            self.title_font = pygame.font.SysFont(None, 120)
        self.font  = pygame.font.SysFont("Bahnschrift", 28) if pygame.font.get_init() else pygame.font.SysFont(None, 28)
        self.small = pygame.font.SysFont("Bahnschrift", 22) if pygame.font.get_init() else pygame.font.SysFont(None, 22)

        # Background
        self.bg = None
        bg_path = os.path.join(IMAGES_DIR, "menu.png")
        if os.path.exists(bg_path):
            self.bg = pygame.image.load(bg_path).convert()
            self.bg = pygame.transform.smoothscale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

        self.settings = load_settings()
        self.mode = "settings" if start_mode == "settings" else "menu"

        # Menu music
        try:
            pygame.mixer.init()
            self.menu_music_path = os.path.join(SOUNDS_DIR, "menu.mp3")
            if os.path.exists(self.menu_music_path):
                pygame.mixer.music.load(self.menu_music_path)
                pygame.mixer.music.setVolume = pygame.mixer.music.set_volume
                pygame.mixer.music.setVolume(self.settings.music_vol / 100)
                pygame.mixer.music.play(-1)
        except Exception:
            pass

        # Buttons
        cx = SCREEN_WIDTH//2 - 160
        self.btn_start    = (pygame.Rect(cx, 360, 320, 62), "Start")
        self.btn_settings = (pygame.Rect(cx, 435, 320, 62), "Settings")
        self.btn_quit     = (pygame.Rect(cx, 510, 320, 62), "Quit")
        self.btn_back     = (pygame.Rect(cx, 540, 320, 58), "Save & Back")

        # Sliders with added spacing
        self.music_rect = pygame.Rect(SCREEN_WIDTH//2-220, 180, 440, 24)
        self.sfx_rect   = pygame.Rect(SCREEN_WIDTH//2-220, 240, 440, 24)  # +60px gap

        self.players_minus = pygame.Rect(SCREEN_WIDTH//2-240, 290, 44, 44)
        self.players_plus  = pygame.Rect(SCREEN_WIDTH//2+196, 290, 44, 44)

        self.diff_left     = pygame.Rect(SCREEN_WIDTH//2-240, 340, 44, 44)
        self.diff_right    = pygame.Rect(SCREEN_WIDTH//2+196, 340, 44, 44)

        # Names section lower (more space after difficulty); no "(optional)"
        start_names_y = 420
        self.name_rects = [pygame.Rect(SCREEN_WIDTH//2-220, start_names_y + i*36, 440, 28) for i in range(3)]
        self.active_name = -1

    def _draw_btn(self, btn):
        rect, text = btn
        pygame.draw.rect(self.screen, BTN_BG, rect, border_radius=14)
        pygame.draw.rect(self.screen, BTN_OUT, rect, 2, border_radius=14)
        label = self.font.render(text, True, (25,25,25))
        self.screen.blit(label, label.get_rect(center=rect.center))

    def _draw_slider(self, rect, value, label):
        pygame.draw.rect(self.screen, BTN_OUT, rect, 2, border_radius=8)
        filled = pygame.Rect(rect.x, rect.y, rect.w * (value / 100), rect.h)
        pygame.draw.rect(self.screen, (40,140,255), filled, border_radius=8)
        txt = self.small.render(f"{label}: {int(value)}%", True, (255,255,255))
        self.screen.blit(txt, (rect.x, rect.y - 22))

    def _stop_menu_music(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self._stop_menu_music()
                    return None

                if self.mode == "menu" and e.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_start[0].collidepoint(e.pos):
                        self._stop_menu_music()
                        return self.settings
                    if self.btn_settings[0].collidepoint(e.pos):
                        self.mode = "settings"
                    if self.btn_quit[0].collidepoint(e.pos):
                        self._stop_menu_music()
                        return None

                elif self.mode == "settings":
                    mx, my = pygame.mouse.get_pos()
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        self.active_name = -1
                        if self.music_rect.collidepoint((mx,my)):
                            self.settings.music_vol = max(0, min(100, int(((mx - self.music_rect.x)/self.music_rect.w)*100)))
                            try:
                                pygame.mixer.music.set_volume(self.settings.music_vol / 100)
                            except Exception:
                                pass
                        elif self.sfx_rect.collidepoint((mx,my)):
                            self.settings.sfx_vol = max(0, min(100, int(((mx - self.sfx_rect.x)/self.sfx_rect.w)*100)))
                        elif self.players_minus.collidepoint((mx,my)):
                            self.settings.players = max(1, self.settings.players-1)
                        elif self.players_plus.collidepoint((mx,my)):
                            self.settings.players = min(3, self.settings.players+1)
                        elif self.diff_left.collidepoint((mx,my)) or self.diff_right.collidepoint((mx,my)):
                            order = ["easy","normal","hard"]
                            i = order.index(self.settings.difficulty)
                            i = (i + (1 if self.diff_right.collidepoint((mx,my)) else -1)) % len(order)
                            self.settings.difficulty = order[i]
                        elif self.btn_back[0].collidepoint(e.pos):
                            save_settings(self.settings)
                            self.mode = "menu"
                        else:
                            for i in range(self.settings.players):
                                if self.name_rects[i].collidepoint((mx,my)):
                                    self.active_name = i
                                    break
                    elif e.type == pygame.KEYDOWN and self.active_name != -1:
                        if e.key == pygame.K_BACKSPACE:
                            self.settings.player_names[self.active_name] = self.settings.player_names[self.active_name][:-1]
                        elif e.key == pygame.K_RETURN:
                            self.active_name = -1
                        else:
                            ch = e.unicode
                            if ch and ch.isprintable():
                                self.settings.player_names[self.active_name] += ch

            # Draw
            if self.bg: self.screen.blit(self.bg, (0,0))
            else:       self.screen.fill(UI_BG)

            if self.mode == "menu":
                title = self.title_font.render("Canoe Game", True, (255,255,255))
                shadow = self.title_font.render("Canoe Game", True, (0,0,0))
                self.screen.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH//2+3, 120+3)))
                self.screen.blit(title,  title.get_rect(center=(SCREEN_WIDTH//2,   120)))
                for b in (self.btn_start, self.btn_settings, self.btn_quit):
                    self._draw_btn(b)
            else:
                title = self.title_font.render("Settings", True, (255,255,255))
                self.screen.blit(title, title.get_rect(center=(SCREEN_WIDTH//2, 90)))

                self._draw_slider(self.music_rect, self.settings.music_vol, "Music Volume")
                self._draw_slider(self.sfx_rect,   self.settings.sfx_vol,   "SFX Volume")

                # Players & Difficulty
                for r in (self.players_minus, self.players_plus, self.diff_left, self.diff_right):
                    pygame.draw.rect(self.screen, BTN_BG, r, border_radius=10)
                    pygame.draw.rect(self.screen, BTN_OUT, r, 2, border_radius=10)
                self.screen.blit(self.font.render("-", True, (25,25,25)), self.players_minus.move(12,5))
                self.screen.blit(self.font.render("+", True, (25,25,25)), self.players_plus.move(12,5))
                self.screen.blit(self.font.render("<", True, (25,25,25)), self.diff_left.move(12,5))
                self.screen.blit(self.font.render(">", True, (25,25,25)), self.diff_right.move(12,5))

                ptxt = self.font.render(f"Players: {self.settings.players}", True, (255,255,255))
                self.screen.blit(ptxt, ptxt.get_rect(center=(SCREEN_WIDTH//2, 314)))

                dtxt = self.font.render(f"Difficulty: {self.settings.difficulty.upper()}", True, (255,255,255))
                self.screen.blit(dtxt, dtxt.get_rect(center=(SCREEN_WIDTH//2, 364)))

                self.screen.blit(self.font.render("Player Names:", True, (255,255,255)),
                                 (SCREEN_WIDTH//2-220, 392))
                for i in range(self.settings.players):
                    r = self.name_rects[i]
                    pygame.draw.rect(self.screen, (230,230,230), r, border_radius=8)
                    pygame.draw.rect(self.screen, BTN_OUT, r, 2, border_radius=8)
                    name = self.settings.player_names[i].strip() or f"Player {i+1}"
                    self.screen.blit(self.small.render(name, True, (25,25,25)), (r.x+8, r.y+4))

                self._draw_btn(self.btn_back)

            pygame.display.flip()
            self.clock.tick(60)
