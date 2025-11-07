import pygame
from game.ble_message import Message
from game.direction import Direction
import time

class InputScheme:
    def get_direction(self) -> Direction:
        pass

class BLEScheme(InputScheme):
    def __init__(self, ble_message: Message):
        self.ble_message = ble_message
        ble_message.CONFIGURED.set()

    def get_direction(self) -> Direction:
        return self.ble_message.get_direction()
    
class KeyboardScheme(InputScheme):
    def __init__(self, left_key: int, right_key:int):
        self.left_key = left_key
        self.right_key = right_key
        self.last_call = None
        self.last_input = Direction(False, False, "STOP")

    def get_direction(self) -> Direction:
        keys = pygame.key.get_pressed()
        
        direction = "STOP"
        if keys[self.left_key] & keys[self.right_key]:
            direction = "STRAIGHT"
        elif keys[self.left_key]:
            direction = "RIGHT"
        elif keys[self.right_key]:
            direction = "LEFT"
        
        # Add delay like BLE
        current_time = time.time()
        if self.last_call is not None and current_time - self.last_call < 2:
            return self.last_input
        
        if direction != "STOP":
            self.last_call = current_time
            self.last_input = Direction(keys[self.left_key], keys[self.right_key], direction)
        return Direction(keys[self.left_key], keys[self.right_key], direction)