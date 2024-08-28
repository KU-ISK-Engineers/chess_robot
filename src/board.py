import chess
from typing import Optional, NamedTuple
from abc import ABC, abstractmethod


class SquareOffset(NamedTuple):
    x: float
    y: float


SQUARE_CENTER = SquareOffset(0, 0)


# TODO: When perspective changes, offsets flip
class PhysicalBoard:
    def __init__(self, 
                 chess_board: Optional[chess.Board] = None, 
                 piece_offsets: Optional[list[SquareOffset]] = None, 
                 perspective: chess.Color = chess.WHITE):
        if chess_board is None:
            chess_board = chess.Board()

        if piece_offsets is None:
            piece_offsets = [SQUARE_CENTER for _ in range(64)] 

        self.chess_board = chess_board
        self.piece_offsets = piece_offsets
        self.perspective = perspective

    def piece_offset(self, square: chess.Square) -> SquareOffset:
        return self.piece_offsets[chess.square_rank(square) * 8 + chess.square_file(square)]

    def set_piece_offset(self, square: chess.Square, offset: SquareOffset):
        self.piece_offsets[chess.square_rank(square) * 8 + chess.square_file(square)] = offset


class BoardDetection(ABC):
    @abstractmethod
    def capture_board(self, perspective: chess.Color = chess.WHITE) -> Optional[PhysicalBoard]:
        pass


def boards_are_equal(board1: chess.Board, board2: chess.Board) -> bool:
    for square in chess.SQUARES:
        if board1.piece_at(square) != board2.piece_at(square):
            return False
    return True

