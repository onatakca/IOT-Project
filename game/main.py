from .game_core import Game
from .menu import Menu
from .ble_gateway import BleGateway
from .ble_message import Message
import logging.config
import yaml
import pygame

with open("game/log_config.yaml", "r") as f:
    config = yaml.safe_load(f)
logging.config.dictConfig(config)
logger = logging.getLogger("root")

def main():
    #create and start ble
    message = Message()
    gateway = BleGateway(message)
    try:
        menu = Menu(message)
        choice, player = menu.run()
        #message from menu quit or start so it quits and starts from main
        if choice == "quit":
            return
        elif choice == "start":
            game = Game(player)

            print("=== CANOE ROWING GAME ===")
            print("Controls:")
            print("  UP    = Both paddles (go UP)")
            print("  LEFT  = Left paddle only (go UP and turn RIGHT)")
            print("  RIGHT = Right paddle only (go UP and turn LEFT)")
            print("  No key = Drift DOWN with current")
            print("\nGoal: Pass as many obstacles as possible to score points!")
            print("Keep rowing... If you hit the bottom, you lose!")
            print("\n  R = Restart")
            print("  Q = Quit")
            print("open config (in theory it configures the sensors but for now press l and r to configure them and then the strat is open)")
            print("=" * 50)
            game.run()
            
    finally:
        gateway.stop()
        pygame.quit()

if __name__ == "__main__":
    main()
