from src.robot import setup_communication

from src.gui import gui_main
from src.game import Game

from dev.board import EngineBoardDetection

import chess.engine
import logging

def main():
    try:
        # TODO: Better logging
        logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', datefmt='%x %X', level=logging.INFO)
        
        setup_communication()

        engine = chess.engine.SimpleEngine.popen_uci("stockfish")

        detection = EngineBoardDetection(engine)

        game = Game(detection, engine)

        detection.attach_game(game)

        gui_main(game)

    except Exception as e:
        logging.exception(e)

if __name__ == "__main__":
    main()
