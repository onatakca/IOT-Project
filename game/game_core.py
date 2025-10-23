import pygame
import random
import sys
import os

from game.player import Player
from .settings import *
from .river import River
from .canoe import Canoe
from .obstacle import Obstacle
from .paddle_indicator import PaddleIndicator

BASE_DIR = os.path.dirname(__file__) 

class Game:
    def __init__(self, player: Player):
        self.player = player
        
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Canoe Game - IoT Demo")
        self.clock = pygame.time.Clock()

        # Load images and scale to game sizes
        self.boat_img = pygame.image.load(os.path.join(BASE_DIR, 'images', 'boat.png')) .convert_alpha()
        self.rock_img = pygame.image.load(os.path.join(BASE_DIR,'images','rock.png')).convert_alpha()

        # Scale to original game dimensions
        self.boat_img = pygame.transform.scale(self.boat_img, (CANOE_WIDTH, CANOE_HEIGHT))
        self.rock_img = pygame.transform.scale(self.rock_img, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))

        # Load sound effects
        pygame.mixer.init()
        self.sound_game_start = pygame.mixer.Sound(os.path.join(BASE_DIR,'sounds','game_start.mp3'))
        self.sound_game_over = pygame.mixer.Sound(os.path.join(BASE_DIR,'sounds','game_over.mp3'))
        self.sound_point = pygame.mixer.Sound(os.path.join(BASE_DIR,'sounds','point.mp3'))

        # Load background music
        pygame.mixer.music.load(os.path.join(BASE_DIR,'sounds','river_splashy.mp3'))

        self.reset_game()

        # Paddle indicators
        self.left_indicator = PaddleIndicator(50, 20, "LEFT")
        self.right_indicator = PaddleIndicator(SCREEN_WIDTH - 130, 20, "RIGHT")

    def reset_game(self):
        self.river = River()
        self.canoe = Canoe(SCREEN_WIDTH // 2 - CANOE_WIDTH // 2,
                          SCREEN_HEIGHT // 2,  # Start at middle of screen
                          self.boat_img)
        self.obstacles = []
        self.game_over = False
        self.game_won = False
        self.last_spawn_time = pygame.time.get_ticks()

        # Play game start sound and start background music
        self.sound_game_start.play()
        pygame.mixer.music.set_volume(0.75)  # Set volume to 75% (25% reduction)
        pygame.mixer.music.play(-1)  # Loop background music indefinitely
        
    def spawn_obstacle(self):
        # Get river bounds at the top of the screen where obstacles spawn
        spawn_y = 0
        left_bound, right_bound = self.river.get_river_bounds_at_y(spawn_y)

        # Spawn obstacle within river bounds
        # Add some margin to keep obstacles away from the banks
        margin = 20
        left_bound += margin
        right_bound -= margin + OBSTACLE_WIDTH

        if right_bound > left_bound:
            x = random.randint(int(left_bound), int(right_bound))
            self.obstacles.append(Obstacle(x, -OBSTACLE_HEIGHT, self.rock_img))
        
    def check_collision(self):
        canoe_rect = self.canoe.get_collision_rect()  # Use smaller hitbox
        for obstacle in self.obstacles:
            if canoe_rect.colliderect(obstacle.get_rect()):
                return True
        return False
    
    def update(self, direction, left_paddle, right_paddle):
        if self.game_over or self.game_won:
            return

        # Update paddle indicators
        self.left_indicator.set_active(left_paddle)
        self.right_indicator.set_active(right_paddle)

        # Move canoe horizontally
        self.canoe.move(direction)

        # Handle vertical movement based on paddling
        is_rowing = left_paddle or right_paddle
        river_scroll_speed = 0
        if is_rowing:
            # Move UP (fighting the current) - river banks should move DOWN
            self.canoe.y -= UPSTREAM_SPEED
            # Limit how far up the canoe can go (around halfway)
            if self.canoe.y < CANOE_MAX_UP_Y:
                self.canoe.y = CANOE_MAX_UP_Y
            # Negative scroll makes river move DOWN on screen
            river_scroll_speed = -UPSTREAM_SPEED
            self.river.update(river_scroll_speed)
        else:
            # Drift DOWN (current pushing down) - river banks should move UP
            self.canoe.y += DOWNSTREAM_DRIFT
            # Positive scroll makes river move UP on screen
            river_scroll_speed = DOWNSTREAM_DRIFT
            self.river.update(river_scroll_speed)

        # Check if canoe hit the bottom of the screen (game over)
        if self.canoe.y + self.canoe.height >= SCREEN_HEIGHT:
            if not self.game_over:
                self.sound_game_over.play()
                pygame.mixer.music.stop()  # Stop background music
            self.game_over = True

        # Update obstacles with river scroll
        for obstacle in self.obstacles[:]:
            obstacle.update(river_scroll_speed)
            # Award points if obstacle passed the canoe
            if obstacle.y > self.canoe.y + self.canoe.height and not hasattr(obstacle, 'counted'):
                self.player.score += 1
                self.sound_point.play()  # Play point sound
                obstacle.counted = True  # Mark as counted so we don't count it again
            if obstacle.is_off_screen():
                self.obstacles.remove(obstacle)

        # Spawn new obstacles
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time > SPAWN_INTERVAL:
            self.spawn_obstacle()
            self.last_spawn_time = current_time

        # Check collisions with obstacles
        if self.check_collision():
            if not self.game_over:
                self.sound_game_over.play()
                pygame.mixer.music.stop()  # Stop background music
            self.game_over = True

        # Check collision with river banks
        if self.river.check_collision(self.canoe.get_collision_rect()):
            if not self.game_over:
                self.sound_game_over.play()
                pygame.mixer.music.stop()  # Stop background music
            self.game_over = True
    
    def draw(self):
        # Draw river
        self.river.draw(self.screen)

        # Draw paddle indicators
        self.left_indicator.draw(self.screen)
        self.right_indicator.draw(self.screen)

        # Draw game objects
        self.canoe.draw(self.screen)
        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        # Draw points score
        font = pygame.font.Font(None, 48)
        points_text = font.render(f"Points: {self.player.score}", True, WHITE)
        text_rect = points_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        # Add black outline for visibility
        outline_text = font.render(f"Points: {self.player.score}", True, BLACK)
        for offset in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            self.screen.blit(outline_text, (text_rect.x + offset[0], text_rect.y + offset[1]))
        self.screen.blit(points_text, text_rect)
        
        # Draw game over screen
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))

            game_over_font = pygame.font.Font(None, 72)
            title_text = game_over_font.render("GAME OVER!", True, RED)
            title_rect = title_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(title_text, title_rect)

            score_font = pygame.font.Font(None, 48)
            score_msg = score_font.render(f"Final Score: {self.player.score} points", True, WHITE)
            score_rect = score_msg.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(score_msg, score_rect)

            restart_font = pygame.font.Font(None, 36)
            restart_text = restart_font.render("Press R to Restart or Q to Quit",
                                              True, YELLOW)
            restart_rect = restart_text.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
            self.screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop with keyboard controls for testing"""
        running = True

        while running:
            direction = self.player.get_direction()

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.game_over:
                        self.reset_game()
                    elif event.key == pygame.K_q:
                        running = False

            # Update and draw
            self.update(direction.direction_str, direction.left, direction.right)
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()