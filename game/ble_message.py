import logging
import threading
from game.direction import Direction

logger = logging.getLogger("ble_message")

class Message:
    def __init__(self):
        self.LEFT = False
        self.RIGHT = False
        self.same_cnt = 0
        self.buffer = 0
        self.last_dir = None
        self.CONFIGURED = threading.Event()
        
    def get_direction(self) -> Direction:
        """ if self.buffer > 0:
            self.buffer -=1
            direction = "STOP"
        else:
            direction = "STOP"
            if self.LEFT and self.RIGHT:
                direction = "STRAIGHT"
            elif self.RIGHT:
                direction = "LEFT"
            elif self.LEFT:
                direction = "RIGHT"

            if direction == self.last_dir:
                self.same_cnt += 1
            else:
                self.same_cnt = 0
            if (self.same_cnt >= 30):
                direction = "STOP"
                self.buffer = 15

            self.last_dir = direction"""
            
        direction = "STOP"
        if self.LEFT and self.RIGHT:
            direction = "STRAIGHT"
        elif self.RIGHT:
            direction = "LEFT"
        elif self.LEFT:
            direction = "RIGHT"
        return Direction(self.LEFT, self.RIGHT, direction)