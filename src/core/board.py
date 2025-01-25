from typing import Optional, NamedTuple, List
from abc import ABC, abstractmethod

import chess


class PieceOffset(NamedTuple):
    """Represents an offset from the center of a square for a chess piece.

    The offset is measured in `x` and `y` directions, with (0.0, 0.0) representing
    the center of the square. The values range from -1.0 to +1.0, where -1.0 indicates
    the left or bottom edge, and +1.0 indicates the right or top edge.

    Attributes:
        x (float): Horizontal offset from the center of the square.
            0.0 represents the center, -1.0 represents the left edge,
            and +1.0 represents the right edge.
        y (float): Vertical offset from the center of the square.
            0.0 represents the center, -1.0 represents the bottom edge,
            and +1.0 represents the top edge.
    """

    x: float
    y: float


def flip_offset(offset: PieceOffset) -> PieceOffset:
    """Flips the coordinates of a given offset to represent the opposite perspective.

    Args:
        offset (PieceOffset): The original offset to flip, representing a piece's position
            within its square from a specific perspective.

    Returns:
        PieceOffset: A new `PieceOffset` instance with x and y coordinates inverted,
            representing the offset from the opposite perspective.
    """
    return PieceOffset(-offset.x, -offset.y)


OFFSET_SQUARE_CENTER = PieceOffset(0, 0)


class PhysicalBoard:
    """Represents a physical chessboard with relative piece offsets.

    This class manages the physical layout of a chessboard, including the relative
    positions (offsets) of pieces on each square. Offsets are defined from White's
    perspective by default, meaning White is positioned at the bottom of the board.
    Depending on the specified perspective, offsets can be flipped to reflect Black's
    viewpoint.

    Attributes:
        chess_board (chess.Board): The current game board represented as a `chess.Board` instance.
        piece_offsets (List[List[PieceOffset]]): A 2D list (8x8) of `PieceOffset` objects, each representing the relative
            offset of a piece on a given square. Offsets are stored in white perspective.
    """

    def __init__(
        self,
        chess_board: Optional[chess.Board] = None,
        piece_offsets: Optional[List[List[PieceOffset]]] = None,
        perspective: chess.Color = chess.WHITE,
    ):
        """Initializes the PhysicalBoard with a chessboard, piece offsets, and color perspective.

        Args:
            chess_board (Optional[chess.Board]): An instance of `chess.Board` representing the current game board.
                If None, a new `chess.Board` is initialized to represent the default starting position.
            piece_offsets (Optional[List[List[PieceOffset]]]): A 2D list (8x8) of `PieceOffset` instances, each indicating the
                relative position of a piece within its square on the board. If None, defaults to positioning
                each piece at the center (0, 0) of its square.
            perspective (chess.Color): The color perspective (chess.WHITE or chess.BLACK) that determines
                the board's orientation. The offsets are flipped to represent the board as viewed from that perspective.
        """

        if chess_board is None:
            chess_board = chess.Board()

        if piece_offsets is None:
            piece_offsets = [[OFFSET_SQUARE_CENTER for _ in range(8)] for _ in range(8)]
        elif perspective == chess.BLACK:
            piece_offsets = [
                [flip_offset(offset) for offset in row] for row in piece_offsets
            ]

        self.chess_board = chess_board
        self.piece_offsets = piece_offsets

    def get_piece_offset(
        self, square: chess.Square, perspective: chess.Color
    ) -> PieceOffset:
        """Returns the offset for a given square on the board, adjusted for perspective.

        Args:
            square (chess.Square): The square for which to retrieve the offset.
            perspective (chess.Color): The color perspective (chess.WHITE or chess.BLACK)
                from which the offset should be viewed.

        Returns:
            PieceOffset: The offset of the piece on the specified square, adjusted
            according to the specified perspective.
        """

        rank_index = chess.square_rank(square)
        file_index = chess.square_file(square)

        offset = self.piece_offsets[rank_index][file_index]
        if perspective == chess.BLACK:
            offset = flip_offset(offset)
        return offset

    def set_piece_offset(
        self,
        square: chess.Square,
        perspective: chess.Color,
        piece_offset: PieceOffset,
    ):
        """Sets the offset for a specific square on the board, considering perspective.

        Args:
            square (chess.Square): The square on which to set the offset.
            perspective (chess.Color): The perspective from which the offset is applied.
            piece_offset (PieceOffset): The offset to apply to the specified square, relative to its center.
        """

        if perspective == chess.BLACK:
            piece_offset = flip_offset(piece_offset)

        rank_index = chess.square_rank(square)
        file_index = chess.square_file(square)

        self.piece_offsets[rank_index][file_index] = piece_offset


class BoardCapture(ABC):
    """Abstract base class for capturing the state of a physical chessboard."""

    @abstractmethod
    def capture_board(self, human_color: chess.Color) -> Optional[PhysicalBoard]:
        """Captures the current state of the physical board from the human player's perspective.

        Args:
            human_perspective (chess.Color): The color perspective (`chess.WHITE` or `chess.BLACK`)
                from which to capture the board's state, determining its orientation and
                corresponding piece offset adjustments.

        Returns:
            Optional[PhysicalBoard]: A `PhysicalBoard` instance representing the captured state
                of the board, or `None` if the capture process fails, such as due to a detection 
                or alignment error.
        """
        pass


def are_boards_equal(board1: chess.Board, board2: chess.Board) -> bool:
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


def flip_square(chess_square: chess.Square) -> chess.Square:
    """Flips a chess square to its mirrored position on the board.

    Args:
        chess_square (chess.Square): The square to flip, represented as an integer.

    Returns:
        chess.Square: The mirrored square, where the rank and file are flipped to their opposite positions.
    """
    if chess_square not in chess.SQUARES:
        return chess_square

    file_index = chess.square_file(chess_square)
    rank_index = chess.square_rank(chess_square)

    mirrored_rank = 7 - rank_index
    mirrored_file = 7 - file_index
    return chess.square(mirrored_file, mirrored_rank)
