import pygame
import random
import os

from game.player import Player
from .settings import *
from .river import River
from .canoe import Canoe
from .obstacle import Obstacle
from .paddle_indicator import PaddleIndicator
from .qte import QTEManager, QTEResult, QTEType

BASE_DIR = os.path.dirname(__file__)

# Palette for end game messages
PALETTE = {
    "overlay":     (0, 0, 0, 200),
    "body":        (230, 245, 255),
    "title":       (255, 255, 120),
    "keycap_bg":   (30, 40, 90),
    "keycap_fg":   (255, 255, 255),
    "shadow":      (0, 0, 0, 120),
}

def quip_named(score: int, name: str) -> str:
    name = (name or "Player")
    if score == 0:            return f"Oops… looks like someone is drowning, {name}!"
    if 1  <= score <= 4:      return f"Okay {name}, I'll need you to row harder."
    if 5  <= score <= 10:     return f"Not bad {name}—keep the rhythm!"
    if 11 <= score <= 20:     return f"You're finding the current, {name}!"
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

class Game:
    def __init__(self, player: Player, settings: UserSettings = None):
        self.player = player
        self.settings = settings if settings is not None else UserSettings()

        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Canoe Game - IoT Demo")
        self.clock = pygame.time.Clock()

        # Fonts for end game messages
        try:
            self.title_font = pygame.font.SysFont("Impact", 74)
            self.body_font  = pygame.font.SysFont("Bahnschrift", 36)
            self.small_font = pygame.font.SysFont("Bahnschrift", 26)
            self.key_font   = pygame.font.SysFont("Bahnschrift", 26)
        except:
            self.title_font = pygame.font.SysFont(None, 74)
            self.body_font  = pygame.font.SysFont(None, 36)
            self.small_font = pygame.font.SysFont(None, 26)
            self.key_font   = pygame.font.SysFont(None, 26)

        # Load images and scale to game sizes
        self.boat_img = pygame.image.load(os.path.join(BASE_DIR, 'images', 'boat.png')).convert_alpha()
        self.rock_img = pygame.image.load(os.path.join(BASE_DIR,'images','rock.png')).convert_alpha()
        self.croc_img = pygame.image.load(os.path.join(BASE_DIR,'images','croc.png')).convert_alpha()

        # Scale to original game dimensions
        self.boat_img = pygame.transform.scale(self.boat_img, (CANOE_WIDTH, CANOE_HEIGHT))
        self.rock_img = pygame.transform.scale(self.rock_img, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))
        self.croc_img = pygame.transform.scale(self.croc_img, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))

        # Load sound effects
        pygame.mixer.init()
        self.sound_game_start = pygame.mixer.Sound(os.path.join(BASE_DIR,'sounds','game_start.mp3'))
        self.sound_game_over = pygame.mixer.Sound(os.path.join(BASE_DIR,'sounds','game_over.mp3'))
        self.sound_point = pygame.mixer.Sound(os.path.join(BASE_DIR,'sounds','point.mp3'))

        # Apply volume settings
        sfx_vol = self.settings.sfx_vol / 100
        self.sound_game_start.set_volume(sfx_vol)
        self.sound_game_over.set_volume(sfx_vol)
        self.sound_point.set_volume(sfx_vol)

        # Load background music
        pygame.mixer.music.load(os.path.join(BASE_DIR,'sounds','river_splashy.mp3'))
        pygame.mixer.music.set_volume(self.settings.music_vol / 100)

        # Apply difficulty settings
        spf, spdf = difficulty_factors(self.settings.difficulty)
        self.spawn_interval = BASE_SPAWN_INTERVAL * spf * 1000  # Convert to milliseconds
        self.obstacle_speed = BASE_OBSTACLE_SPEED * spdf

        self.reset_game()

        # Paddle indicators (moved to bottom of screen)
        self.left_indicator = PaddleIndicator(50, SCREEN_HEIGHT - 100, "LEFT")
        self.right_indicator = PaddleIndicator(SCREEN_WIDTH - 130, SCREEN_HEIGHT - 100, "RIGHT")

        # Player name
        self.player_name = self.settings.player_names[0].strip() if self.settings.player_names[0].strip() else "Player 1"

        # Video mode disabled - using clean programmatic rendering
        self.video_mode = False

    def reset_game(self):
        self.river = River()
        self.canoe = Canoe(SCREEN_WIDTH // 2 - CANOE_WIDTH // 2,
                          SCREEN_HEIGHT - 200,  # Fixed position near bottom
                          self.boat_img)
        self.obstacles = []
        self.game_over = False
        self.game_won = False
        self.last_spawn_time = pygame.time.get_ticks()

        self.player.score = 0

        # QTE system
        self.qte_manager = QTEManager(difficulty=self.settings.difficulty)
        self.last_qte_result = None
        self.qte_feedback_time = 0
        self.combo_count = 0  # Track successful QTEs in a row
        self.health = 3  # Player has 3 lives

        # Track QTE-obstacle pairs
        self.qte_obstacles = {}  # Maps QTE to its corresponding obstacle

        # Auto-scroll speed (constant forward movement)
        self.auto_scroll_speed = 2.0  # pixels per frame

        # Canoe lanes (left, center, right)
        # All lanes stay well within river bounds (river: 200px to 600px)
        self.canoe_lane = 1  # 0=left, 1=center, 2=right
        self.target_lane = 1  # Lane we're animating toward
        center_x = SCREEN_WIDTH // 2
        # Calculate lane spacing to fill the river width (500px / 3 lanes)
        # River bounds: center - 250 to center + 250
        # Position lanes to maximize width usage, placing obstacles right at banks
        lane_spacing = 145  # Maximum spacing to fill river width
        self.lane_positions = [
            center_x - lane_spacing - CANOE_WIDTH // 2,  # Left lane: ~228px (near left bank)
            center_x - CANOE_WIDTH // 2,                 # Center lane: ~373px
            center_x + lane_spacing - CANOE_WIDTH // 2,  # Right lane: ~518px (near right bank)
        ]

        # Lane switching animation
        self.lane_switch_speed = 8.0  # Pixels per frame
        self.should_recenter = False  # Whether to auto-recenter after dodge
        self.dodge_obstacles = []  # Obstacles we're currently dodging

        # Damage flash effect
        self.damage_flash_time = 0
        self.damage_flash_duration = 300  # milliseconds

        # Jump animation for BOTH QTE
        self.is_jumping = False
        self.jump_start_time = 0
        self.jump_duration = 1300  # milliseconds
        self.jump_height = 50  # pixels
        self.jump_particles = []  # List of particles for jump effect
        self.should_jump = False  # Flag to trigger jump when close to obstacles
        self.jump_obstacles = []  # Obstacles to jump over

        # Start in center lane
        self.canoe.x = self.lane_positions[1]

        # Play game start sound and start background music
        self.sound_game_start.play()
        pygame.mixer.music.set_volume(0.75)  # Set volume to 75% (25% reduction)
        pygame.mixer.music.play(-1)  # Loop background music indefinitely
        
    def spawn_obstacle_for_qte(self, qte):
        """
        Spawn obstacles with visual clarity (mix of rocks and crocs).

        Lanes: 1 (left), 2 (center/middle), 3 (right)
        - Row LEFT: Fill lanes 1&2 (left+middle) with obstacles → only RIGHT lane empty
        - Row RIGHT: Fill lanes 2&3 (middle+right) with obstacles → only LEFT lane empty
        - Row BOTH: Fill ALL 3 lanes → boat must JUMP over middle
        """
        spawn_y = -OBSTACLE_HEIGHT - 100  # Spawn closer for tighter timing (obstacles arrive faster)

        # Helper to get random obstacle image (mix of rock and croc)
        def random_obstacle_img():
            return random.choice([self.rock_img, self.croc_img])

        if qte.qte_type == QTEType.LEFT:
            # Row LEFT → boat moves RIGHT → only lane 3 (right) is safe
            # Fill lanes 1 (left) and 2 (middle) with obstacles
            obs1 = Obstacle(self.lane_positions[0], spawn_y, random_obstacle_img())  # Lane 1 (left)
            obs2 = Obstacle(self.lane_positions[1], spawn_y, random_obstacle_img())  # Lane 2 (middle)
            self.obstacles.append(obs1)
            self.obstacles.append(obs2)
            self.qte_obstacles[id(qte)] = [obs1, obs2]

        elif qte.qte_type == QTEType.RIGHT:
            # Row RIGHT → boat moves LEFT → only lane 1 (left) is safe
            # Fill lanes 2 (middle) and 3 (right) with obstacles
            obs1 = Obstacle(self.lane_positions[1], spawn_y, random_obstacle_img())  # Lane 2 (middle)
            obs2 = Obstacle(self.lane_positions[2], spawn_y, random_obstacle_img())  # Lane 3 (right)
            self.obstacles.append(obs1)
            self.obstacles.append(obs2)
            self.qte_obstacles[id(qte)] = [obs1, obs2]

        elif qte.qte_type == QTEType.BOTH:
            # Row BOTH → boat JUMPS → all lanes full
            obs1 = Obstacle(self.lane_positions[0], spawn_y, random_obstacle_img())  # Lane 1 (left)
            obs2 = Obstacle(self.lane_positions[1], spawn_y, random_obstacle_img())  # Lane 2 (middle)
            obs3 = Obstacle(self.lane_positions[2], spawn_y, random_obstacle_img())  # Lane 3 (right)
            self.obstacles.append(obs1)
            self.obstacles.append(obs2)
            self.obstacles.append(obs3)
            self.qte_obstacles[id(qte)] = [obs1, obs2, obs3]
        
    def check_collision(self):
        """
        Check if canoe collides with obstacles.
        Only collides if obstacle is in the same lane as the canoe.
        """
        canoe_rect = self.canoe.get_collision_rect()

        for obstacle in self.obstacles:
            obstacle_rect = obstacle.get_rect()

            # Only check collision if obstacle is in same lane as canoe
            # Determine which lane the obstacle is in
            obstacle_lane = None
            for lane_idx, lane_x in enumerate(self.lane_positions):
                # Check if obstacle X position is close to this lane
                if abs(obstacle.x - lane_x) < 50:  # Tolerance of 50 pixels
                    obstacle_lane = lane_idx
                    break

            # If obstacle is in same lane as canoe, check collision
            if obstacle_lane == self.canoe_lane:
                if canoe_rect.colliderect(obstacle_rect):
                    return True

        return False
    
    def update(self, direction, left_paddle, right_paddle):
        if self.game_over or self.game_won:
            return

        current_time = pygame.time.get_ticks()

        # Update paddle indicators
        self.left_indicator.set_active(left_paddle)
        self.right_indicator.set_active(right_paddle)

        # Get canoe Y position (used throughout update)
        canoe_y = self.canoe.y

        # Smooth lane switching animation
        target_x = self.lane_positions[self.target_lane]
        if abs(self.canoe.x - target_x) > 1:  # Still animating
            # Move toward target lane
            if self.canoe.x < target_x:
                self.canoe.x = min(self.canoe.x + self.lane_switch_speed, target_x)
            else:
                self.canoe.x = max(self.canoe.x - self.lane_switch_speed, target_x)
        else:
            # Animation complete - snap to exact position
            self.canoe.x = target_x
            self.canoe_lane = self.target_lane

        # Check if we should trigger jump when obstacles are close
        if self.should_jump and not self.is_jumping and len(self.jump_obstacles) > 0:
            # Check if any jump obstacle is within jump trigger distance
            jump_trigger_distance = 70  # pixels - how far above canoe to trigger jump
            for obstacle in self.jump_obstacles:
                if obstacle in self.obstacles:
                    # Calculate distance from obstacle to canoe (positive = obstacle below, negative = above)
                    distance_to_canoe = canoe_y - obstacle.y
                    # Trigger when obstacle is above canoe but within trigger distance
                    if 0 < distance_to_canoe < jump_trigger_distance:
                        # Trigger jump animation
                        self.is_jumping = True
                        self.jump_start_time = current_time
                        self.should_jump = False  # Clear flag
                        # Create jump particles
                        canoe_x = self.lane_positions[self.canoe_lane] + CANOE_WIDTH // 2
                        canoe_y_center = self.canoe.y + CANOE_HEIGHT // 2
                        for _ in range(15):
                            particle = {
                                'x': canoe_x + random.randint(-20, 20),
                                'y': canoe_y_center + random.randint(-10, 10),
                                'vx': random.uniform(-3, 3),
                                'vy': random.uniform(-5, -2),
                                'life': 30,  # frames
                                'size': random.randint(3, 8)
                            }
                            self.jump_particles.append(particle)
                        break  # Only trigger once

        # Update jump animation
        if self.is_jumping:
            elapsed = current_time - self.jump_start_time
            if elapsed < self.jump_duration:
                # Calculate parabolic jump arc
                progress = elapsed / self.jump_duration
                # Parabola: y = -4h * (x - 0.5)^2 + h
                jump_offset = -4 * self.jump_height * (progress - 0.5) ** 2 + self.jump_height
                self.canoe.y = SCREEN_HEIGHT - 150 - jump_offset
            else:
                # Jump complete
                self.is_jumping = False
                self.canoe.y = SCREEN_HEIGHT - 150

        # Update jump particles
        for particle in self.jump_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.3  # Gravity
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.jump_particles.remove(particle)

        # Auto-scroll river (constant forward movement)
        river_scroll_speed = -self.auto_scroll_speed
        self.river.update(river_scroll_speed)

        # Update obstacles with river scroll
        canoe_y = self.canoe.y

        for obstacle in self.obstacles[:]:
            obstacle.update(river_scroll_speed)
            if obstacle.is_off_screen():
                self.obstacles.remove(obstacle)
                # Remove from dodge tracking if it's there
                if obstacle in self.dodge_obstacles:
                    self.dodge_obstacles.remove(obstacle)

        # Auto-recenter after the dodged obstacles have passed
        if self.should_recenter and len(self.dodge_obstacles) > 0:
            # Check if all dodge obstacles have passed the canoe
            all_dodge_obstacles_passed = True
            for obstacle in self.dodge_obstacles:
                if obstacle in self.obstacles and obstacle.y < canoe_y + CANOE_HEIGHT:
                    all_dodge_obstacles_passed = False
                    break

            if all_dodge_obstacles_passed:
                self.target_lane = 1  # Return to center (lane 2)
                self.should_recenter = False
                self.dodge_obstacles = []

        # QTE SYSTEM UPDATE
        # Spawn new QTE if needed - only after previous obstacles have passed
        can_spawn_new_qte = self.qte_manager.should_spawn_qte(current_time)

        # CRITICAL: Check if all obstacles from previous QTE have passed the boat
        if can_spawn_new_qte and len(self.obstacles) > 0:
            # Don't spawn if any obstacles are still above or at boat level
            for obstacle in self.obstacles:
                if obstacle.y < canoe_y + CANOE_HEIGHT + 100:  # 100px buffer
                    can_spawn_new_qte = False
                    break

        if can_spawn_new_qte:
            self.qte_manager.spawn_qte(current_time)
            # Spawn obstacles for this QTE
            if len(self.qte_manager.qtes) > 0:
                new_qte = self.qte_manager.qtes[-1]
                self.spawn_obstacle_for_qte(new_qte)

        # Update QTE manager with paddle input
        self.qte_manager.update(current_time, left_paddle, right_paddle)

        # Check if QTE was just completed (check all QTEs for newly finished ones)
        for qte in self.qte_manager.qtes:
            if qte.is_finished(current_time) and qte.result != QTEResult.PENDING:
                # Check if we already processed this QTE
                if not hasattr(qte, 'processed'):
                    qte.processed = True  # Mark as processed

                    # Handle result
                    if qte.result == QTEResult.PERFECT:
                        self.player.score += 3
                        self.sound_point.play()
                        self.combo_count += 1
                        self.last_qte_result = "PERFECT!"
                        self.qte_feedback_time = current_time
                        # Dodge the obstacle (move to side lane)
                        self._dodge_obstacle(qte.qte_type, qte)
                        # DON'T remove obstacles - let them pass naturally
                    elif qte.result == QTEResult.GOOD:
                        self.player.score += 1
                        self.sound_point.play()
                        self.combo_count += 1
                        self.last_qte_result = "GOOD!"
                        self.qte_feedback_time = current_time
                        # Dodge the obstacle (move to side lane)
                        self._dodge_obstacle(qte.qte_type, qte)
                        # DON'T remove obstacles - let them pass naturally
                    elif qte.result == QTEResult.MISS:
                        # Missed QTE - lose health, DON'T dodge (stay in current lane)
                        # This causes visual collision with crocodiles
                        self.health -= 1
                        self.combo_count = 0
                        self.last_qte_result = "MISS!"
                        self.qte_feedback_time = current_time
                        # Trigger damage flash
                        self.damage_flash_time = current_time
                        # Boat stays in lane 2 (center) → visibly hits obstacles → red flash
                        # Set up recentering so boat returns to center after obstacles pass
                        self.target_lane = 1  # Stay in center
                        self.should_recenter = True
                        qte_id = id(qte)
                        if qte_id in self.qte_obstacles:
                            self.dodge_obstacles = self.qte_obstacles[qte_id][:]
                        # Obstacles will scroll past and off screen
                        if self.health <= 0:
                            self.sound_game_over.play()
                            pygame.mixer.music.stop()
                            self.game_over = True

        # River bank collision disabled - QTE system handles all obstacles

    def _dodge_obstacle(self, qte_type: QTEType, qte):
        """
        Set target lane based on QTE type (Temple Run style).

        Rowing LEFT moves boat RIGHT (to lane 3)
        Rowing RIGHT moves boat LEFT (to lane 1)
        Rowing BOTH keeps boat in CENTER (lane 2)
        """
        if qte_type == QTEType.LEFT:
            # Player rows LEFT → boat moves RIGHT to lane 3
            self.target_lane = 2  # Lane 3 (right)
            self.should_recenter = True
            # Track obstacles for this dodge
            qte_id = id(qte)
            if qte_id in self.qte_obstacles:
                self.dodge_obstacles = self.qte_obstacles[qte_id][:]
        elif qte_type == QTEType.RIGHT:
            # Player rows RIGHT → boat moves LEFT to lane 1
            self.target_lane = 0  # Lane 1 (left)
            self.should_recenter = True
            # Track obstacles for this dodge
            qte_id = id(qte)
            if qte_id in self.qte_obstacles:
                self.dodge_obstacles = self.qte_obstacles[qte_id][:]
        elif qte_type == QTEType.BOTH:
            # Player rows BOTH → boat will jump over obstacles when close
            self.target_lane = 1  # Lane 2 (center)
            self.should_recenter = False
            self.dodge_obstacles = []
            # Set flag to jump when obstacles are close
            self.should_jump = True
            qte_id = id(qte)
            if qte_id in self.qte_obstacles:
                self.jump_obstacles = self.qte_obstacles[qte_id][:]

    def draw(self):
        current_time = pygame.time.get_ticks()

        # Draw river background
        self.river.draw(self.screen)

        # Draw game objects - order matters for layering
        # When jumping, draw boat on top; otherwise draw obstacles on top
        if self.is_jumping:
            # Draw obstacles first, then boat on top (boat appears to jump over)
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)

            self.canoe.draw(self.screen)

            # Draw jump particles (splash effects) on top of everything
            for particle in self.jump_particles:
                alpha = int(255 * (particle['life'] / 30))  # Fade out
                particle_surface = pygame.Surface((particle['size'], particle['size']), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, (255, 255, 255, alpha),
                                 (particle['size'] // 2, particle['size'] // 2), particle['size'] // 2)
                self.screen.blit(particle_surface, (int(particle['x']), int(particle['y'])))
        else:
            # Normal draw order - boat first, then obstacles on top
            self.canoe.draw(self.screen)

            for obstacle in self.obstacles:
                obstacle.draw(self.screen)

        # Draw paddle indicators
        self.left_indicator.draw(self.screen)
        self.right_indicator.draw(self.screen)

        # Draw damage flash effect (red overlay when losing health)
        if self.damage_flash_time > 0:
            elapsed = current_time - self.damage_flash_time
            if elapsed < self.damage_flash_duration:
                # Calculate flash alpha (fade out)
                alpha = int(150 * (1.0 - elapsed / self.damage_flash_duration))
                flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                flash_surface.fill((255, 0, 0, alpha))  # Red with fading alpha
                self.screen.blit(flash_surface, (0, 0))
            else:
                # Flash finished
                self.damage_flash_time = 0

        # Draw lane guides (subtle lines for debugging - can be removed later)
        # Uncomment these lines if you want to see the lane boundaries
        # for lane_x in self.lane_positions:
        #     pygame.draw.line(self.screen, (100, 100, 100, 50),
        #                     (lane_x + CANOE_WIDTH//2, 0),
        #                     (lane_x + CANOE_WIDTH//2, SCREEN_HEIGHT), 1)

        # Draw QTE prompts (on top of everything)
        self.qte_manager.draw(self.screen, current_time)

        # Draw HUD score box (styled like menu buttons)
        box = pygame.Rect(10, 10, 240, 80)
        pygame.draw.rect(self.screen, BTN_BG,  box, border_radius=14)
        pygame.draw.rect(self.screen, BTN_OUT, box, 2, border_radius=14)

        # Name (smaller) at top of the box
        name_surface = self.small_font.render(self.player_name, True, (25,25,25))
        self.screen.blit(name_surface, name_surface.get_rect(center=(box.centerx, box.y + 22)))

        # Score (bigger) centered lower in the box
        score_font_hud = pygame.font.SysFont(None, 36)
        score_surface = score_font_hud.render(str(self.player.score), True, (25,25,25))
        self.screen.blit(score_surface, score_surface.get_rect(center=(box.centerx, box.y + 55)))

        # Draw health hearts (top right)
        heart_x = SCREEN_WIDTH - 150
        heart_y = 30
        for i in range(3):
            color = (255, 50, 50) if i < self.health else (100, 100, 100)
            pygame.draw.circle(self.screen, color, (heart_x + i * 40, heart_y), 15)
            pygame.draw.circle(self.screen, color, (heart_x + i * 40 + 15, heart_y), 15)
            # Triangle for bottom of heart
            points = [
                (heart_x + i * 40 - 15, heart_y),
                (heart_x + i * 40 + 30, heart_y),
                (heart_x + i * 40 + 7.5, heart_y + 25)
            ]
            pygame.draw.polygon(self.screen, color, points)

        # Combo counter removed for cleaner UI

        # Draw QTE feedback (PERFECT/GOOD/MISS)
        if self.last_qte_result and current_time - self.qte_feedback_time < 1500:
            feedback_font = pygame.font.SysFont("Impact", 56) if pygame.font.get_init() else pygame.font.SysFont(None, 56)
            if self.last_qte_result == "PERFECT!":
                color = (50, 255, 50)
            elif self.last_qte_result == "GOOD!":
                color = (255, 255, 50)
            else:
                color = (255, 50, 50)

            feedback_surf = feedback_font.render(self.last_qte_result, True, color)
            # Fade out effect
            fade_progress = (current_time - self.qte_feedback_time) / 1500
            alpha = int(255 * (1 - fade_progress))
            feedback_surf.set_alpha(alpha)
            self.screen.blit(feedback_surf, (SCREEN_WIDTH // 2 - feedback_surf.get_width() // 2, 300))
        
        # Draw game over screen with personalized message
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill(PALETTE["overlay"])
            self.screen.blit(overlay, (0, 0))

            # Get personalized quip based on score
            title_text = quip_named(self.player.score, self.player_name)

            left_margin, right_margin = 60, 60
            maxw = SCREEN_WIDTH - left_margin - right_margin

            # Headline (wrapped)
            y = 150
            for hl in wrap_lines(self.title_font, title_text, maxw):
                surf = self.title_font.render(hl, True, PALETTE["title"])
                self.screen.blit(surf, surf.get_rect(center=(SCREEN_WIDTH//2, y)))
                y += 64
            y += 12

            # Score display
            score_line = f"{self.player_name} — {self.player.score} pts"
            score_surf = self.body_font.render(score_line, True, (255,255,255))
            self.screen.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH//2, y)))
            y += 50

            # Keycaps near bottom
            key_y = SCREEN_HEIGHT - 64
            kx = SCREEN_WIDTH//2
            draw_keycap(self.screen, "R", kx-60, key_y, self.key_font)
            draw_keycap(self.screen, "Q", kx+60, key_y, self.key_font)
            label = self.small_font.render("Restart              Exit to Menu", True, PALETTE["body"])
            self.screen.blit(label, label.get_rect(center=(kx, key_y+30)))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop with keyboard controls for testing"""
        running = True

        while running:
            direction = self.player.get_direction()

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.reset_game()
                    elif event.key == pygame.K_q:
                        if self.game_over:
                            # During game over, Q exits to menu
                            return "menu"
                        else:
                            # During gameplay, Q quits entirely
                            return "quit"

            # Update and draw
            self.update(direction.direction_str, direction.left, direction.right)
            self.draw()
            self.clock.tick(FPS)

        return "quit"