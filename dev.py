from src.gui import gui_main
from src.game import Game

from dev.board import EngineBoardDetection
from dev.robot import patch_communication

import chess.engine
import logging
from typing import Optional
import platform
import argparse

def load_engine(engine_path: Optional[str] = None):
    os_name = platform.system()
    if not engine_path:
        if os_name == 'Windows':
            engine_path = 'dev/stockfish_windows/stockfish-windows-x86-64-avx2.exe'
        elif os_name == 'Linux':
            engine_path = 'dev/stockfish_linux/stockfish-ubuntu-x86-64-avx2'
        else:
            raise SystemError(f"{os_name} is not supported for stockfish")

    logging.info(f"Selected stockfish path for {os_name}: {engine_path}")
    engine = chess.engine.SimpleEngine.popen_uci(engine_path)
    return engine

def main(delay: float, engine_path: Optional[str]):
    try:
        # TODO: Better logging
        logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', datefmt='%x %X', level=logging.INFO)
        
        patch_communication(new_delay = delay)

        engine = load_engine(engine_path)

        detection = EngineBoardDetection(engine)

        game = Game(detection, engine)

        detection.attach_game(game)

        gui_main(game, splash=False)

    except Exception as e:
        logging.exception(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A script to process delay and engine path.")

    parser.add_argument(
        '--delay',
        type=float,
        default=0,
        help="Optional delay from robot communication immitation."
    )

    parser.add_argument(
        '--engine_path',
        type=str,
        default=None,
        help="The optional path to the engine."
    )

    args = parser.parse_args()
    main(delay=args.delay, engine_path=args.engine_path)
