import logging
from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, Tuple, List

import chess

from src.core.board import OFFSET_SQUARE_CENTER, PhysicalBoard, PieceOffset

logger = logging.getLogger(__name__)

OFF_BOARD_SQUARES = {
    chess.ROOK: -1,
    chess.KNIGHT: -2,
    chess.BISHOP: -3,
    chess.QUEEN: -4,
    chess.KING: -5,
    chess.PAWN: -6,
}


def off_board_square(piece_type: chess.PieceType, piece_color: chess.Color) -> int:
    """Returns the coordinate of the specified piece when placed off the board (e.g., after capture).

    Args:
        piece_type (chess.PieceType): The type of the piece (e.g., pawn, rook).
        piece_color (chess.Color): The color of the piece (chess.WHITE or chess.BLACK).

    Returns:
        int: The coordinate representing the off-board location for the given piece.
    """

    # Only one color pieces are supported currently due to promotion
    return OFF_BOARD_SQUARES[piece_type]


class PieceMover(ABC):
    """Abstract class representing an interface for moving pieces on a physical board."""

    @abstractmethod
    def move_piece(
        self,
        from_square: chess.Square,
        to_square: chess.Square,
        color: chess.Color,
        origin_offset: PieceOffset,
    ) -> bool:
        """Moves a piece from one square to another on a physical board.

        Note: The piece is put in the center of the square.

        Args:
            from_square (chess.Square): The starting square of the piece to be moved.
            to_square (chess.Square): The destination square for the piece.
            color (chess.Color): The color perspective of the mover (e.g., chess.WHITE or chess.BLACK).
            origin_offset (PieceOffset): The offset of the piece's original location on the `from_square`,
                relative to the square's center.

        Returns:
            bool: True if the move was successfully executed on the physical board, False otherwise.
        """
        pass

    @abstractmethod
    def reset(self) -> bool:
        """Resets the PieceMover's state, such as clearing off-board piece counts.

        Returns:
            bool: True if the reset operation was successful, False otherwise.
        """
        pass


def execute_move(
    mover: PieceMover, board: PhysicalBoard, move: chess.Move, color: chess.Color
) -> bool:
    """
    Executes a specified chess move on a physical board, handling various types of moves
    such as standard moves, captures, castling, and en passant.

    Note: This function should be called before the move is saved on the `chess.Board` object,
    as it relies on the board's current state to determine the necessary piece movements.

    Args:
        mover (PieceMover): The `PieceMover` instance responsible for physically moving
            pieces on the board.
        board (PhysicalBoard): The current physical board representation, including piece
            positions and offsets.
        move (chess.Move): The chess move to execute, represented as a `chess.Move` object
            containing the starting and destination squares.
        color (chess.Color): The color of the piece mover moving the piece (e.g robot hand color)

    Returns:
        bool: `True` if the move was successfully executed on the physical board;
              `False` if any step of the move sequence failed.
    """
    steps = expand_moves(board.chess_board, move)
    if not steps:
        return False

    for from_square, to_square in steps:
        if not move_piece(mover, board, from_square, to_square, color):
            return False

    return True


def expand_moves(
    chess_board: chess.Board, move: chess.Move
) -> List[Tuple[chess.Square, chess.Square]]:
    """
    Expands a chess move into individual piece movements, including special moves (e.g., captures, castling).

    Note:
        This function must be called before the move is saved on the `chess.Board`, as it
        relies on the board's current state to accurately determine the required piece movements.

    Args:
        chess_board (chess.Board): The current state of the chessboard.
        move (chess.Move): The chess move to expand into individual movements.

    Returns:
        List[Tuple[chess.Square, chess.Square]]: A list of individual piece movements (from-square to to-square)
            required to complete the move on the physical board.
    """
    from_square, to_square = (move.from_square, move.to_square)
    moves_list = []

    if chess_board.is_castling(move):
        rook_move = castle_rook_move(move)
        if not rook_move:
            return []

        moves_list.append((from_square, to_square))
        moves_list.append((rook_move.from_square, rook_move.to_square))
    else:  # Regular moves
        if chess_board.is_capture(move):
            captured_piece = chess_board.piece_at(to_square)
            if not captured_piece:
                return []

            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = off_board_square(piece_type, color)

            # Remove captured piece
            moves_list.append((to_square, off_board_place))
        if chess_board.is_en_passant(move):
            captured_square = en_passant_captured(move)
            captured_piece = chess_board.piece_at(captured_square)
            if not captured_piece:
                return []

            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = off_board_square(piece_type, color)

            # Remove captured piece
            moves_list.append((captured_square, off_board_place))
        if move.promotion:
            removed_piece = chess_board.piece_at(move.from_square)
            if not removed_piece:
                return []

            piece_type, color = (removed_piece.piece_type, removed_piece.color)
            off_board_place_removed = off_board_square(piece_type, color)
            off_board_place_promoted = off_board_square(move.promotion, color)

            # Remove original piece off the board
            moves_list.append((from_square, off_board_place_removed))

            from_square = off_board_place_promoted

        moves_list.append((from_square, to_square))

    return moves_list


