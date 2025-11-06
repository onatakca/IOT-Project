import logging
import threading
import time
from game.direction import Direction

logger = logging.getLogger("ble_message")

class Message:
    def __init__(self):
        self.LEFT = False
        self.RIGHT = False
        self.CONFIGURED = threading.Event()
        self._left_timestamp = 0
        self._right_timestamp = 0
        self._hold_duration = 0.5  # Hold paddle state for 500ms after detection

    def set_left_paddle(self):
        """Called when left paddle stroke is detected"""
        self.LEFT = True
        self._left_timestamp = time.time()

    def set_right_paddle(self):
        """Called when right paddle stroke is detected"""
        self.RIGHT = True
        self._right_timestamp = time.time()

    def update(self):
        """Update paddle states - auto-reset after hold duration"""
        current_time = time.time()

        if self.LEFT and (current_time - self._left_timestamp > self._hold_duration):
            self.LEFT = False

        if self.RIGHT and (current_time - self._right_timestamp > self._hold_duration):
            self.RIGHT = False

    def get_direction(self) -> Direction:
        # Update states before returning direction
        self.update()

        direction = "STOP"
        if self.LEFT and self.RIGHT:
            direction = "STRAIGHT"
        elif self.RIGHT:
            direction = "LEFT"
        elif self.LEFT:
            direction = "RIGHT"
        return Direction(self.LEFT, self.RIGHT, direction)