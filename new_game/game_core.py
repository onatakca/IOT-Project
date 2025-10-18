# game_core.py — sound hookup + polished HUD/results
# - River "splash" music plays ONLY during rounds (loop); follows Music Volume
# - game_start plays once at round start (SFX volume)
# - point.mp3 plays each time you pass an obstacle (SFX volume)
# - game_over.mp3 plays when the round ends (SFX volume)
# - Menu music remains in menu.py and also follows Music Volume
# - HUD: name is now INSIDE the light gray button-style score box (name smaller than score)
# - Results: names & points use the same clean font (Bahnschrift); spacing/margins adjusted
# - Keeps vertical split, obstacle scaling, crocodile pattern, keycaps low, wrapped text

import pygame, random, os
from .settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS,
    BASE_SPAWN_INTERVAL, BASE_OBSTACLE_SPEED, difficulty_factors,
    UserSettings, CANOE_WIDTH, CANOE_HEIGHT, IMAGES_DIR, SOUNDS_DIR, BTN_BG, BTN_OUT
)
from .river import River
from .canoe import Canoe
from .obstacle import Obstacle
from .menu import Menu

UPSTREAM_SPEED   = 3.0
DOWNSTREAM_DRIFT = 1.6

PALETTE = {
    "overlay":     (0, 0, 0, 200),
    "split_border":(25, 25, 25),
    "body":        (230, 245, 255),
    "title":       (255, 255, 120),
    "keycap_bg":   (30, 40, 90),
    "keycap_fg":   (255, 255, 255),
    "shadow":      (0, 0, 0, 120),
}

PLAYER_KEYS = [
    {"left": pygame.K_LEFT,  "right": pygame.K_RIGHT, "both": pygame.K_UP},
    {"left": pygame.K_a,     "right": pygame.K_d,     "both": pygame.K_w},
    {"left": pygame.K_j,     "right": pygame.K_l,     "both": pygame.K_i},
]

def quip_named(score: int, name: str) -> str:
    name = (name or "Player")
    if score == 0:            return f"Oops… looks like someone is drowning, {name}!"
    if 1  <= score <= 4:      return f"Okay {name}, I’ll need you to row harder."
    if 5  <= score <= 10:     return f"Not bad {name}—keep the rhythm!"
    if 11 <= score <= 20:     return f"You’re finding the current, {name}!"
    if 21 <= score <= 30:     return f"Nice flow {name}—stay sharp!"
    if 31 <= score <= 40:     return f"Strong paddling {name}! Nearly pro!"
    if 41 <= score <= 50:     return f"Elite rowing {name}—stone-cold!"
    return f"Legendary. You're a river tamer, {name}!"

def draw_keycap(surface, text, x, y, font):
    cap = pygame.Rect(0, 0, 36, 36); cap.center = (x, y)
    sh = pygame.Surface((cap.w+6, cap.h+6), pygame.SRCALPHA)
    sh.fill(PALETTE["shadow"]); surface.blit(sh, (cap.x+2, cap.y+2))
    pygame.draw.rect(surface, PALETTE["keycap_bg"], cap, border_radius=8)
    pygame.draw.rect(surface, (255,255,255,50), cap, 2, border_radius=8)
    lbl = font.render(text, True, PALETTE["keycap_fg"])
    surface.blit(lbl, lbl.get_rect(center=cap.center))

def wrap_lines(font, text, max_width):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = (line + " " + w) if line else w
        if font.size(test)[0] <= max_width:
            line = test
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return lines

