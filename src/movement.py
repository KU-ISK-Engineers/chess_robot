import logging
from typing import Optional, Tuple
import chess
from . import robot
from .board import PhysicalBoard, SQUARE_CENTER
from typing import NamedTuple

logger = logging.getLogger(__name__)


def reflect_move(board: PhysicalBoard, move: chess.Move) -> bool:
    """
    Executes valid or invalid move on the physical board,
    Updates appropriate square offsets after move was executed
    Returns True if move was played out on the physical board, False otherwise
    """
    moves = chess_move_to_piece_moves(board, move)
    if not moves:
        return False

    for (from_square, to_square) in moves:
        if not move_piece(board, from_square, to_square):
            return False

    return True


def chess_move_to_piece_moves(board: PhysicalBoard, move: chess.Move) -> list[tuple[chess.Square, chess.Square]]:
    from_square, to_square = (move.from_square, move.to_square)
    moves_list = []

    if board.chess_board.is_castling(move):
        rook_move = castle_rook_move(move)
        if not rook_move:
            return []

        moves_list.append((from_square, to_square))
        moves_list.append((rook_move.from_square, rook_move.to_square))
    else:  # Regular moves
        if board.chess_board.is_capture(move):
            captured_piece = board.chess_board.piece_at(to_square)
            if not captured_piece:
                return []

            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = robot.off_board_square(piece_type, color)

            # Remove captured piece
            moves_list.append((to_square, off_board_place))
        if board.chess_board.is_en_passant(move):
            captured_square = en_passant_captured(move)
            captured_piece = board.chess_board.piece_at(captured_square)
            if not captured_piece:
                return []

            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = robot.off_board_square(piece_type, color)

            # Remove captured piece
            moves_list.append((captured_square, off_board_place))
        if move.promotion:
            removed_piece = board.chess_board.piece_at(move.from_square)
            if not removed_piece:
                return []

            piece_type, color = (removed_piece.piece_type, removed_piece.color)
            off_board_place_removed = robot.off_board_square(piece_type, color)
            off_board_place_promoted = robot.off_board_square(
                move.promotion, color
            )

            # Remove original piece off the board
            moves_list.append((from_square, off_board_place_removed))

            from_square = off_board_place_promoted

        moves_list.append((from_square, to_square))

    return moves_list


def move_piece(board: PhysicalBoard, from_square: chess.Square, to_square: chess.Square) -> bool:
    """
    Moves piece from square to the other on the physical board,
    Updates appropriate square offsets after move was executed
    Returns True if piece was moved, False otherwise
    """
    offset = board.piece_offset(from_square)
    move_str = piece_move_str(from_square, to_square)

    command = robot.form_command(from_square, to_square, offset, perspective=board.perspective)
    response = robot.issue_command(command)

    if response != robot.COMMAND_SUCCESS:
        logger.error(f"Moved piece {move_str} failed")
        return False

    # Update board offsets
    if 0 <= from_square <= 63:
        board.set_piece_offset(from_square, SQUARE_CENTER)

    if 0 <= to_square <= 63:
        board.set_piece_offset(to_square, offset)

    logger.info(f"Moved piece {move_str} success")
    return True


def piece_move_str(from_square: chess.Square, to_square: chess.Square) -> str:
    from_str = chess.square_name(from_square) if 0 <= from_square <= 63 else from_square
    to_str = chess.square_name(to_square) if 0 <= to_square <= 63 else to_square
    return f"{from_str} -> {to_str}"


class SquarePiece(NamedTuple):
    square: chess.Square
    piece: chess.Piece


def identify_move(previous_board: chess.Board, current_board: chess.Board) -> tuple[Optional[chess.Move], bool]:
    """
    Identifies move played by comparing two boards
    Returns Move if it was identified, and boolean value indicating whether the move is legal in current board
    """
    # Find piece differences
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
        if disappeared[0].piece.piece_type == chess.PAWN and chess.square_rank(move.to_square) in (0, 7):
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
        if disappeared[0].piece.piece_type != chess.KING or disappeared[0].piece != appeared[0].piece:
            return None, False

        if disappeared[1].piece.piece_type != chess.ROOK or disappeared[1].piece != appeared[1].piece:
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
        if previous_board.is_en_passant(chess.Move(disappeared[0].square, appeared[0].square)):
            pawn_move_from = disappeared[0].square
            en_passant_square = disappeared[1].square
        elif previous_board.is_en_passant(chess.Move(disappeared[1].square, appeared[0].square)):
            pawn_move_from = disappeared[1].square
            en_passant_square = disappeared[0].square
        else:
            return None, False

        move = chess.Move(pawn_move_from, appeared[0].square)

        if en_passant_captured(move) != en_passant_square:
            return None, False

    return move, bool(move) and move in previous_board.legal_moves


def castle_rook_move(king_move: chess.Move) -> Optional[chess.Move]:
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
    # Determine the direction of the pawn's movement to find the captured pawn's location
    direction = -8 if (move.to_square > move.from_square) else 8
    captured_square = move.to_square + direction
    return captured_square


def iter_reset_board(board: PhysicalBoard, expected_board: PhysicalBoard) -> Tuple[bool, bool]:
    """
    Iteratively rearranges pieces on the physical board to match the expected board
    Each time this is called current physical board becomes more similar to the expected board
    Returns first boolean value indicating whether a piece was moved, second value whether board is now the same as expected board
    """
    # Create mappings for current and expected piece positions
    current_positions = {square: board.chess_board.piece_at(square) for square in chess.SQUARES if board.chess_board.piece_at(square)}
    expected_positions = {square: expected_board.chess_board.piece_at(square) for square in chess.SQUARES if expected_board.chess_board.piece_at(square)}

    # Find pieces that are correctly placed, to avoid unnecessary moves
    correctly_placed = {square: piece for square, piece in expected_positions.items() if current_positions.get(square) == piece}

    # Remove correctly placed pieces from current and expected mappings
    for square in list(correctly_placed.keys()):
        current_positions.pop(square, None)
        expected_positions.pop(square, None)

    # Use list to track empty squares on the board
    empty_squares = [square for square in chess.SQUARES if square not in current_positions and square not in expected_positions]

    # First pass: move pieces directly to their target positions if possible
    for square, piece in list(expected_positions.items()):
        if piece in current_positions.values():
            for start_square, current_piece in list(current_positions.items()):
                if current_piece == piece:
                    return move_piece(board, start_square, square), False

    # Second pass: move remaining pieces out of the way, using empty squares as intermediate holding spots
    for start_square, piece in list(current_positions.items()):
        if piece not in expected_positions.values():
            if empty_squares:
                temp_square = empty_squares.pop(0)
                return move_piece(board, start_square, temp_square), False

    # Third pass: place pieces in their final positions from temporary spots or off-board
    for square, piece in list(expected_positions.items()):
        origin_square = None
        for temp_square, current_piece in list(current_positions.items()):
            if current_piece == piece:
                origin_square = temp_square
                break

        if origin_square is None:
            origin_square = robot.off_board_square(piece.piece_type, piece.color)

        return move_piece(board, origin_square, square), False

    board.chess_board = expected_board.chess_board
    board.perspective = expected_board.perspective

    return True, True

