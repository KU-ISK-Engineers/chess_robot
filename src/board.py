import chess
import numpy as np
import chess
from typing import Optional

class BoardWithOffsets:
    def __init__(self, board: chess.Board, offsets: np.ndarray, perspective: chess.Color):
        self.chess_board = board
        self.offsets = offsets
        self.perspective = perspective

    def offset(self, square: chess.Square):
        """
        return x_offset, y_offset percentages
        """

        return self.offsets[chess.square_rank(square), chess.square_file(square)]
    
    def set_offset(self, square: chess.Square, offset_x: float, offset_y: float):
        self.offsets[chess.square_rank(square), chess.square_file(square)] = (offset_x, offset_y)

    def remove_piece_at(self, square: chess.Square) -> Optional[chess.Piece]:
        piece = self.chess_board.remove_piece_at(square)
        self.set_offset(square, 0, 0)
        return piece
    
    # TODO: Finish method
    def set_piece_at(self, square: chess.Square, piece: chess.Piece, promoted: Optional[chess.Piece] = None):
        self.chess_board.set_piece
        self.chess_board.set_piece

    def push_move(self, move: chess.Move):
        self.chess_board.push(move)