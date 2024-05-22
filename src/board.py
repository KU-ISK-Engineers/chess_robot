import chess
import numpy as np
import chess
from typing import Optional
from collections import namedtuple

SquareOffset = namedtuple('Offset', ['x', 'y'])
SQUARE_CENTER = SquareOffset(0, 0)

class BoardWithOffsets:
    def __init__(self, board: chess.Board, offsets: np.ndarray, perspective: chess.Color):
        self.chess_board = board
        self.offsets = offsets
        self.perspective = perspective

    def offset(self, square: chess.Square) -> SquareOffset:
        return self.offsets[chess.square_rank(square), chess.square_file(square)]
    
    def set_offset(self, square: chess.Square, offset: SquareOffset):
        self.offsets[chess.square_rank(square), chess.square_file(square)] = offset

    def remove_piece_at(self, square: chess.Square) -> Optional[chess.Piece]:
        piece = self.chess_board.remove_piece_at(square)
        self.set_offset(square, SQUARE_CENTER)
        return piece
    
    def set_piece_at(self, square: chess.Square, piece: chess.Piece, promoted: bool = False, offset: SquareOffset = SQUARE_CENTER):
        self.chess_board.set_piece_at(square, piece, promoted)
        self.set_offset(square, offset)

    def legal_moves(self):
        return self.chess_board.legal_moves