def move_piece(
    mover: PieceMover,
    board: PhysicalBoard,
    from_square: chess.Square,
    to_square: chess.Square,
    color: chess.Color,
) -> bool:
    """
    Moves a piece from one square to another on the physical board, updating square offsets
    as needed.

    Note: This function directly handles physical piece movement and does not check
    the move's legality.

    Args:
        mover (PieceMover): The `PieceMover` instance responsible for moving pieces on the
            physical board.
        board (PhysicalBoard): The board instance representing the current state of the
            physical board.
        from_square (chess.Square): The starting square of the piece to be moved.
        to_square (chess.Square): The target square for the piece.
        color (chess.Color): The color perspective of the move, indicating the mover's
            perspective (e.g., `True` for white, `False` for black).

    Returns:
        bool: `True` if the piece was moved successfully on the physical board; `False` otherwise.
    """

    if from_square in chess.SQUARES:
        origin_offset = board.get_piece_offset(from_square, color)
    else:
        origin_offset = OFFSET_SQUARE_CENTER

    move_str = piece_move_str(from_square, to_square)
    res = mover.move_piece(from_square, to_square, color, origin_offset)
    if not res:
        logger.error(f"Failed moving piece {move_str}!")
        return False

    # Update board offsets
    if from_square in chess.SQUARES:
        board.set_piece_offset(from_square, color, OFFSET_SQUARE_CENTER)

    if to_square in chess.SQUARES:
        board.set_piece_offset(to_square, color, OFFSET_SQUARE_CENTER)

    logger.info(f"Moved piece {move_str}")
    return True


def iter_reset_board(
    mover: PieceMover,
    board: PhysicalBoard,
    expected_board: PhysicalBoard,
    color: chess.Color,
) -> Tuple[bool, bool]:
    """
    Iteratively rearranges pieces on the physical board to align with the expected board state.

    This function compares the current board state with an expected target state and makes
    adjustments as necessary, moving pieces directly to their target positions if possible,
    or using empty squares as temporary positions when needed.

    Args:
        mover (PieceMover): The `PieceMover` instance responsible for executing physical moves.
        board (PhysicalBoard): The current physical state of the board, representing the
            actual positions of pieces.
        expected_board (PhysicalBoard): The desired target state for the board, with pieces
            in their intended positions.
        color (chess.Color): The color perspective of the `PieceMover` instance.

    Returns:
        Tuple[bool, bool]: A tuple containing two values: First `True` if any piece was moved, second `True` if physical board matches expected board
    """
    # Create mappings for current and expected piece positions
    current_positions = {
        square: piece
        for square in chess.SQUARES
        if (piece := board.chess_board.piece_at(square))
    }

    expected_positions = {
        square: piece
        for square in chess.SQUARES
        if (piece := expected_board.chess_board.piece_at(square))
    }

    # Find pieces that are correctly placed, to avoid unnecessary moves
    correctly_placed = {
        square: piece
        for square, piece in expected_positions.items()
        if (current_piece := current_positions.get(square)) == piece
    }

    # Remove correctly placed pieces from current and expected mappings
    for square in list(correctly_placed.keys()):
        current_positions.pop(square, None)
        expected_positions.pop(square, None)

    # Use list to track empty squares on the board
    empty_squares = [
        square
        for square in chess.SQUARES
        if square not in current_positions and square not in expected_positions
    ]

    # First pass: move pieces directly to their target positions if possible
    for square, piece in list(expected_positions.items()):
        if piece in current_positions.values():
            for start_square, current_piece in list(current_positions.items()):
                if current_piece == piece:
                    return move_piece(mover, board, start_square, square, color), False

    # Second pass: move remaining pieces out of the way, using empty squares as intermediate holding spots
    for start_square, piece in list(current_positions.items()):
        if piece not in expected_positions.values():
            if empty_squares:
                temp_square = empty_squares.pop(0)
                return move_piece(mover, board, start_square, temp_square, color), False

    # Third pass: place pieces in their final positions from temporary spots or off-board
    for square, piece in list(expected_positions.items()):
        origin_square = None
        for temp_square, current_piece in list(current_positions.items()):
            if current_piece == piece:
                origin_square = temp_square
                break

        if origin_square is None:
            origin_square = off_board_square(piece.piece_type, piece.color)

        return move_piece(mover, board, origin_square, square, color), False

    return False, True


class SquarePiece(NamedTuple):
    square: chess.Square
    piece: chess.Piece


