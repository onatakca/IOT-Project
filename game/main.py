from .game_core import Game
from .ble_gateway import BleGateway
from .ble_message import Message
import logging.config
import yaml
import queue

with open("game/log_config.yaml", "r") as f:
    config = yaml.safe_load(f)
logging.config.dictConfig(config)
logger = logging.getLogger("root")
from game.menu import Menu

def main():
    
    # Create and start the BLE gateway
    message = Message()
    gateway = BleGateway(message)
    
    game = Game(message)
    menu = Menu(message)
    menu.run() 
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