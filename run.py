import logging
import os
import argparse

from ultralytics import YOLO
import chess.engine
from src.communication.tcp_robot import TCPRobotHand
from src.detection.basler_camera import (
    CameraBoardCapture,
    Orientation,
)
from src.ui.gui import gui_main
from src.core.game import Game


def setup_logging() -> None:
    log_dir = "logs"
    log_file = os.path.join(log_dir, "run.log")
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

    logging.getLogger("ultralytics").setLevel(logging.CRITICAL)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the chess-playing robot system.")
    parser.add_argument(
        "--ip", type=str, default="192.168.1.6", help="IP address for the robot hand"
    )
    parser.add_argument(
        "--port", type=int, default=6001, help="Port for the robot hand"
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default="training/models/yolo8_200.onnx",
        help="Path to YOLO model",
    )
    parser.add_argument(
        "--engine_path",
        type=str,
        default="stockfish",
        help="Path to the chess engine executable",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    setup_logging()
    args = parse_arguments()

    try:
        robot_hand = TCPRobotHand(ip=args.ip, port=args.port, timeout=30)
        model = YOLO(args.model_path)
        board_capture = CameraBoardCapture(
            model=model,
            physical_orientation=Orientation.HUMAN_BOTTOM,
            max_piece_offset=0.99,
            timeout=5000,
            visualize_board=args.debug,
        )

        with chess.engine.SimpleEngine.popen_uci(args.engine_path) as engine:
            logging.info("Chess engine started from %s", args.engine_path)

            game = Game(
                board_capture=board_capture, piece_mover=robot_hand, engine=engine
            )
            logging.info("Game initialized, launching GUI...")
            gui_main(game)

    except chess.engine.EngineError:
        logging.exception("Failed to start chess engines")
    except FileNotFoundError:
        logging.exception("File not found")
    except Exception:
        logging.exception("Unexpected error occurred")


if __name__ == "__main__":
    main()
