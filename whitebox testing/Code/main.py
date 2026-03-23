"""Entry point for running the MoneyPoly game.

This module handles basic user input for player setup and starts the game loop.
"""


from moneypoly.game import Game


def get_player_names():
    """Prompt the user for player names and return them as a list."""
    print("Enter player names separated by commas (minimum 2 players):")
    raw = input("> ").strip()
    names = [n.strip() for n in raw.split(",") if n.strip()]
    return names


def main():
    """Initialize the game and run it, handling setup and interruption errors."""
    names = get_player_names()
    try:
        game = Game(names)
        game.run()
    except KeyboardInterrupt:
        print("\n\n  Game interrupted. Goodbye!")
    except ValueError as exc:
        print(f"Setup error: {exc}")


if __name__ == "__main__":
    main()
