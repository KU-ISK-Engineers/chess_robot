from typing import Optional, NamedTuple
from abc import ABC, abstractmethod

import chess


class PieceOffset(NamedTuple):
    """Represents an offset from the center of a square for a chess piece.

    The offset is measured in x and y directions, with (0, 0) representing
    the center of the square.

    Attributes:
        x (float): Offset from the center in the x-direction.
        y (float): Offset from the center in the y-direction.
    """

    x: float
    y: float


OFFSET_SQUARE_CENTER = PieceOffset(0, 0)


class PhysicalBoard:
    """Represents a physical chessboard with piece offsets and color perspective.

    The `perspective` attribute specifies which side of the board is physically
    oriented as white, affecting how pieces and offsets are viewed and managed.

    Attributes:
        chess_board (chess.Board): The logical state of the chessboard.
        piece_offsets (list[SquareOffset]): List of offsets for each square, indicating
            the position of pieces relative to each square's center.
        perspective (chess.Color): The board's color perspective (chess.WHITE or chess.BLACK),
            indicating the side that is physically facing the player as white.
    """

    def __init__(
        self,
        chess_board: Optional[chess.Board] = None,
        piece_offsets: Optional[list[PieceOffset]] = None,
        physical_perspective: chess.Color = chess.WHITE,
    ):
        """Initializes the PhysicalBoard with a chess board, optional piece offsets, and a color perspective.

        Args:
            chess_board (Optional[chess.Board]): An instance of `chess.Board` representing the current game state.
                If None, a new `chess.Board` is initialized.
            piece_offsets (Optional[list[SquareOffset]]): A list of `SquareOffset` values for each square,
                representing the relative position of pieces on the board. Defaults to center each piece at (0,0).
            perspective (chess.Color): The color perspective (chess.WHITE or chess.BLACK) indicating which side
                is considered "white" in the physical layout. Defaults to chess.WHITE.
        """

        if chess_board is None:
            chess_board = chess.Board()

        if piece_offsets is None:
            piece_offsets = [OFFSET_SQUARE_CENTER for _ in range(64)]

        self.chess_board = chess_board
        self.piece_offsets = piece_offsets
        self.perspective = physical_perspective

    def piece_offset(self, square: chess.Square) -> PieceOffset:
        """Returns the offset for a given square on the board.

        Args:
            square (chess.Square): The square for which to retrieve the offset.

        Returns:
            SquareOffset: The offset of the piece on the specified square.
        """
        return self.piece_offsets[
            chess.square_rank(square) * 8 + chess.square_file(square)
        ]

    def set_piece_offset(self, square: chess.Square, offset: PieceOffset):
        """Sets the offset for a specific square on the board.

        Args:
            square (chess.Square): The square on which to set the offset.
            offset (SquareOffset): The offset to apply to the specified square.
        """
        self.piece_offsets[
            chess.square_rank(square) * 8 + chess.square_file(square)
        ] = offset


class BoardDetection(ABC):
    """Abstract base class for capturing the state of a physical board."""

    @abstractmethod
    def capture_board(
        self, physical_perspective: chess.Color = chess.WHITE
    ) -> Optional[PhysicalBoard]:
        """Captures the current state of the physical board from a specified color perspective.

        If `physical_perspective` is chess.WHITE, the board is captured as-is. If `physical_perspective` is
        chess.BLACK, the board is captured with a physical rotation along the Y-axis to align
        with the black perspective.

        Args:
            physical_perspective (chess.Color): The color perspective (chess.WHITE or chess.BLACK) from
                which to capture the board's state, determining orientation.

        Returns:
            Optional[PhysicalBoard]: A `PhysicalBoard` instance representing the captured state
                of the board, or None if the capture process fails.
        """
        pass


def boards_are_equal(board1: chess.Board, board2: chess.Board) -> bool:
    """Compares two chess boards to check if they are identical in piece positions.

    Args:
        board1 (chess.Board): The first board to compare.
        board2 (chess.Board): The second board to compare.

    Returns:
        bool: True if both boards have the same pieces on each square, False otherwise.
    """
    for square in chess.SQUARES:
        if board1.piece_at(square) != board2.piece_at(square):
            return False
    return True