def identify_move(
    previous_board: chess.Board, current_board: chess.Board
) -> Tuple[Optional[chess.Move], bool]:
    """
    Identifies the move played by comparing two board states.

    Args:
        previous_board (chess.Board): The board state before the move.
        current_board (chess.Board): The board state after the move.

    Returns:
        Tuple[Optional[chess.Move], bool]: The identified move and a boolean indicating if it is legal.
    """
    disappeared: list[SquarePiece] = []
    appeared: list[SquarePiece] = []

    for square in chess.SQUARES:
        previous_piece = previous_board.piece_at(square)
        current_piece = current_board.piece_at(square)

        if previous_piece != current_piece:
            if previous_piece and not current_piece:
                disappeared.append(SquarePiece(square, previous_piece))
            elif current_piece:  # New piece or captured
                appeared.append(SquarePiece(square, current_piece))

    # Identify move
    move = None

    # Validate normal and promotion moves
    if len(disappeared) == 1 and len(appeared) == 1:
        move = chess.Move(disappeared[0].square, appeared[0].square)

        # Promotion exception
        if disappeared[0].piece.piece_type == chess.PAWN and chess.square_rank(
            move.to_square
        ) in (0, 7):
            move.promotion = appeared[0].piece.piece_type

        # En passant exception
        if previous_board.is_en_passant(move):
            return move, False

        # Castling exception
        if previous_board.is_castling(move):
            return move, False

    # Validate castling move
    elif len(disappeared) == 2 and len(appeared) == 2:
        # Keep king in front
        if disappeared[0].piece.piece_type != chess.KING:
            disappeared = [disappeared[1], disappeared[0]]
        if appeared[0].piece.piece_type != chess.KING:
            appeared = [appeared[1], appeared[0]]

        # Validate pieces
        if (
            disappeared[0].piece.piece_type != chess.KING
            or disappeared[0].piece != appeared[0].piece
        ):
            return None, False

        if (
            disappeared[1].piece.piece_type != chess.ROOK
            or disappeared[1].piece != appeared[1].piece
        ):
            return None, False

        if disappeared[0].piece.color != disappeared[1].piece.color:
            return None, False

        move = chess.Move(disappeared[0].square, appeared[0].square)
        rook_move = chess.Move(disappeared[1].square, appeared[1].square)

        # Rook checks
        if rook_move != castle_rook_move(move):
            return move, False

    # Validate en passant
    elif len(disappeared) == 2 and len(appeared) == 1:
        if previous_board.is_en_passant(
            chess.Move(disappeared[0].square, appeared[0].square)
        ):
            pawn_move_from = disappeared[0].square
            en_passant_square = disappeared[1].square
        elif previous_board.is_en_passant(
            chess.Move(disappeared[1].square, appeared[0].square)
        ):
            pawn_move_from = disappeared[1].square
            en_passant_square = disappeared[0].square
        else:
            return None, False

        move = chess.Move(pawn_move_from, appeared[0].square)

        if en_passant_captured(move) != en_passant_square:
            return None, False

    return move, bool(move) and move in previous_board.legal_moves


def castle_rook_move(king_move: chess.Move) -> Optional[chess.Move]:
    """
    Determines the rook move associated with a castling move.

    Args:
        king_move (chess.Move): The castling move of the king.

    Returns:
        Optional[chess.Move]: The rook's move if castling is detected, otherwise None.
    """
    if king_move.to_square == chess.G1:  # White king-side
        rook_from = chess.H1
        rook_to = chess.F1
    elif king_move.to_square == chess.C1:  # White queen-side
        rook_from = chess.A1
        rook_to = chess.D1
    elif king_move.to_square == chess.G8:  # Black king-side
        rook_from = chess.H8
        rook_to = chess.F8
    elif king_move.to_square == chess.C8:  # Black queen-side
        rook_from = chess.A8
        rook_to = chess.D8
    else:
        return None

    return chess.Move(rook_from, rook_to)


def en_passant_captured(move: chess.Move) -> chess.Square:
    """
    Finds the square of the captured pawn in an en passant move.

    Args:
        move (chess.Move): The en passant move of the pawn.

    Returns:
        chess.Square: The square where the captured pawn was located.
    """
    direction = -8 if (move.to_square > move.from_square) else 8
    captured_square = move.to_square + direction
    return captured_square


def piece_move_str(from_square: chess.Square, to_square: chess.Square) -> str:
    """
    Generates a string representing a move from one square to another.

    Args:
        from_square (chess.Square): The starting square.
        to_square (chess.Square): The destination square.

    Returns:
        str: A string describing the move in the format "from -> to".
    """
    from_str = chess.square_name(from_square) if 0 <= from_square <= 63 else from_square
    to_str = chess.square_name(to_square) if 0 <= to_square <= 63 else to_square
    return f"{from_str} -> {to_str}"
