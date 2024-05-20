import chess
import chess.engine
from typing import Optional

from .camera import CameraDetection
from . import movement
from .communication_ssh import RESPONSE_SUCCESS

PLAYER = 0
ROBOT = 1

class Game:
    def __init__(self, 
                 camera: CameraDetection,
                 engine: chess.engine.SimpleEngine,
                 board: Optional[chess.Board] = None, 
                 color: Optional[chess.Color] = None,
                 depth: int = 4,
                 player: int = PLAYER) -> None:
        self.camera = camera

        self.board = None
        self.player = None
        self.depth = depth
        self.engine = engine
        self.color_picked = False

        self.reset_board(board, color, player)

    def reset_board(self, 
                    new_board: Optional[chess.Board] = None, 
                    color: Optional[chess.Color] = None, 
                    player: int = PLAYER,
                    move_pieces: bool = False):
        if move_pieces:
            if new_board is None:
                raise ValueError("Board must be given for it to be reset to")
            
            if self.board is None:
                self.board = self.camera.capture_board()

            response = movement.reset_board(self.board, new_board)
            if response != RESPONSE_SUCCESS:
                raise RuntimeError("Robot hand timed out")
                
        if new_board is None:
            self.board = self.camera.capture_board()
        else:
            self.board = new_board

        if color is not None:
            self.board.turn = color
            self.color_picked = True
        else:
            self.color_picked = False

        self.player = player

    def robot_makes_move(self, move: Optional[chess.Move] = None) -> Optional[chess.Move]:
        if move is not None:
            result = self.engine.play(self.board, chess.engine.Limit(depth=self.depth))
            move = result.move

        if not self.validate_move(move):
            return 
        
        response = movement.make_move(self.board, move)
        if response != RESPONSE_SUCCESS:
            raise RuntimeError("Robot hand timed out")
        
        # TODO: Make a new image to ensure no one fucked up with the movement
        
        self.player = PLAYER
        self.board.push(move)
        return move
    
    def player_made_move(self) -> Optional[chess.Move]:
        """Assume player has already made a move"""
        new_board = self.camera.capture_board()
        move = movement.identify_move(self.prev_board, new_board)

        if not self.validate_move(move):
            return 
        
        self.player = ROBOT
        self.board.push(move)
        return move

    def validate_move(self, move: Optional[chess.Move]) -> bool:
        if not self.color_picked:
            color = self.board.piece_at(move.from_square).color
            self.board.turn = color

        if not move:
            return False # no move found
        
        if not move in self.board.legal_moves:
            return False # Invalid move in board
        
        return True



