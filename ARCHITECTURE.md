# Game Architecture - test_run_game.py

## Overview

This document describes the architecture of the canoe rowing game, which uses IoT paddle sensors to control a canoe navigating through obstacles in a river.

## Class Diagram

```mermaid
classDiagram
    class Game {
        -screen
        -clock
        -river: River
        -canoe: Canoe
        -obstacles: List~Obstacle~
        -points: int
        -game_over: bool
        -game_won: bool
        -boat_img
        -rock_img
        -left_indicator: PaddleIndicator
        -right_indicator: PaddleIndicator
        +__init__()
        +reset_game()
        +spawn_obstacle()
        +check_collision() bool
        +update(direction, left_paddle, right_paddle)
        +draw()
        +run()
    }

    class River {
        -segments: List~float~
        -segment_height: int
        -scroll_offset: float
        -total_scroll: float
        -center_offset: int
        -curve_phase: float
        -current_scroll_speed: float
        -water_texture: Surface
        -grass_texture: Surface
        +__init__()
        +add_segment()
        +update(speed)
        +get_river_bounds_at_y(y) tuple
        +draw(screen)
        +check_collision(canoe_rect) bool
    }

    class Canoe {
        -x: int
        -y: int
        -width: int
        -height: int
        -speed: int
        -boat_img: Surface
        +__init__(x, y, boat_img)
        +move(direction)
        +draw(screen)
        +get_rect() Rect
        +get_collision_rect() Rect
    }

    class Obstacle {
        -x: int
        -y: int
        -width: int
        -height: int
        -rock_img: Surface
        -counted: bool
        +__init__(x, y, rock_img)
        +update(river_scroll_speed)
        +draw(screen)
        +get_rect() Rect
        +is_off_screen() bool
    }

    class PaddleIndicator {
        -x: int
        -y: int
        -label: str
        -active: bool
        -width: int
        -height: int
        +__init__(x, y, label)
        +set_active(active)
        +draw(screen)
    }

    Game "1" --> "1" River : has
    Game "1" --> "1" Canoe : has
    Game "1" --> "*" Obstacle : manages
    Game "1" --> "2" PaddleIndicator : has
    River ..> Canoe : checks collision
    Game ..> Obstacle : checks collision
```

## Class Descriptions

### Game
**Main game controller** that orchestrates all game components and manages the game loop.

- Initializes Pygame, loads assets (boat and rock images)
- Manages game state (points, game_over, game_won)
- Handles game loop, update logic, and rendering
- Spawns obstacles at regular intervals
- Checks collisions between canoe, obstacles, and river banks
- Displays UI elements (score, paddle indicators, game over screen)

### River
**Dynamic river environment** with curved banks and scrolling textures.

- Generates S-curved river path using sinusoidal functions
- Manages river scrolling (moves up when rowing, down when drifting)
- Draws animated water and grass textures
- Provides river boundary information for collision detection
- Tracks scroll offset for smooth texture animation

### Canoe
**Player-controlled boat** that moves through the river.

- Handles horizontal movement (left/right)
- Vertical position controlled by Game based on paddle input
- Draws boat sprite or fallback rectangle
- Provides both full rect and smaller collision rect for accurate hit detection

### Obstacle
**Rocks spawned in the river** that the player must avoid.

- Moves with river scroll speed (fixed to river coordinate system)
- Draws rock sprite or fallback rectangle
- Tracks whether it has been counted for scoring
- Removes itself when off-screen

### PaddleIndicator
**Visual feedback** showing which paddles are active.

- Displays LEFT/RIGHT paddle status at top of screen
- Changes color based on active state (green = active, gray = inactive)
- Provides real-time feedback to player

## Game Flow

