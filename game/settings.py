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