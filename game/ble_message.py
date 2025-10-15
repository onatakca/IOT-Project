import logging
import threading

logger = logging.getLogger("ble_message")

class Message:
    def __init__(self):
        self.LEFT = False
        self.RIGHT = False
        self.CONFIGURED = threading.Event()
        
    def get_direction(self) -> str:
        if self.LEFT and not self.RIGHT:
            return "LEFT"
        elif self.RIGHT and not self.LEFT:
            return "RIGHT"
        elif not self.LEFT and not self.RIGHT:
            return "STOP"
        else:
            return "STRAIGHT"
        