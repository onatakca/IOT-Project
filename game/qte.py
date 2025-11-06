import pygame
import random
from enum import Enum
from .settings import *

class QTEType(Enum):
    """Types of QTE prompts"""
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BOTH = "BOTH"

class QTEResult(Enum):
    """QTE completion results"""
    PERFECT = "PERFECT"
    GOOD = "GOOD"
    MISS = "MISS"
    PENDING = "PENDING"

class QTE:
    """Quick Time Event - prompts player to row within a time window"""

    def __init__(self, qte_type: QTEType, spawn_time: int, warning_duration: int = 2000,
                 active_duration: int = 1500):
        """
        Args:
            qte_type: Type of QTE (LEFT/RIGHT/BOTH)
            spawn_time: Game time when QTE was created (pygame.time.get_ticks())
            warning_duration: Time to show warning before active window (ms)
            active_duration: Time window for player to respond (ms)
        """
        self.qte_type = qte_type
        self.spawn_time = spawn_time
        self.warning_duration = warning_duration
        self.active_duration = active_duration
        self.result = QTEResult.PENDING
        self.activated = False
        self.activation_time = None

    def get_phase(self, current_time: int) -> str:
        """Returns the current phase: 'warning', 'active', or 'finished'"""
        elapsed = current_time - self.spawn_time

        if elapsed < self.warning_duration:
            return "warning"
        elif elapsed < self.warning_duration + self.active_duration:
            return "active"
        else:
            return "finished"

    def get_progress(self, current_time: int) -> float:
        """Returns progress through active window (0.0 to 1.0)"""
        elapsed = current_time - self.spawn_time - self.warning_duration
        if elapsed < 0:
            return 0.0
        return min(1.0, elapsed / self.active_duration)

    def check_input(self, current_time: int, left_paddle: bool, right_paddle: bool) -> bool:
        """
        Check if correct input was provided during active window.
        Returns True if input matches QTE type.
        """
        phase = self.get_phase(current_time)
        if phase != "active" or self.activated:
            return False

        # Check if correct paddles are active
        correct_input = False
        if self.qte_type == QTEType.LEFT and left_paddle and not right_paddle:
            correct_input = True
        elif self.qte_type == QTEType.RIGHT and right_paddle and not left_paddle:
            correct_input = True
        elif self.qte_type == QTEType.BOTH and left_paddle and right_paddle:
            correct_input = True

        if correct_input:
            self.activated = True
            self.activation_time = current_time

            # Calculate result based on timing
            progress = self.get_progress(current_time)
            if progress < 0.3:
                self.result = QTEResult.PERFECT
            elif progress < 0.7:
                self.result = QTEResult.GOOD
            else:
                self.result = QTEResult.GOOD
            return True

        return False

    def finalize(self, current_time: int):
        """Mark QTE as missed if not completed"""
        if self.get_phase(current_time) == "finished" and not self.activated:
            self.result = QTEResult.MISS

    def is_finished(self, current_time: int) -> bool:
        """Returns True if QTE is complete (success or failure)"""
        return self.get_phase(current_time) == "finished" or self.activated

    def draw(self, screen: pygame.Surface, current_time: int):
        """Draw the QTE prompt on screen"""
        phase = self.get_phase(current_time)

        if phase == "finished" and not self.activated:
            phase = "finished"

        # Fonts
        try:
            prompt_font = pygame.font.SysFont("Impact", 72)
            small_font = pygame.font.SysFont("Bahnschrift", 36)
        except:
            prompt_font = pygame.font.SysFont(None, 72)
            small_font = pygame.font.SysFont(None, 36)

        # Center position
        center_x = SCREEN_WIDTH // 2
        center_y = 150

        if phase == "warning":
            # Show warning with pulsing effect
            elapsed = current_time - self.spawn_time
            pulse = abs(pygame.math.Vector2(0, 0).distance_to(
                pygame.math.Vector2(elapsed % 500, 0))) / 500
            alpha = int(150 + 105 * pulse)

            # Get prompt text
            if self.qte_type == QTEType.LEFT:
                text = "ROW LEFT!"
                color = (255, 100, 100)
            elif self.qte_type == QTEType.RIGHT:
                text = "ROW RIGHT!"
                color = (100, 100, 255)
            else:
                text = "ROW BOTH!"
                color = (255, 255, 100)

            # Draw warning text
            warning_surf = small_font.render("GET READY", True, (255, 255, 255))
            screen.blit(warning_surf, warning_surf.get_rect(center=(center_x, center_y - 40)))

            # Draw prompt (no subtext)
            prompt_surf = prompt_font.render(text, True, color)
            screen.blit(prompt_surf, prompt_surf.get_rect(center=(center_x, center_y + 20)))

        elif phase == "active":
            # Show active prompt with progress bar
            if self.qte_type == QTEType.LEFT:
                text = "ROW LEFT!"
                color = (255, 50, 50)
            elif self.qte_type == QTEType.RIGHT:
                text = "ROW RIGHT!"
                color = (50, 50, 255)
            else:
                text = "ROW BOTH!"
                color = (255, 255, 50)

            # Draw prompt (no subtext)
            prompt_surf = prompt_font.render(text, True, color)
            screen.blit(prompt_surf, prompt_surf.get_rect(center=(center_x, center_y)))

            # Draw progress bar
            bar_width = 400
            bar_height = 20
            bar_x = center_x - bar_width // 2
            bar_y = center_y + 90

            # Background
            pygame.draw.rect(screen, (50, 50, 50),
                           (bar_x, bar_y, bar_width, bar_height), border_radius=10)

            # Progress fill (depleting)
            progress = self.get_progress(current_time)
            fill_width = int(bar_width * (1.0 - progress))

            # Color based on time remaining
            if progress < 0.5:
                fill_color = (50, 255, 50)  # Green
            elif progress < 0.8:
                fill_color = (255, 255, 50)  # Yellow
            else:
                fill_color = (255, 50, 50)  # Red

            pygame.draw.rect(screen, fill_color,
                           (bar_x, bar_y, fill_width, bar_height), border_radius=10)

            # Border
            pygame.draw.rect(screen, (255, 255, 255),
                           (bar_x, bar_y, bar_width, bar_height), 2, border_radius=10)


