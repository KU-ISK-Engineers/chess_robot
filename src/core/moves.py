import logging
from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, Tuple

import chess

from src.core.board import OFFSET_SQUARE_CENTER, PhysicalBoard, PieceOffset

logger = logging.getLogger(__name__)


OFF_BOARD_SQUARES = {
    (chess.ROOK, chess.WHITE): -1,
    (chess.BISHOP, chess.WHITE): -2,
    (chess.KNIGHT, chess.WHITE): -3,
    (chess.QUEEN, chess.WHITE): -4,
    (chess.KING, chess.WHITE): -5,
    (chess.PAWN, chess.WHITE): -6,
    (chess.ROOK, chess.BLACK): -7,
    (chess.BISHOP, chess.BLACK): -8,
    (chess.KNIGHT, chess.BLACK): -9,
    (chess.QUEEN, chess.BLACK): -10,
    (chess.KING, chess.BLACK): -11,
    (chess.PAWN, chess.BLACK): -12,
}


def off_board_square(piece_type: chess.PieceType, color: chess.Color) -> int:
    """Returns the coordinate of the specified piece when placed off the board (e.g., after capture).

    Args:
        piece_type (chess.PieceType): The type of the piece (e.g., pawn, rook).
        color (chess.Color): The color of the piece (chess.WHITE or chess.BLACK).

    Returns:
        int: The coordinate representing the off-board location for the given piece.
    """
    return OFF_BOARD_SQUARES[(piece_type, color)]


# TODO: Why was there perspective?
class PieceMover(ABC):
    """Abstract class representing an interface for moving pieces on a physical board."""

    @abstractmethod
    def move_piece(
        self,
        from_square: chess.Square,
        to_square: chess.Square,
        piece_offset: PieceOffset = OFFSET_SQUARE_CENTER,
        physical_perspective: chess.COLOR = chess.WHITE,
    ) -> bool:
        """Moves a piece from one square to another on a physical board.

        Args:
            from_square (chess.Square): The starting square of the piece.
            to_square (chess.Square): The destination square for the piece.
            offset (SquareOffset, optional): Offset for piece placement on the destination square.
                Defaults to the center of the square.
            physical_perspective (chess.Color, optional): The physical perspective of the player (e.g., chess.WHITE or chess.BLACK).
                If chess.WHITE, the board is unrotated. If chess.BLACK, the board is rotated along the Y-axis to align
                with the black perspective. Defaults to chess.WHITE.

        Returns:
            bool: True if the move was successfully executed on the physical board, False otherwise.
        """
        pass

    @abstractmethod
    def reset(self) -> bool:
        """Forces PieceMover to reset state, e.g reset counts for off-board locations

        Returns:
            bool: True if operation was successful, False otherwise
        """
        pass


def reflect_move(mover: PieceMover, board: PhysicalBoard, move: chess.Move) -> bool:
    """
    Executes a move on the physical board, handling both simple and complex moves (e.g., castling, captures).

    Note:
        This function must be called before saving the move on the `chess.Board`, as it relies
        on the pre-move position to determine the steps required to execute the move.

    Args:
        mover (PieceMover): The `PieceMover` instance responsible for physically moving pieces.
        board (PhysicalBoard): The current state of the physical board.
        move (chess.Move): The chess move to be executed on the physical board.

    Returns:
        bool: True if the move was successfully executed on the physical board, False otherwise.
    """
    steps = expand_moves(board.chess_board, move)
    if not steps:
        return False

    for from_square, to_square in steps:
        if not move_piece(mover, board, from_square, to_square):
            return False

    return True


def expand_moves(
    chess_board: chess.Board, move: chess.Move
) -> list[tuple[chess.Square, chess.Square]]:
    """
    Expands a chess move into individual piece movements, including special moves (e.g., captures, castling).

    Note:
        This function must be called before the move is saved on the `chess.Board`, as it
        relies on the board's current state to accurately determine the required piece movements.

    Args:
        chess_board (chess.Board): The current state of the chessboard.
        move (chess.Move): The chess move to expand into individual movements.

    Returns:
        list[tuple[chess.Square, chess.Square]]: A list of individual piece movements (from-square to to-square)
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
) -> bool:
    """
    Moves a piece from one square to another on the physical board, updating square offsets.

    Args:
        mover (PieceMover): The PieceMover instance to perform the move.
        board (PhysicalBoard): The board instance where the move is executed.
        from_square (chess.Square): Starting square of the move.
        to_square (chess.Square): Target square of the move.

    Returns:
        bool: True if the piece was moved successfully, False otherwise.
    """

    if 0 <= from_square <= 63:
        offset = board.piece_offset(from_square)
    else:
        offset = OFFSET_SQUARE_CENTER

    move_str = piece_move_str(from_square, to_square)
    res = mover.move_piece(from_square, to_square, offset, board.perspective)
    if not res:
        logger.error(f"Moved piece {move_str} failed")
        return False

    # Update board offsets
    if 0 <= from_square <= 63:
        board.set_piece_offset(from_square, OFFSET_SQUARE_CENTER)

    if 0 <= to_square <= 63:
        board.set_piece_offset(to_square, offset)

    logger.info(f"Moved piece {move_str} success")
    return True


def iter_reset_board(
    mover: PieceMover, board: PhysicalBoard, expected_board: PhysicalBoard
) -> Tuple[bool, bool]:
    """
    Iteratively arranges pieces on the physical board to match the expected board state.

    Args:
        mover (PieceMover): The PieceMover instance to perform the move.
        board (PhysicalBoard): The current physical board state.
        expected_board (PhysicalBoard): The expected target board state.

    Returns:
        Tuple[bool, bool]: The first boolean indicates if a piece was moved; the second if the board matches the expected state.
    """
    # Create mappings for current and expected piece positions
    current_positions = {
        square: board.chess_board.piece_at(square)
        for square in chess.SQUARES
        if board.chess_board.piece_at(square)
    }
    expected_positions = {
        square: expected_board.chess_board.piece_at(square)
        for square in chess.SQUARES
        if expected_board.chess_board.piece_at(square)
    }

    # Find pieces that are correctly placed, to avoid unnecessary moves
    correctly_placed = {
        square: piece
        for square, piece in expected_positions.items()
        if current_positions.get(square) == piece
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
                    return move_piece(mover, board, start_square, square), False

    # Second pass: move remaining pieces out of the way, using empty squares as intermediate holding spots
    for start_square, piece in list(current_positions.items()):
        if piece not in expected_positions.values():
            if empty_squares:
                temp_square = empty_squares.pop(0)
                return move_piece(mover, board, start_square, temp_square), False

    # Third pass: place pieces in their final positions from temporary spots or off-board
    for square, piece in list(expected_positions.items()):
        origin_square = None
        for temp_square, current_piece in list(current_positions.items()):
            if current_piece == piece:
                origin_square = temp_square
                break

        if origin_square is None:
            origin_square = off_board_square(piece.piece_type, piece.color)

        return move_piece(mover, board, origin_square, square), False

    board.chess_board = expected_board.chess_board
    board.perspective = expected_board.perspective

    return False, True


class SquarePiece(NamedTuple):
    square: chess.Square
    piece: chess.Piece


def identify_move(
    previous_board: chess.Board, current_board: chess.Board
) -> tuple[Optional[chess.Move], bool]:
    """
    Identifies the move played by comparing two board states.

    Args:
        previous_board (chess.Board): The board state before the move.
        current_board (chess.Board): The board state after the move.

    Returns:
        tuple[Optional[chess.Move], bool]: The identified move and a boolean indicating if it is legal.
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
