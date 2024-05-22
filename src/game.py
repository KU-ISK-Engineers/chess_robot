import chess
import chess.engine
from typing import Optional

from .camera import CameraDetection
from . import movement
from . import communication
from .board import BoardWithOffsets

HUMAN = 0
ROBOT = 1

# TODO: Detect perspective, optional board, percentages
# TODO: Detect initial position

class Game:
    def __init__(self, 
                 detection: CameraDetection,
                 engine: chess.engine.SimpleEngine,
                 board: BoardWithOffsets, 
                 depth: int = 4,
                 player: int = HUMAN,
                 move_pieces: bool = False) -> None:
        self.detection = detection
        self.board = board
        self.player = player
        self.depth = depth
        self.engine = engine

        self.reset_board(board, player, move_pieces=move_pieces)

    def reset_board(self, 
                    new_board: BoardWithOffsets, 
                    player: int = HUMAN,
                    move_pieces: bool = False):

        if move_pieces:
            if self.board is None:
                # TODO: Maybe flip board if perspectives differ
                self.board = self.detection.capture_board(perspective=new_board.perspective)

            response = movement.reset_board(self.board, new_board.chess_board, new_board.perspective)
            if response != communication.RESPONSE_SUCCESS:
                raise RuntimeError("Robot hand timed out")
                
        self.player = player

    def robot_makes_move(self, move: Optional[chess.Move] = None) -> Optional[chess.Move]:
        if move is not None:
            result = self.engine.play(self.board, chess.engine.Limit(depth=self.depth))
            move = result.move

        if not self.validate_move(move):
            return 
        
        response = movement.reflect_move(self.board, move)
        if response != communication.RESPONSE_SUCCESS:
            return
        
        # TODO: Make a new image to ensure no one fucked up with the movement
        
        self.player = HUMAN
        self.board.push(move)
        return move
    
    def chess_board(self) -> chess.Board:
        return self.board.chess_board
    
    def player_made_move(self) -> Optional[chess.Move]:
        """Assume player has already made a move"""
        prev_board = self.board
        new_board = self.detection.capture_board(perspective=self.board)
        move = movement.identify_move(prev_board.chess_board, new_board.chess_board)

        if not self.validate_move(move):
            return None
        
        self.player = ROBOT
        self.board.push(move, to_offset=new_board.offset(move.to_square))
        return move

    def validate_move(self, move: Optional[chess.Move]) -> bool:
        return move in self.board.legal_moves
    
    def check_game_over(self) -> Optional[str]:
        """Check if the game is over and return the result."""
        if self.board.chess_board.is_game_over():
            return self.board.chess_board.result()
        return None

# ----- TESTING ---

from ultralytics import YOLO
from pypylon import pylon

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

def main():
    # if len(sys.argv) != 2:
    #     print("Usage: python script.py path_to_model")
    #     sys.exit(1)

    # model = YOLO(sys.argv[1])
    model = YOLO("../training/chess_200.pt")
    camera = setup_camera()

    engine = chess.engine.SimpleEngine.popen_uci("../stockfish_pi/stockfish-android-armv8")

    detection = CameraDetection(camera, model)

    communication.setup_communication()

    board = BoardWithOffsets()
    board = chess.Board()

    game = Game(detection, engine, board)

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

if __name__ == "__main__":
    main()