class QTEManager:
    """Manages multiple QTEs and spawning logic"""

    def __init__(self, difficulty: str = "normal"):
        self.qtes = []
        self.difficulty = difficulty
        self.last_spawn_time = 0
        self.spawn_interval = 4000  # 4 seconds between QTEs (base)

        # Adjust spawn rate based on difficulty
        if difficulty == "easy":
            self.spawn_interval = 5000  # 5 seconds
        elif difficulty == "hard":
            self.spawn_interval = 3000  # 3 seconds

    def spawn_qte(self, current_time: int, force_type: QTEType = None):
        """Spawn a new QTE"""
        if force_type:
            qte_type = force_type
        else:
            # Random QTE type
            qte_type = random.choice([QTEType.LEFT, QTEType.RIGHT, QTEType.BOTH])

        # Adjust timing windows based on difficulty
        if self.difficulty == "easy":
            warning = 2500
            active = 2000
        elif self.difficulty == "hard":
            warning = 1500
            active = 1000
        else:
            warning = 2000
            active = 1500

        qte = QTE(qte_type, current_time, warning, active)
        self.qtes.append(qte)
        self.last_spawn_time = current_time

    def should_spawn_qte(self, current_time: int) -> bool:
        """Check if it's time to spawn a new QTE"""
        if not self.qtes:
            return True

        # Only spawn if last QTE is finished
        last_qte = self.qtes[-1]
        if last_qte.is_finished(current_time):
            elapsed = current_time - self.last_spawn_time
            return elapsed >= self.spawn_interval

        return False

    def update(self, current_time: int, left_paddle: bool, right_paddle: bool):
        """Update all QTEs and check for input"""
        for qte in self.qtes:
            if qte.get_phase(current_time) == "active":
                qte.check_input(current_time, left_paddle, right_paddle)
            qte.finalize(current_time)

        # Remove finished QTEs (keep last few for feedback display)
        self.qtes = [qte for qte in self.qtes
                    if current_time - qte.spawn_time < 6000]  # Keep for 6 seconds

    def get_active_qte(self, current_time: int):
        """Get the currently active QTE (if any)"""
        for qte in self.qtes:
            phase = qte.get_phase(current_time)
            if phase in ["warning", "active"]:
                return qte
        return None

    def get_last_result(self) -> QTEResult:
        """Get the result of the most recent completed QTE"""
        if self.qtes and self.qtes[-1].result != QTEResult.PENDING:
            return self.qtes[-1].result
        return None

    def draw(self, screen: pygame.Surface, current_time: int):
        """Draw active QTE prompts"""
        active_qte = self.get_active_qte(current_time)
        if active_qte:
            active_qte.draw(screen, current_time)
