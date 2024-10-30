from typing import Optional
import platform
import argparse
import os

from src.ui.gui import gui_main
from src.core.game import Game

from dev.board import MockEngineBoardDetection
from dev.robot import patch_communication

import chess.engine
import chess.pgn
import logging


def setup_logging():
    log_dir = "logs"
    log_file = os.path.join(log_dir, "main.log")

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def load_engine(engine_path: Optional[str] = None):
    os_name = platform.system()
    arch = platform.machine()

    if not engine_path:
        if os_name == "Windows" and arch in ["x86_64", "AMD64"]:
            engine_path = "dev/stockfish_windows/stockfish-windows-x86-64-avx2.exe"
        elif os_name == "Linux" and arch == "x86_64":
            engine_path = "dev/stockfish_linux/stockfish-ubuntu-x86-64-avx2"
        else:
            raise SystemError(f"{arch} {os_name} is not supported for stockfish")

    logging.info(f"Selected stockfish path for {os_name}: {engine_path}")
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    return engine


def main(delay: float, engine_path: Optional[str]):
    game = None

    try:
        patch_communication(new_delay=delay)

        engine = load_engine(engine_path)

        detection = MockEngineBoardDetection(engine, delay=delay)

        game = Game(detection, engine)

        detection.attach_game(game)

        gui_main(game, splash=False)

    except Exception as e:
        logging.exception(e)

        if game:
            board = game.chess_board()
            logging.error(f"Game position PGN {board_to_pgn(board)}")
            logging.error(f"Last move FEN {board.fen()}")


def board_to_pgn(board: chess.Board) -> chess.pgn.Game:
    game = chess.pgn.Game()
    node = game

    for move in board.move_stack:
        node = node.add_variation(move)

    return game


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s %(levelname)s:%(name)s:%(message)s",
        datefmt="%x %X",
        level=logging.INFO,
        handlers=[logging.StreamHandler(), logging.FileHandler("log.txt")],
    )

    parser = argparse.ArgumentParser(
        description="A script to process delay and engine path."
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0,
        help="Optional delay from robot communication imitation.",
    )

    parser.add_argument(
        "--engine_path", type=str, default=None, help="The optional path to the engine."
    )

    args = parser.parse_args()
    main(delay=args.delay, engine_path=args.engine_path)
