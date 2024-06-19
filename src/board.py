import chess
from typing import Optional, NamedTuple
from abc import ABC, abstractmethod

class SquareOffset(NamedTuple):
    x: float
    y: float

SQUARE_CENTER = SquareOffset(0, 0)

class RealBoard:
    def __init__(self, board: Optional[chess.Board] = None, offsets: Optional[list[SquareOffset]] = None, perspective: chess.Color = chess.WHITE):
        if board is None:
            board = chess.Board()

        if offsets is None:
            offsets = [SQUARE_CENTER for _ in range(64)] 

        self.chess_board = board
        self.offsets = offsets
        self.perspective = perspective

    def offset(self, square: chess.Square) -> SquareOffset:
        return self.offsets[chess.square_rank(square) * 8 + chess.square_file(square)]

    def set_offset(self, square: chess.Square, offset: SquareOffset):
        self.offsets[chess.square_rank(square) * 8 + chess.square_file(square)] = offset

    def remove_piece_at(self, square: chess.Square) -> Optional[chess.Piece]:
        piece = self.chess_board.remove_piece_at(square)
        self.set_offset(square, SQUARE_CENTER)
        return piece
    
    def set_piece_at(self, square: chess.Square, piece: Optional[chess.Piece], promoted: bool = False, offset: SquareOffset = SQUARE_CENTER):
        self.chess_board.set_piece_at(square, piece, promoted)
        self.set_offset(square, offset)

    def push(self, move: chess.Move, to_offset: SquareOffset = SQUARE_CENTER):
        # TODO: Fix offsets for special moves (castling and en passant)?
        self.chess_board.push(move)
        self.set_offset(move.from_square, SQUARE_CENTER)
        self.set_offset(move.to_square, to_offset)

    def clear_board(self):
        self.chess_board.clear_board()
        self.offsets = [SQUARE_CENTER for _ in range(64)]

    def __getattr__(self, name: str):
        return getattr(self.chess_board, name)


class BoardDetection(ABC):
    @abstractmethod
    def capture_board(self, perspective: chess.Color = chess.WHITE) -> RealBoard:
        pass

