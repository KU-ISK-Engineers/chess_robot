import logging
import os
import argparse
import chess.engine

from src.mocks.board_capture import SimulatedBoardCapture
from src.mocks.piece_mover import SimulatedPieceMover
from src.ui.gui import gui_main
from src.core.game import Game


def setup_logging():
    """Configures logging settings to output to both console and log file."""
    log_dir = "logs"
    log_file = os.path.join(log_dir, "simulated.log")
    os.makedirs(log_dir, exist_ok=True)

    level = logging.INFO
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s")

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def parse_arguments():
    """Parses command-line arguments for the chess-playing robot system."""
    parser = argparse.ArgumentParser(description="Run the chess-playing robot system.")
    parser.add_argument(
        "--engine_path",
        type=str,
        default="stockfish",
        help="Path to the chess engine executable",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main():
    args = parse_arguments()
    setup_logging()

    try:
        # Initialize simulated hardware components
        piece_mover = SimulatedPieceMover()
        logging.info("Simulated piece mover initialized.")

        # Set up the chess engine with context management for automatic cleanup
        with chess.engine.SimpleEngine.popen_uci(args.engine_path) as engine:
            logging.info("Chess engine started from %s", args.engine_path)

            # Initialize the simulated board capture system
            board_capture = SimulatedBoardCapture(engine=engine)
            logging.info("Simulated board capture initialized.")

            # Start the game with the simulated components
            game = Game(
                board_capture=board_capture, piece_mover=piece_mover, engine=engine, 
            )
            logging.info("Game initialized, launching GUI...")
            
            board_capture.track_game(game)

            # Launch the GUI
            gui_main(game, splash=False)

    except chess.engine.EngineError as e:
        logging.exception("Failed to start the chess engine: %s", e)
    except FileNotFoundError as e:
        logging.exception("File not found: %s", e)
    except Exception as e:
        logging.exception("An unexpected error occurred: %s", e)


if __name__ == "__main__":
    main()
