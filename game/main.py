from .game_core import Game

def main():
    game = Game()
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