```mermaid
flowchart TD
    A[Game Start] --> B[Initialize Game]
    B --> C[Load Assets]
    C --> D[Reset Game State]
    D --> E[Game Loop]
    E --> F{Check Input}
    F --> G[Update Paddle States]
    G --> H[Move Canoe]
    H --> I{Both Paddles?}
    I -->|Yes| J[Move UP Straight]
    I -->|Left Only| K[Move UP + Turn RIGHT]
    I -->|Right Only| L[Move UP + Turn LEFT]
    I -->|None| M[Drift DOWN]
    J --> N[Scroll River]
    K --> N
    L --> N
    M --> N
    N --> O[Update Obstacles]
    O --> P[Check Collisions]
    P --> Q{Collision?}
    Q -->|Yes| R[Game Over]
    Q -->|No| S[Spawn New Obstacles]
    S --> T[Update Score]
    T --> U[Draw Everything]
    U --> V{Game Over?}
    V -->|No| E
    V -->|Yes| W{Restart?}
    W -->|Yes| D
    W -->|No| X[Exit]
```

## Control Logic

### Input Mapping
- **UP Arrow**: Both paddles active → Canoe moves UP (straight)
- **LEFT Arrow**: Left paddle only → Canoe moves UP and turns RIGHT
- **RIGHT Arrow**: Right paddle only → Canoe moves UP and turns LEFT
- **No Input**: No paddles → Canoe drifts DOWN with current

### Vertical Movement
- **Rowing** (any paddle active): Canoe moves upward at `UPSTREAM_SPEED` (3 px/frame), river scrolls down
- **Drifting** (no paddles): Canoe drifts downward at `DOWNSTREAM_DRIFT` (1.5 px/frame), river scrolls up
- **Boundary**: Canoe cannot go above middle of screen (y = 300)

### Horizontal Movement
- **Left paddle**: Canoe moves right at `CANOE_SPEED` (5 px/frame)
- **Right paddle**: Canoe moves left at `CANOE_SPEED` (5 px/frame)
- **Both paddles**: No horizontal movement (straight)

### Scoring
- **+1 point** each time an obstacle passes below the canoe
- Obstacles marked as "counted" to prevent double-counting

### Game Over Conditions
1. Collision with obstacle (rock)
2. Collision with river bank
3. Canoe reaches bottom of screen (y + height ≥ 600)

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| SCREEN_WIDTH | 800 | Window width in pixels |
| SCREEN_HEIGHT | 600 | Window height in pixels |
| FPS | 60 | Target frame rate |
| CANOE_WIDTH | 55 | Boat sprite width |
| CANOE_HEIGHT | 100 | Boat sprite height |
| CANOE_SPEED | 5 | Horizontal movement speed |
| UPSTREAM_SPEED | 3 | Upward speed when rowing |
| DOWNSTREAM_DRIFT | 1.5 | Downward drift speed |
| RIVER_WIDTH | 400 | Width of playable river |
| OBSTACLE_WIDTH | 80 | Rock sprite width |
| OBSTACLE_HEIGHT | 80 | Rock sprite height |
| SPAWN_INTERVAL | 2000 | Milliseconds between obstacle spawns |

## Integration Points for IoT

The game is designed to integrate with BLE paddle sensors:

1. **Current**: Keyboard input in `Game.run()` (lines 484-536)
2. **Future**: Replace keyboard polling with BLE data from Thingy:52 devices
3. **Interface**: `update(direction, left_paddle, right_paddle)` method (line 375)
   - `direction`: "LEFT", "RIGHT", "STRAIGHT", or "STOP"
   - `left_paddle`: boolean (True = left paddle active)
   - `right_paddle`: boolean (True = right paddle active)

### BLE Integration Pattern
```python
# Pseudocode for BLE integration
while running:
    # Get paddle states from BLE
    left_paddle = ble_left_device.is_paddling()
    right_paddle = ble_right_device.is_paddling()

    # Determine direction
    if left_paddle and right_paddle:
        direction = "STRAIGHT"
    elif left_paddle:
        direction = "RIGHT"
    elif right_paddle:
        direction = "LEFT"
    else:
        direction = "STOP"

    # Update game
    game.update(direction, left_paddle, right_paddle)
    game.draw()
```

## File Structure

```
game/
├── test_run_game.py       # Main game file (this architecture)
├── images/
│   ├── boat.png           # Canoe sprite
│   ├── rock.png           # Obstacle sprite
│   ├── water.png          # Water texture (tiled)
│   └── grass.png          # Grass texture (tiled)
└── sounds/                # (Future: sound effects)
```
