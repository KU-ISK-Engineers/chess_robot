import chess
import chess.engine
from typing import Optional
from .board import RealBoard, BoardDetection, boards_are_equal
from . import robot
from . import movement
import logging

logger = logging.getLogger(__name__)

HUMAN = 0
ROBOT = 1


class Game:
    def __init__(self, 
                 detection: BoardDetection,
                 engine: chess.engine.SimpleEngine,
                 board: Optional[chess.Board] = None,
                 perspective: chess.Color = chess.WHITE,
                 depth: int = 4) -> None:
        self.detection = detection
        self.depth = depth
        self.engine = engine

        if not board:
            board = chess.Board()

        self.board = RealBoard(board=board, perspective=perspective)

        if perspective == chess.WHITE:
            self.player = HUMAN
        else:
            self.player = ROBOT

        self.resigned = False
        robot.reset_state()

    def reset_board(self,
                    board: Optional[chess.Board] = None,
                    perspective: Optional[chess.Color] = None, 
                    move_pieces: bool = False):
        if perspective is None:
            perspective = self.board.perspective

        if not board:
            board = chess.Board()

        self.board = RealBoard(board=board, perspective=perspective)

        fen = self.board.chess_board.fen()
        logger.info(f'Resetting board {'white' if perspective == chess.WHITE else 'black'} perspective FEN {fen}')

        if move_pieces:
            response = self._reshape_board(self.board)
            if response != robot.COMMAND_SUCCESS:
                raise RuntimeError("Robot hand timed out")

        if self.board.perspective == chess.WHITE:
            self.player = HUMAN
        else:
            self.player = ROBOT

        self.resigned = False
        robot.reset_state()

    def set_depth(self, depth: int = 4):
        # FIXME: Does not work, rename method, fix logic
        self.depth = depth
        self.engine.configure({"Skill Level": depth})

    def robot_makes_move(self, move: Optional[chess.Move] = None) -> Optional[chess.Move]:
        new_board = self.detection.capture_board(perspective=self.board.perspective)
        if not new_board:
            return

        if not boards_are_equal(self.board.chess_board, new_board.chess_board):
            logger.info('Detected board does not match previous legal board for robot to move, waiting to reposition')
            return 

        if move is None:
            result = self.engine.play(self.board.chess_board, chess.engine.Limit(depth=self.depth))
            move = result.move

        logger.info("Robot making move %s", move.uci())

        if not move or not self.validate_move(move):
            logger.error("Invalid robot move: %s", move.uci())
            return 

        self.board.offsets = new_board.offsets
        response = movement.reflect_move(self.board, move)
        if response != robot.COMMAND_SUCCESS:
            return
        
        self.player = HUMAN
        self.board.push(move)
        return move
    
    def player_made_move(self) -> tuple[Optional[chess.Move], bool]:
        new_board = self.detection.capture_board(perspective=self.board.perspective)
        if not new_board:
            return None, False

        move, legal = movement.identify_move(self.board.chess_board, new_board.chess_board)
        if move:
            logger.info(f"Player made {'legal' if legal else 'illegal'} move {move.uci()}")
            if legal:
                self.player = ROBOT
                self.board.push(move, to_offset=new_board.offset(move.to_square))

        return move, legal

    def validate_move(self, move: Optional[chess.Move]) -> bool:
        # TODO: Check if resigned here?
        return move in self.board.legal_moves
    
    def result(self) -> str:
        # TODO: Win / lose not on white or black, but on human or robot
        if not self.resigned:
            return self.board.result()
        
        return "resigned"
    
    def resign_player(self):
        self.resigned = True

    def chess_board(self) -> chess.Board:
        return self.board.chess_board

    def _reshape_board(self, expected_board: RealBoard) -> int:
        done = False
        current_board = self.board
        logger.info('Reshaping game board')

        while not done:
            current_board = self.detection.capture_board(perspective=expected_board.perspective)
            if not current_board:
                continue

            response, done = movement.iter_reset_board(current_board, expected_board)
            if response != robot.COMMAND_SUCCESS:
                return response

        self.board.chess_board = current_board.chess_board
        self.board.offsets = current_board.offsets
        return robot.COMMAND_SUCCESS
    
