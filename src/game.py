import chess
import chess.engine
from typing import Optional
from .board import PhysicalBoard, BoardDetection, boards_are_equal
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

        self.board = PhysicalBoard(chess_board=board, perspective=perspective)

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

        self.board = PhysicalBoard(chess_board=board, perspective=perspective)

        fen = self.board.chess_board.fen()
        logger.info(f'Resetting board {'white' if perspective == chess.WHITE else 'black'} perspective FEN {fen}')

        if move_pieces and not self._reshape_board(self.board):
            if not self._reshape_board(self.board):
                raise RuntimeError("Failed to reshape the board")

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
            return None

        if not boards_are_equal(self.board.chess_board, new_board.chess_board):
            logger.info('Detected board does not match previous legal board for robot to move, waiting to reposition')
            return None

        if move is None:
            result = self.engine.play(self.board.chess_board, chess.engine.Limit(depth=self.depth))
            move = result.move

        logger.info("Robot making move %s", move and move.uci())

        if not move or move not in self.board.chess_board.legal_moves:
            logger.error("Invalid robot move: %s", move and move.uci())
            return None

        self.board.piece_offsets = new_board.piece_offsets
        if not movement.reflect_move(self.board, move):
            return None
        
        self.player = HUMAN
        self.board.chess_board.push(move)
        return move
    
    def player_made_move(self) -> tuple[Optional[chess.Move], bool]:
        new_board = self.detection.capture_board(perspective=self.board.perspective)
        if not new_board:
            return None, False

        move, legal = movement.identify_move(self.board.chess_board, new_board.chess_board)
        if move:
            logger.info(f"Player made {'legal' if legal else 'illegal'} move {move.uci()}")
            if legal:
                self.board.chess_board.push(move)
                self.board.piece_offsets = new_board.piece_offsets
                self.player = ROBOT

        return move, legal

    def result(self) -> str:
        # TODO: Win / lose not on white or black, but on human or robot
        if not self.resigned:
            return self.board.chess_board.result()
        
        return "resigned"
    
    def resign_player(self):
        self.resigned = True

    def chess_board(self) -> chess.Board:
        return self.board.chess_board

    def _reshape_board(self, expected_board: PhysicalBoard) -> bool:
        logger.info('Reshaping game board')

        current_board = self.board

        done = False
        while not done:
            current_board = self.detection.capture_board(perspective=expected_board.perspective)
            if not current_board:
                continue

            moved, done = movement.iter_reset_board(self.board, expected_board)
            if not moved:
                break

        if done and current_board:
            self.board = current_board
        return done
    