# ----------------- World -----------------
class World:
    def __init__(self, vw, vh, obstacle_scale=1.0):
        self.vw, self.vh = vw, vh
        self.river = River(vw, vh, IMAGES_DIR)

        # Boat
        self.canoe_img = None
        boat_path = os.path.join(IMAGES_DIR, "boat.png")
        if os.path.exists(boat_path):
            self.canoe_img = pygame.transform.scale(
                pygame.image.load(boat_path).convert_alpha(),
                (CANOE_WIDTH, CANOE_HEIGHT)
            )

        # Obstacle scaling
        self.ob_scale = max(0.25, float(obstacle_scale))
        base_w, base_h = 80, 80
        self.ob_w = max(24, int(base_w * self.ob_scale))
        self.ob_h = max(24, int(base_h * self.ob_scale))

        # Rock & Croc
        self.rock_img = None
        rp = os.path.join(IMAGES_DIR, "rock.png")
        if os.path.exists(rp):
            self.rock_img = pygame.transform.smoothscale(
                pygame.image.load(rp).convert_alpha(), (self.ob_w, self.ob_h)
            )
        self.croc_img = None
        cp = os.path.join(IMAGES_DIR, "crocodile.png")
        if os.path.exists(cp):
            self.croc_img = pygame.transform.smoothscale(
                pygame.image.load(cp).convert_alpha(), (self.ob_w, self.ob_h)
            )

        self.spawn_count = 0
        self.reset()

    def reset(self):
        self.canoe = Canoe(self.vw//2 - CANOE_WIDTH//2, self.vh//2, self.canoe_img)
        self.obstacles = []
        self.spawn_timer = 0.0
        self.points = 0
        self.game_over = False

    def spawn_obstacle(self):
        left, right = self.river.bounds_at(0)
        m = 20
        left += m; right -= (m + self.ob_w)
        if right > left:
            x = random.randint(int(left), int(right))
            self.spawn_count += 1
            use_croc = (self.spawn_count % 3 == 0) and (self.croc_img is not None)
            img = self.croc_img if use_croc else self.rock_img
            self.obstacles.append(Obstacle(x, -self.ob_h, img, size=(self.ob_w, self.ob_h)))

    def update(self, paddling, left_active, right_active, spawn_interval, obst_speed):
        if self.game_over: return
        # inverted turning
        if paddling == "LEFT":   self.canoe.move("RIGHT")
        elif paddling == "RIGHT":self.canoe.move("LEFT")

        if left_active or right_active:
            self.canoe.y -= UPSTREAM_SPEED
            if self.canoe.y < self.vh//2: self.canoe.y = self.vh//2
            self.river.update(-UPSTREAM_SPEED)
        else:
            self.canoe.y += DOWNSTREAM_DRIFT
            self.river.update(+DOWNSTREAM_DRIFT)

        if self.canoe.y + self.canoe.height >= self.vh:
            self.game_over = True

        self.spawn_timer -= 1/FPS
        if self.spawn_timer <= 0:
            self.spawn_obstacle()
            self.spawn_timer = spawn_interval

        for o in self.obstacles[:]:
            o.update(obst_speed)
            if not o.counted and o.y > self.canoe.y + self.canoe.height:
                self.points += 1; o.counted = True
            if o.offscreen(self.vh):
                self.obstacles.remove(o)

        c = self.canoe.get_collision_rect()
        for o in self.obstacles:
            if c.colliderect(o.get_rect()):
                self.game_over = True; break
        if self.river.hits_bank(c):
            self.game_over = True

    def draw_hud(self, surf, name, name_font_small, score_font_big):
        # Score box styled like menu buttons (light gray + dark outline)
        box = pygame.Rect(10, 10, 240, 80)
        pygame.draw.rect(surf, BTN_BG,  box, border_radius=14)
        pygame.draw.rect(surf, BTN_OUT, box, 2, border_radius=14)

        # Name (smaller) at top of the box
        name_surface = name_font_small.render(name, True, (25,25,25))
        surf.blit(name_surface, name_surface.get_rect(center=(box.centerx, box.y + 22)))

        # Score (bigger) centered lower in the box
        score_surface = score_font_big.render(str(self.points), True, (25,25,25))
        surf.blit(score_surface, score_surface.get_rect(center=(box.centerx, box.y + 55)))

    def draw(self, surf, name: str, name_font_small, score_font_big):
        self.river.draw(surf)
        self.canoe.draw(surf)
        for o in self.obstacles: o.draw(surf)
        self.draw_hud(surf, name, name_font_small, score_font_big)

# ----------------- Game (with simple sound manager) -----------------
class Game:
    def __init__(self, settings: UserSettings):
        self.settings = settings
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Canoe Game")
        self.clock = pygame.time.Clock()

        # Fonts
        try:
            self.title_font = pygame.font.SysFont("Impact", 74)
        except:
            self.title_font = pygame.font.SysFont(None, 74)
        try:
            self.body_font  = pygame.font.SysFont("Bahnschrift", 36)
            self.small_font = pygame.font.SysFont("Bahnschrift", 26)
            self.key_font   = pygame.font.SysFont("Bahnschrift", 26)
            # HUD: names slightly smaller than score; both clean
            self.hud_name_font  = pygame.font.SysFont("Bahnschrift", 26, bold=True)
        except:
            self.body_font  = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 26)
            self.key_font   = pygame.font.SysFont(None, 26)
            self.hud_name_font  = pygame.font.SysFont(None, 26, bold=True)
        # Old clean font for score number (bigger)
        self.hud_score_font = pygame.font.SysFont(None, 36)

        # Scoreboard at end (same family for names & points)
        try:
            self.scoreboard_font = pygame.font.SysFont("Bahnschrift", 34)
        except:
            self.scoreboard_font = pygame.font.SysFont(None, 34)

        # Sound system
        self._init_audio()

        self._apply_settings(rebuild=True)
        self.round_over = False
        self.results_cached = None

    # ---------- Audio ----------
    def _init_audio(self):
        try:
            pygame.mixer.init()
        except Exception:
            return
        # Preload SFX
        def load_mp3(name):
            p = os.path.join(SOUNDS_DIR, name)
            return pygame.mixer.Sound(p) if os.path.exists(p) else None

        self.sfx_start  = load_mp3("game_start.mp3")
        self.sfx_point  = load_mp3("point.mp3")
        self.sfx_over   = load_mp3("game_over.mp3")
        # River loop uses mixer.music (so it can stream/loop cleanly)
        self.river_music_path = os.path.join(SOUNDS_DIR, "river_splashy.mp3")

        # Apply initial volumes
        self._apply_volume()

    def _apply_volume(self):
        # Music volume will be applied when starting/stopping river loop
        vol_sfx = (self.settings.sfx_vol or 0)/100
        for s in (self.sfx_start, self.sfx_point, self.sfx_over):
            if s: s.set_volume(vol_sfx)

    def _start_round_audio(self):
        # Play start "ding" once (SFX)
        if self.sfx_start:
            self.sfx_start.set_volume((self.settings.sfx_vol or 0)/100)
            self.sfx_start.play()

        # Start river loop as "music"
        if os.path.exists(self.river_music_path):
            try:
                pygame.mixer.music.load(self.river_music_path)
                pygame.mixer.music.set_volume((self.settings.music_vol or 0)/100)
                pygame.mixer.music.play(-1)
            except Exception:
                pass

    def _stop_round_music(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    # ---------- Settings → gameplay ----------
    def _apply_settings(self, rebuild: bool):
        # volumes might have changed
        self._apply_volume()

        spf, spdf = difficulty_factors(self.settings.difficulty)
        self.spawn_interval = BASE_SPAWN_INTERVAL * spf
        self.ob_speed       = BASE_OBSTACLE_SPEED * spdf

        n = max(1, min(3, self.settings.players))
        self.players = n
        self.viewports = self._make_viewports(n)

        scale = 1.0 if n == 1 else (0.5 if n == 2 else (1.0/3.0))
        self.worlds = [World(w, h, obstacle_scale=scale) for (_,_,w,h) in self.viewports]

        self.round_over = False
        self.results_cached = None
        # Start round audio fresh
        self._start_round_audio()

    def _make_viewports(self, n):
        if n == 1:
            return [(0,0,SCREEN_WIDTH,SCREEN_HEIGHT)]
        if n == 2:
            w = SCREEN_WIDTH // 2
            return [(0,0,w,SCREEN_HEIGHT), (w,0,SCREEN_WIDTH-w,SCREEN_HEIGHT)]
        w = SCREEN_WIDTH // 3
        return [(0,0,w,SCREEN_HEIGHT), (w,0,w,SCREEN_HEIGHT), (2*w,0,SCREEN_WIDTH-2*w,SCREEN_HEIGHT)]

    def _read_controls(self, idx):
        k = pygame.key.get_pressed()
        m = PLAYER_KEYS[idx]
        left, right, both = k[m["left"]], k[m["right"]], k[m["both"]]
        if both: return "STRAIGHT", True, True
        if left and not right:  return "LEFT", True, False
        if right and not left:  return "RIGHT", False, True
        return "STOP", False, False

    def _open_settings(self):
        # Stop round music while inside settings? (keep playing)
        menu = Menu(start_mode="settings")
        s = menu.run()
        if s is not None:
            self.settings = s
            self._apply_settings(rebuild=True)

    def _default_name(self, idx):
        if hasattr(self.settings, "player_names"):
            nm = (self.settings.player_names[idx] if idx < len(self.settings.player_names) else "").strip()
            return nm if nm else f"Player {idx+1}"
        return f"Player {idx+1}"

    def _compute_results(self):
        scores = [w.points for w in self.worlds]
        names  = [self._default_name(i) for i in range(self.players)]
        max_score = max(scores) if scores else 0
        winners = [names[i] for i,s in enumerate(scores) if s == max_score]
        headline_name = winners[0] if len(winners) == 1 else "champions"
        title = quip_named(max_score, headline_name)
        subtitle = None
        lines = [f"{names[i]} — {scores[i]} pts" for i in range(self.players)]
        return title, subtitle, lines

    def _handle_point_sfx(self):
        # play point sound (SFX volume)
        if self.sfx_point:
            self.sfx_point.set_volume((self.settings.sfx_vol or 0)/100)
            self.sfx_point.play()

    def _handle_game_over_sfx(self):
        # stop river loop
        self._stop_round_music()
        # play game_over one-shot (SFX volume)
        if self.sfx_over:
            self.sfx_over.set_volume((self.settings.sfx_vol or 0)/100)
            self.sfx_over.play()

    def run(self):
        running = True
        while running:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_q: running = False
                    elif e.key == pygame.K_r:
                        for w in self.worlds: w.reset()
                        self.round_over = False; self.results_cached = None
                        # restart round audio fresh
                        self._start_round_audio()
                    elif e.key == pygame.K_s:
                        self._open_settings()

            if not self.round_over:
                for i, world in enumerate(self.worlds):
                    direction, lp, rp = self._read_controls(i)
                    # Before update, capture score to detect passage
                    prev_points = world.points
                    world.update(direction, lp, rp, self.spawn_interval, self.ob_speed)
                    if world.points > prev_points:
                        self._handle_point_sfx()

                if all(w.game_over for w in self.worlds):
                    self.round_over = True
                    self._handle_game_over_sfx()
                    if self.players == 1:
                        name  = self._default_name(0)
                        score = self.worlds[0].points
                        title = quip_named(score, name)
                        subtitle = None
                        lines = [f"{name} — {score} pts"]
                        self.results_cached = (title, subtitle, lines)
                    else:
                        self.results_cached = self._compute_results()

            # Draw panes
            self.screen.fill((0,0,0))
            for i,(x,y,w,h) in enumerate(self.viewports):
                pane = pygame.Surface((w,h)).convert_alpha()
                self.worlds[i].draw(pane, self._default_name(i), self.hud_name_font, self.hud_score_font)
                if self.worlds[i].game_over and not self.round_over:
                    ov = pygame.Surface((w,h), pygame.SRCALPHA); ov.fill((0,0,0,140))
                    pane.blit(ov, (0,0))
                    t = self.small_font.render("Waiting for others...", True, (255,220,220))
                    pane.blit(t, (w//2 - t.get_width()//2, h//2))
                self.screen.blit(pane, (x,y))
                pygame.draw.rect(self.screen, PALETTE["split_border"], (x,y,w,h), 2)

            # Results overlay
            if self.round_over and self.results_cached:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill(PALETTE["overlay"])
                self.screen.blit(overlay, (0,0))

                title, subtitle, lines = self.results_cached
                left_margin, right_margin = 60, 60
                maxw = SCREEN_WIDTH - left_margin - right_margin

                # Headline (wrapped)
                y = 120
                for hl in wrap_lines(self.title_font, title, maxw):
                    surf = self.title_font.render(hl, True, PALETTE["title"])
                    self.screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH//2, y)))
                    y += 64
                y += 12

                # Subtitle (if any)
                if subtitle:
                    for line in wrap_lines(self.body_font, subtitle, maxw):
                        s = self.body_font.render(line, True, PALETTE["body"])
                        self.screen.blit(s, s.get_rect(center=(SCREEN_WIDTH//2, y)))
                        y += 42
                    y += 10

                # Scoreboard: one clean font (Bahnschrift)
                for line in lines:
                    t = self.scoreboard_font.render(line, True, (255,255,255))
                    self.screen.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, y)))
                    y += 44

                # Keycaps near bottom
                key_y = SCREEN_HEIGHT - 64
                kx = SCREEN_WIDTH//2
                draw_keycap(self.screen, "R", kx-72, key_y, self.key_font)
                draw_keycap(self.screen, "S", kx,    key_y, self.key_font)
                draw_keycap(self.screen, "Q", kx+72, key_y, self.key_font)
                label = self.small_font.render("Restart         Settings         Quit", True, PALETTE["body"])
                self.screen.blit(label, label.get_rect(center=(kx, key_y+30)))

            pygame.display.flip()
            self.clock.tick(FPS)
        # ensure music stops when quitting game
        self._stop_round_music()
        pygame.quit()
