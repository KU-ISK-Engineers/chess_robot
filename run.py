from src.gui import gui_main
from src.communication import setup_communication, close_communication
from src.camera import CameraDetection
from src.game import Game, HUMAN, ROBOT
from src.board import BoardWithOffsets
from pypylon import pylon
from ultralytics import YOLO
import chess.engine
import logging

def setup_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate.SetValue(5)
    camera.ExposureAuto.SetValue('Continuous')
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("RGB8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    return camera

def setup_yolo():
    pass

def true_main():
    try:
        logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', datefmt='%x %X', level=logging.INFO)
        
        setup_communication()

        model = YOLO("chess_200.pt")
        camera = setup_camera()

        engine = chess.engine.SimpleEngine.popen_uci("../stockfish_pi/stockfish-android-armv8")

        detection = CameraDetection(camera, model)

        game = Game(detection, engine, BoardWithOffsets())


        if game.player == HUMAN:
            if game.player_made_move():
                # ejimas legalus
            else:
                # ejimas nelegalus
        elif game.player == ROBOT:
            if game.robot_makes_move():
                # ejimas padarytas
            else:
                # ejimas nepadarytas

        game.player == HUMAN
        game.check_game_over()

        game.depth = 12
        game.player = HUMAN


        new_board = BoardWithOffsets(perspective=chess.BLACK)
        game.reset_board(new_board, move_pieces=)

        game.board.perspective = chess.WHITE
        game.reset_board()

        gui_main(game)
    except Exception as e:
        logging.exception(e)
        close_communication()

def main():
    gui_main()

if __name__ == "__main__":
    main()