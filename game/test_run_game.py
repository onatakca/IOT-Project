import pygame
import random
import math
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (50, 150, 255)
DARK_BLUE = (20, 60, 120)
GREEN = (50, 200, 50)
RED = (255, 50, 50)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
BROWN = (101, 67, 33)
LIGHT_GREEN = (34, 139, 34)

# Game settings
CANOE_WIDTH = 55  # Adjusted width
CANOE_HEIGHT = 100
CANOE_SPEED = 5
UPSTREAM_SPEED = 3  # How fast canoe moves up when rowing
DOWNSTREAM_DRIFT = 1.5  # How fast canoe drifts down when not rowing
CANOE_MAX_UP_Y = SCREEN_HEIGHT // 2  # Highest point canoe can reach (middle of screen)
RIVER_WIDTH = 400
OBSTACLE_WIDTH = 80
OBSTACLE_HEIGHT = 80
OBSTACLE_SPEED = 3
SPAWN_INTERVAL = 2000  # milliseconds
GOAL_DISTANCE = 5000  # Distance to travel to win

class River:
    """Generates a curved river with S-shaped variation"""
    def __init__(self):
        self.segments = []
        self.segment_height = 5  # Smaller segments for smoother curves
        self.scroll_offset = 0
        self.total_scroll = 0  # Never wraps - accumulates forever for water animation
        self.center_offset = SCREEN_WIDTH // 2
        self.curve_phase = 0  # Phase for sinusoidal curves
        self.current_scroll_speed = 0  # Track current river scroll speed

        # Load textures and scale them to tile size
        WATER_TILE_SIZE = 128  # Size for water tiles
        GRASS_TILE_SIZE = 192  # Slightly larger for grass tiles

        water_original = pygame.image.load('images/water.png').convert_alpha()
        grass_original = pygame.image.load('images/grass.png').convert_alpha()

        # Scale down to tileable size
        self.water_texture = pygame.transform.scale(water_original, (WATER_TILE_SIZE, WATER_TILE_SIZE))
        self.grass_texture = pygame.transform.scale(grass_original, (GRASS_TILE_SIZE, GRASS_TILE_SIZE))

        # Get texture dimensions
        self.water_texture_width = WATER_TILE_SIZE
        self.water_texture_height = WATER_TILE_SIZE
        self.grass_texture_width = GRASS_TILE_SIZE
        self.grass_texture_height = GRASS_TILE_SIZE

        # Generate initial river segments
        for i in range(SCREEN_HEIGHT // self.segment_height + 20):
            self.add_segment()

    def add_segment(self):
        """Add a new river segment with smooth S-curve pattern"""
        if len(self.segments) == 0:
            offset = 0
        else:
            # Create smooth S-curve using sine wave with less randomness
            self.curve_phase += 0.02  # Smaller increment = smoother, wider curves
            sine_offset = math.sin(self.curve_phase) * 100  # Amplitude of 100
            random_variation = random.uniform(-5, 5)  # Less randomness for smoother curves
            offset = sine_offset + random_variation

            # Keep the river from going too far off center
            max_offset = 120
            offset = max(min(offset, max_offset), -max_offset)

        self.segments.append(offset)

    def update(self, speed):
        """Scroll the river"""
        self.current_scroll_speed = speed  # Store for water animation adjustment
        self.scroll_offset += speed
        self.total_scroll += speed  # Accumulate forever, never wraps

        # Scrolling forward (river moves down on screen)
        while self.scroll_offset >= self.segment_height:
            self.scroll_offset -= self.segment_height
            self.segments.pop(0)
            self.add_segment()

        # Scrolling backward (river moves up on screen)
        while self.scroll_offset < 0:
            self.scroll_offset += self.segment_height
            # Add segment at the beginning - continue the S-curve pattern
            self.curve_phase -= 0.02  # Go backwards in the curve
            sine_offset = math.sin(self.curve_phase) * 100
            random_variation = random.uniform(-5, 5)
            offset = sine_offset + random_variation
            max_offset = 120
            offset = max(min(offset, max_offset), -max_offset)

            self.segments.insert(0, offset)
            # Remove from end to keep list size reasonable
            if len(self.segments) > 200:
                self.segments.pop()

    def get_river_bounds_at_y(self, y):
        """Get the left and right bounds of the river at a given y position"""
        # Determine which segment this y position is in
        segment_index = int((y + self.scroll_offset) // self.segment_height)

        if segment_index < 0 or segment_index >= len(self.segments):
            offset = 0
        else:
            offset = self.segments[segment_index]

        center = self.center_offset + offset
        left_bound = center - RIVER_WIDTH // 2
        right_bound = center + RIVER_WIDTH // 2

        return left_bound, right_bound

    def draw(self, screen):
        """Draw the river with curved banks"""
        # Water flow with partial compensation to reduce extremes
        # NOTE: Good baseline values that were close: base // 10, compensation * 0.5
        #       (good speed when drifting/moving down, slightly slow when paddling/moving up)
        base_speed = pygame.time.get_ticks() // 10  # Faster base speed
        speed_compensation = int(self.total_scroll * 0.6)  # Slightly stronger compensation for more speed when paddling up
        water_offset = (base_speed - speed_compensation) % self.water_texture_height

        # Draw water texture
        for tile_y in range(-self.water_texture_height, SCREEN_HEIGHT + self.water_texture_height, self.water_texture_height):
            for tile_x in range(0, SCREEN_WIDTH, self.water_texture_width):
                screen.blit(self.water_texture, (tile_x, tile_y + water_offset))

        # Draw river banks with grass texture
        for i in range(len(self.segments) - 1):
            # Negate scroll_offset: positive scroll moves river DOWN, negative moves UP
            y1 = i * self.segment_height - self.scroll_offset
            y2 = (i + 1) * self.segment_height - self.scroll_offset

            if y2 < -50 or y1 > SCREEN_HEIGHT + 50:
                continue

            offset1 = self.segments[i]
            offset2 = self.segments[i + 1]

            center1 = self.center_offset + offset1
            center2 = self.center_offset + offset2

            # Left bank
            left1 = center1 - RIVER_WIDTH // 2
            left2 = center2 - RIVER_WIDTH // 2

            # Draw left shore with grass texture
            if left1 > 0:
                # Create clipping rect for left bank
                bank_rect = pygame.Rect(0, int(y1), int(left1), max(1, int(y2 - y1)))
                screen.set_clip(bank_rect)

                # Tile grass texture - use total_scroll to avoid wrapping glitches
                grass_offset = int(-self.total_scroll) % self.grass_texture_height
                for grass_y in range(-self.grass_texture_height, SCREEN_HEIGHT + self.grass_texture_height, self.grass_texture_height):
                    for grass_x in range(0, int(left1) + self.grass_texture_width, self.grass_texture_width):
                        screen.blit(self.grass_texture, (grass_x, grass_y + grass_offset))

                # Remove clipping
                screen.set_clip(None)
                # Draw bank edge (reduced width)
                pygame.draw.line(screen, BROWN, (left1, y1), (left2, y2), 2)

            # Right bank
            right1 = center1 + RIVER_WIDTH // 2
            right2 = center2 + RIVER_WIDTH // 2

            # Draw right shore with grass texture
            if right1 < SCREEN_WIDTH:
                # Create clipping rect for right bank
                bank_rect = pygame.Rect(int(right1), int(y1), SCREEN_WIDTH - int(right1), max(1, int(y2 - y1)))
                screen.set_clip(bank_rect)

                # Tile grass texture - use total_scroll to avoid wrapping glitches
                grass_offset = int(-self.total_scroll) % self.grass_texture_height
                for grass_y in range(-self.grass_texture_height, SCREEN_HEIGHT + self.grass_texture_height, self.grass_texture_height):
                    for grass_x in range(int(right1) - self.grass_texture_width, SCREEN_WIDTH + self.grass_texture_width, self.grass_texture_width):
                        screen.blit(self.grass_texture, (grass_x, grass_y + grass_offset))

                # Remove clipping
                screen.set_clip(None)
                # Draw bank edge (reduced width)
                pygame.draw.line(screen, BROWN, (right1, y1), (right2, y2), 2)

    def check_collision(self, canoe_rect):
        """Check if canoe collides with river banks"""
        canoe_center_y = canoe_rect.centery
        left_bound, right_bound = self.get_river_bounds_at_y(canoe_center_y)

        # Check if canoe is outside river bounds
        if canoe_rect.left < left_bound or canoe_rect.right > right_bound:
            return True
        return False

class Canoe:
    def __init__(self, x, y, boat_img=None):
        self.x = x
        self.y = y
        self.width = CANOE_WIDTH
        self.height = CANOE_HEIGHT
        self.speed = CANOE_SPEED
        self.boat_img = boat_img

    def move(self, direction):
        """Move canoe based on paddle input"""
        if direction == "LEFT":
            self.x -= self.speed
        elif direction == "RIGHT":
            self.x += self.speed
        # No boundary check here - will be checked against river bounds in game

    def draw(self, screen):
        if self.boat_img:
            # Draw boat image
            screen.blit(self.boat_img, (self.x, self.y))
        else:
            # Fallback to original drawing
            pygame.draw.rect(screen, (139, 69, 19),
                            (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, BLACK,
                            (self.x, self.y, self.width, self.height), 3)
            points = [
                (self.x, self.y),
                (self.x + self.width, self.y),
                (self.x + self.width // 2, self.y - 15)
            ]
            pygame.draw.polygon(screen, (139, 69, 19), points)
            pygame.draw.polygon(screen, BLACK, points, 3)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def get_collision_rect(self):
        """Smaller hitbox for more accurate collision detection"""
        # Shrink hitbox by 30% on all sides
        margin_x = self.width * 0.15
        margin_y = self.height * 0.15
        return pygame.Rect(self.x + margin_x, self.y + margin_y,
                          self.width - margin_x * 2, self.height - margin_y * 2)

class Obstacle:
    def __init__(self, x, y, rock_img=None):
        self.x = x
        self.y = y
        self.width = OBSTACLE_WIDTH
        self.height = OBSTACLE_HEIGHT
        self.rock_img = rock_img

    def update(self, river_scroll_speed=0):
        # Move only with river scroll - obstacles are fixed to the river map
        self.y -= river_scroll_speed

    def draw(self, screen):
        if self.rock_img:
            # Draw rock image
            screen.blit(self.rock_img, (self.x, self.y))
        else:
            # Fallback to original drawing
            pygame.draw.rect(screen, GRAY,
                            (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (50, 50, 50),
                            (self.x, self.y, self.width, self.height), 3)
            # Add some texture lines
            pygame.draw.line(screen, (70, 70, 70),
                            (self.x + 10, self.y + 10),
                            (self.x + 30, self.y + 25), 2)
            pygame.draw.line(screen, (70, 70, 70),
                            (self.x + 50, self.y + 15),
                            (self.x + 70, self.y + 35), 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT

class PaddleIndicator:
    def __init__(self, x, y, label):
        self.x = x
        self.y = y
        self.label = label
        self.active = False
        self.width = 80
        self.height = 40
        
    def set_active(self, active):
        self.active = active
        
    def draw(self, screen):
        color = GREEN if self.active else GRAY
        pygame.draw.rect(screen, color, 
                        (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, BLACK, 
                        (self.x, self.y, self.width, self.height), 2)
        
        # Draw label
        font = pygame.font.Font(None, 24)
        text = font.render(self.label, True, BLACK)
        text_rect = text.get_rect(center=(self.x + self.width // 2, 
                                          self.y + self.height // 2))
        screen.blit(text, text_rect)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Canoe Game - IoT Demo")
        self.clock = pygame.time.Clock()

        # Load images and scale to game sizes
        self.boat_img = pygame.image.load('images/boat.png').convert_alpha()
        self.rock_img = pygame.image.load('images/rock.png').convert_alpha()

        # Scale to original game dimensions
        self.boat_img = pygame.transform.scale(self.boat_img, (CANOE_WIDTH, CANOE_HEIGHT))
        self.rock_img = pygame.transform.scale(self.rock_img, (OBSTACLE_WIDTH, OBSTACLE_HEIGHT))

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
        self.points = 0  # Track score by obstacles passed
        self.game_over = False
        self.game_won = False
        self.last_spawn_time = pygame.time.get_ticks()
        
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
            self.game_over = True

        # Update obstacles with river scroll
        for obstacle in self.obstacles[:]:
            obstacle.update(river_scroll_speed)
            # Award points if obstacle passed the canoe
            if obstacle.y > self.canoe.y + self.canoe.height and not hasattr(obstacle, 'counted'):
                self.points += 1
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
            self.game_over = True

        # Check collision with river banks
        if self.river.check_collision(self.canoe.get_collision_rect()):
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
        points_text = font.render(f"Points: {self.points}", True, WHITE)
        text_rect = points_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        # Add black outline for visibility
        outline_text = font.render(f"Points: {self.points}", True, BLACK)
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
            score_msg = score_font.render(f"Final Score: {self.points} points", True, WHITE)
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
            # Simulate paddle states from arrow keys
            keys = pygame.key.get_pressed()
            up_key = keys[pygame.K_UP]
            left_key = keys[pygame.K_LEFT]
            right_key = keys[pygame.K_RIGHT]

            # Determine paddle states and direction
            # UP = both paddles rowing
            # LEFT = only left paddle rowing (turns right)
            # RIGHT = only right paddle rowing (turns left)
            if up_key:
                # Both paddles rowing - go straight
                left_paddle = True
                right_paddle = True
                direction = "STRAIGHT"
            elif left_key:
                # Only left paddle - turn right
                left_paddle = True
                right_paddle = False
                direction = "RIGHT"
            elif right_key:
                # Only right paddle - turn left
                left_paddle = False
                right_paddle = True
                direction = "LEFT"
            else:
                # No rowing - flow back
                left_paddle = False
                right_paddle = False
                direction = "STOP"

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
            self.update(direction, left_paddle, right_paddle)
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

def main():
    game = Game()
    print("=== CANOE ROWING GAME ===")
    print("Controls:")
    print("  UP    = Both paddles (go UP)")
    print("  LEFT  = Left paddle only (go UP and turn RIGHT)")
    print("  RIGHT = Right paddle only (go UP and turn LEFT)")
    print("  No key = Drift DOWN with current")
    print(" ")
    print("Goal: Pass as many obstacles as possible to score points!")
    print("Keep rowing to fight the current or you'll drift to the bottom!")
    print("If you hit the bottom of the screen, you lose!")
    print("")
    print("  R = Restart")
    print("  Q = Quit")
    print("=" * 50)
    game.run()

if __name__ == "__main__":
    main()