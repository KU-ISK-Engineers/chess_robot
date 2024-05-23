from src.gui import gui_main
from src.communication import setup_communication
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

def test_game(game: Game):
    while True:
        if game.player == ROBOT:
            move = game.robot_makes_move()
            print(f"Robot made move: {move}")
        else:
            move = game.player_made_move()
            print(f"Player made move: {move}")
        
        result = game.check_game_over()
        if result:
            print(f"Game over with result: {result}")
            break

def true_main():
    try:
        logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s:%(message)s', datefmt='%x %X', level=logging.INFO)
        
        setup_communication()

        model = YOLO("chess_200.pt")
        camera = setup_camera()

        engine = chess.engine.SimpleEngine.popen_uci("stockfish8/Stockfish-sf_15/src/stockfish")

        detection = CameraDetection(camera, model)

        game = Game(detection, engine)

        #test_game(game)

        gui_main(game)

    except Exception as e:
        logging.exception(e)

if __name__ == "__main__":
    true_main()