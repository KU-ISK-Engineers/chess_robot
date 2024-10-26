import logging
import os

from ultralytics import YOLO
import chess.engine

from src.communication.tcp_robot import TCPRobotHand
from src.detection.camera import CameraBoardDetection, default_camera_setup

from src.ui.gui import gui_main
from src.core.game import Game



def setup_logging():
    log_dir = "logs"
    log_file = os.path.join(log_dir, "main.log")

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s:%(name)s:%(message)s"
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


# TODO: CLI Arguments, Read from environment args
def main():
    setup_logging()
    
    robot_hand = TCPRobotHand()

    model = YOLO("models/chess_200.pt")

    engine = chess.engine.SimpleEngine.popen_uci("stockfish")
    camera = default_camera_setup()

    detection = CameraBoardDetection(model, camera=camera)

    game = Game(detection, robot_hand, engine)

    gui_main(game)


if __name__ == "__main__":
    main()
