import chess
import chess.engine
from typing import Optional
import time
from ..scripts.camera import CameraDetection
from . import movement
from . import communication
from ..scripts.board import BoardWithOffsets
from .detection import visualise_chessboard

HUMAN = 0
ROBOT = 1

# TODO: Detect perspective, optional board, percentages
# TODO: Detect initial position

class Game:
    def __init__(self, 
                 detection: CameraDetection,
                 engine: chess.engine.SimpleEngine,
                 perspective: chess.Color = chess.WHITE,
                 depth: int = 4,
                 move_pieces: bool = False) -> None:
        self.detection = detection
        self.depth = depth
        self.engine = engine

        self.board = None
        self.player = None
        self.resigned = False

        self.reset_board(perspective, move_pieces=move_pieces)
        self.set_depth(depth)

    def set_depth(self, depth: int = 4):
        self.depth = depth
        self.engine.configure({"Skill Level": depth})
        #elo = int(300 + 200 * (depth - 1))
        #self.engine.configure({"UCI_LimitStrength": True, "UCI_Elo": elo})

    def reset_board(self, 
                    perspective: chess.Color, 
                    move_pieces: bool = False):
        if move_pieces:
            response = self._reshape_board(self.board.chess_board, self.board.perspective)
            if response != communication.RESPONSE_SUCCESS:
                raise RuntimeError("Robot hand timed out")
        else:
            self.board = BoardWithOffsets(perspective=perspective)

        if self.board.perspective == chess.WHITE:
            self.player = HUMAN
        else:
            self.player = ROBOT

        self.resigned = False
        communication.issue_command("99 99 99 99")

    def robot_makes_move(self, move: Optional[chess.Move] = None) -> Optional[chess.Move]:
        visualise_chessboard(self.board)

        new_board = self.detection.capture_board(perspective=self.board.perspective)
        self.board.offsets = new_board.offsets

        if not boards_are_equal(self.board.chess_board, new_board.chess_board):
            print('Boards are not the same, waiting for the board to reposition to correct place')
            return 

        if move is None:
            result = self.engine.play(self.board.chess_board, chess.engine.Limit(depth=self.depth))
            move = result.move

        if not self.validate_move(move):
            print(move.uci())
            return 
        
        response = movement.reflect_move(self.board, move)
        if response != communication.RESPONSE_SUCCESS:
            return
        
        # TODO: Make a new image to ensure no one fucked up with the movement
        
        self.player = HUMAN
        self.board.push(move)
        self._update_move()
        return move
    
    def chess_board(self) -> chess.Board:
        return self.board.chess_board
    
    def player_made_move(self) -> Optional[chess.Move]:
        visualise_chessboard(self.board)

        move1, board1 = self._player_made_move()
        if move1 is None:
            return None

        time.sleep(0.3)
        move2, board2 = self._player_made_move()
        if move2 is None:
            return None

        if move1 != move2:
            return None

        """Assume player has already made a move"""
        # prev_board = self.board
        # new_board = self.detection.capture_board(perspective=self.board.perspective)
        # move = movement.identify_move(prev_board.chess_board, new_board.chess_board)

        #if not self.validate_move(move):
        #    return None
        
        self.player = ROBOT
        self.board.push(move1, to_offset=board1.offset(move1.to_square))
        self._update_move()
        return move1

    def _player_made_move(self) -> Optional[chess.Move]:
        prev_board = self.board
        new_board = self.detection.capture_board(perspective=self.board.perspective)
        move = movement.identify_move(prev_board.chess_board, new_board.chess_board)

        if not self.validate_move(move):
            return None, None

        return move, new_board

    def validate_move(self, move: Optional[chess.Move]) -> bool:
        return move in self.board.legal_moves()
    
    def check_game_over(self) -> str:
        """Check if the game is over and return the result."""
        if not self.resigned:
            return self.board.chess_board.result()
        
        return "resigned"
    
    def resign_player(self):
        self.resigned = True
    
    def _reshape_board(self, expected_board: chess.Board, perspective: chess.Color):
        done = False
        current_board = self.detection.capture_board(perspective=perspective)

        while not done:
            current_board = self.detection.capture_board(perspective=perspective)
            response, done = movement.reset_board_v2(current_board, expected_board, perspective)
            if response != communication.RESPONSE_SUCCESS:
                return response

        self.board.chess_board = current_board.chess_board
        self.board.offsets = current_board.offsets

        return communication.RESPONSE_SUCCESS

    def _update_move(self):
        if self.board.chess_board.is_game_over():
            communication.issue_command("99 99 99 99")
    
def boards_are_equal(board1: chess.Board, board2: chess.Board) -> bool:
    for square in chess.SQUARES:
        if board1.piece_at(square) != board2.piece_at(square):
            return False
    return True

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
