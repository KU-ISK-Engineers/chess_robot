import chess
import numpy as np
import chess
from typing import Optional
from collections import namedtuple

SquareOffset = namedtuple('Offset', ['x', 'y'])
SQUARE_CENTER = SquareOffset(0, 0)

class BoardWithOffsets:
    def __init__(self, board: chess.Board = None, offsets: np.ndarray = None, perspective: chess.Color = chess.WHITE):
        if board is None:
            board = chess.Board()
        if offsets is None:
            offsets = np.array([[SQUARE_CENTER for _ in range(8)] for _ in range(8)], dtype=object)
        
        self.chess_board = board
        self.offsets = offsets
        self.perspective = perspective

    def offset(self, square: chess.Square) -> SquareOffset:
        return self.offsets[chess.square_rank(square), chess.square_file(square)]
    
    def set_offset(self, square: chess.Square, offset: SquareOffset):
        self.offsets[chess.square_rank(square), chess.square_file(square)] = offset

    def piece_at(self, square: chess.Square):
        return self.piece_at(square)

    def remove_piece_at(self, square: chess.Square) -> Optional[chess.Piece]:
        piece = self.chess_board.remove_piece_at(square)
        self.set_offset(square, SQUARE_CENTER)
        return piece
    
    def set_piece_at(self, square: chess.Square, piece: chess.Piece, promoted: bool = False, offset: SquareOffset = SQUARE_CENTER):
        self.chess_board.set_piece_at(square, piece, promoted)
        self.set_offset(square, offset)

    def legal_moves(self):
        return self.chess_board.legal_moves
    
    def push(self, move: chess.Move, to_offset: SquareOffset = SQUARE_CENTER):
        self.chess_board.push(move)
        self.set_offset(move.from_square, SQUARE_CENTER)
        self.set_offset(move.to_square, to_offset)
