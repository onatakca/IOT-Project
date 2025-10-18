# settings.py
import json, os
from dataclasses import dataclass, asdict

BASE_DIR    = os.path.dirname(__file__)
IMAGES_DIR  = os.path.join(BASE_DIR, "images")
SOUNDS_DIR  = os.path.join(BASE_DIR, "sounds")
SETTINGS_JSON = os.path.join(BASE_DIR, "settings.json")

SCREEN_WIDTH, SCREEN_HEIGHT = 900, 600
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
UI_BG  = (18, 44, 90)
BTN_BG = (236, 236, 236)
BTN_OUT= (25, 25, 25)
ACCENT = (40, 140, 255)

CANOE_WIDTH, CANOE_HEIGHT = 55, 100
OBSTACLE_WIDTH, OBSTACLE_HEIGHT = 80, 80

BASE_SPAWN_INTERVAL = 1.0
BASE_OBSTACLE_SPEED = 6.0

@dataclass
class UserSettings:
    music_vol: int = 60      # 0–100
    sfx_vol:   int = 80      # 0–100
    players:   int = 1       # 1..3
    difficulty: str = "normal"  # easy|normal|hard
    player_names: list | None = None  # ["Alice","Bob",""]

    def __post_init__(self):
        if self.player_names is None:
            self.player_names = ["", "", ""]

def load_settings() -> "UserSettings":
    try:
        if os.path.exists(SETTINGS_JSON):
            with open(SETTINGS_JSON, "r") as f:
                d = json.load(f)
            return UserSettings(**d)
    except Exception:
        pass
    return UserSettings()

def save_settings(s: "UserSettings"):
    with open(SETTINGS_JSON, "w") as f:
        json.dump(asdict(s), f, indent=2)

def difficulty_factors(name: str):
    name = (name or "normal").lower()
    if name == "easy":   return (1.4, 0.9)  # fewer, slower
    if name == "hard":   return (0.6, 1.2)  # more, faster
    return (1.0, 1.0)    # normal
