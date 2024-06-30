import logging
from typing import Optional, Tuple
import chess
from . import robot
from .board import RealBoard, SQUARE_CENTER

logger = logging.getLogger(__name__)

def reflect_move(board: RealBoard, move: chess.Move) -> int:
    """
    Makes move physically, does not save the move in board
    """

    response = robot.COMMAND_SUCCESS
    from_square, to_square = (move.from_square, move.to_square)

    if board.chess_board.is_castling(move):
        rook_move = castle_rook_move(move)
        if not rook_move:
            return robot.COMMAND_FAILURE

        response = move_piece(board, from_square, to_square, response)
        response = move_piece(board, rook_move.from_square, rook_move.to_square, response)
    else:  # Regular moves
        if board.chess_board.is_capture(move):
            captured_piece = board.piece_at(to_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = robot.off_board_square(piece_type, color)

            # Remove captured piece
            response = move_piece(board, to_square, off_board_place, response)
        if board.chess_board.is_en_passant(move):
            captured_square = en_passant_captured(move)
            captured_piece = board.piece_at(captured_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = robot.off_board_square(piece_type, color)

            # Remove captured piece
            response = move_piece(board, captured_square, off_board_place, response)
        if move.promotion:
            removed_piece = board.piece_at(move.from_square)
            piece_type, color = (removed_piece.piece_type, removed_piece.color)
            off_board_place_removed = robot.off_board_square(piece_type, color)
            off_board_place_promoted = robot.off_board_square(
                move.promotion, color
            )

            # Remove original piece off the board
            response = move_piece(board, from_square, off_board_place_removed, response)

            # Set new piece to be moved
            from_square = off_board_place_promoted

        response = move_piece(board, from_square, to_square, response)

    return response

def move_piece(board: RealBoard, from_square: chess.Square, to_square: chess.Square, prev_response=robot.COMMAND_SUCCESS) -> int:
    """Assume move is valid, call before pushing move in memory!"""
    if prev_response == robot.COMMAND_SUCCESS:
        offset = board.offset(from_square)

        command = robot.form_command(from_square, to_square, offset, perspective=board.perspective)
        response = robot.issue_command(command)

        from_str = chess.square_name(from_square) if 0 <= from_square <= 63 else from_square
        to_str = chess.square_name(to_square) if 0 <= to_square <= 63 else to_square
        move_str = f"{from_str} -> {to_str}"

        if response == robot.COMMAND_SUCCESS:
            # Update board offsets
            if 0 <= from_square <= 63:
                board.set_offset(from_square, SQUARE_CENTER)

            if 0 <= to_square <= 63:
                board.set_offset(to_square, SQUARE_CENTER)

            logger.info(f"Moved piece {move_str} success")
        else:
            logger.warning(f"Moved piece {move_str} failed!")

        return response
    else:
        return prev_response

def identify_move(previous_board: chess.Board, current_board: chess.Board) -> tuple[Optional[chess.Move], bool]:
    """
    Don't forget to validate move afterwards before using it
    """

    # Find piece differences
    dissapeared: list[tuple[chess.Square, chess.Piece]] = []
    appeared: list[tuple[chess.Square, chess.Piece]] = []

    for square in chess.SQUARES:
        previous_piece = previous_board.piece_at(square)
        current_piece = current_board.piece_at(square)

        if previous_piece != current_piece:
            if previous_piece and not current_piece:
                dissapeared.append((square, previous_piece))
            elif current_piece: # New piece or captured
                appeared.append((square, current_piece))

    # Identify move
    move = None

    # Validate normal and promotion moves
    if len(dissapeared) == 1 and len(appeared) == 1:
        previous_square, previous_piece = dissapeared[0]
        current_square, current_piece = appeared[0]

        move = chess.Move(previous_square, current_square)

        # En passant exception
        if is_en_passant(previous_board, move):
            return move, False
            
        # Castling exception
        if previous_board.is_castling(move):
            return move, False
        
        # Promotion exception
        if previous_piece.piece_type == chess.PAWN and chess.square_rank(move.to_square) in (0,7):
            move.promotion = current_piece.piece_type

    # Validate castling move
    elif len(dissapeared) == 2 and len(appeared) == 2:
        # Keep king in front
        if dissapeared[0][1].piece_type != chess.KING:
            dissapeared = [dissapeared[1], dissapeared[0]]
        if appeared[0][1].piece_type != chess.KING:
            appeared = [appeared[1], appeared[0]]

        # Validate pieces
        if dissapeared[0][1].piece_type != chess.KING or dissapeared[0][1] != appeared[0][1]:
            return None, False

        if dissapeared[1][1].piece_type != chess.ROOK or dissapeared[1][1] != appeared[1][1]:
            return None, False

        if dissapeared[0][1].color != appeared[0][1].color:
            return None, False

        move = chess.Move(dissapeared[0][0], appeared[0][0])
        rook_move = chess.Move(dissapeared[1][0], appeared[1][0])

        # Rook checks
        if rook_move != castle_rook_move(move):
            return move, False

    # Validate en passant
    elif len(dissapeared) == 2 and len(appeared) == 1:
        current_square = appeared[0][0]
        if previous_board.is_en_passant(chess.Move(dissapeared[0][0], current_square)):
            pawn_move_from = dissapeared[0][0]
            en_passant_square = dissapeared[1][0]
        elif previous_board.is_en_passant(chess.Move(dissapeared[1][0], current_square)):
            pawn_move_from = dissapeared[1][0]
            en_passant_square = dissapeared[0]
        else:
            return None, False

        move = chess.Move(pawn_move_from, current_square)

        if en_passant_captured(move) != en_passant_square:
            return None, False

    return move, bool(move) and move in previous_board.legal_moves
 
def castle_rook_move(king_move: chess.Move) -> Optional[chess.Move]:
    rook_from, rook_to = None, None
    if king_move.to_square == chess.G1:  # White kingside
        rook_from = chess.H1
        rook_to = chess.F1
    elif king_move.to_square == chess.C1:  # White queenside
        rook_from = chess.A1
        rook_to = chess.D1
    elif king_move.to_square == chess.G8:  # Black kingside
        rook_from = chess.H8
        rook_to = chess.F8
    elif king_move.to_square == chess.C8:  # Black queenside
        rook_from = chess.A8
        rook_to = chess.D8
    else:
        return None

    return chess.Move(rook_from, rook_to)


def en_passant_captured(move: chess.Move):
    # Determine the direction of the pawn's movement to find the captured pawn's location
    direction = -8 if (move.to_square > move.from_square) else 8
    captured_square = move.to_square + direction
    return captured_square

def is_en_passant(board, move):
    if board.piece_at(move.from_square).piece_type == chess.PAWN:
        if abs(move.from_square - move.to_square) in (7, 9) and not board.piece_at(move.to_square):
            return True
    return False

def iter_reset_board(board: RealBoard, expected_board: RealBoard) -> Tuple[int, bool]:
    """
    Resets the board to match the expected_board configuration.
    If no expected_board is provided, it resets to the default chess starting position.
    If perspective is provided, adjusts the perspective accordingly.
    """
    # Create mappings for current and expected piece positions
    current_positions = {square: board.piece_at(square) for square in chess.SQUARES if board.piece_at(square)}
    expected_positions = {square: expected_board.piece_at(square) for square in chess.SQUARES if expected_board.piece_at(square)}

    # Find pieces that are correctly placed, to avoid unnecessary moves
    correctly_placed = {square: piece for square, piece in expected_positions.items() if current_positions.get(square) == piece}

    # Remove correctly placed pieces from current and expected mappings
    for square in list(correctly_placed.keys()):
        current_positions.pop(square, None)
        expected_positions.pop(square, None)

    # Use list to track empty squares on the board
    empty_squares = [square for square in chess.SQUARES if square not in current_positions and square not in expected_positions]

    # Helper function to move a piece and update mappings
    def move_piece_and_update(start_square: chess.Square, end_square: chess.Square) -> int:
        piece = board.piece_at(start_square)
        response = move_piece(board, start_square, end_square)
        if response != robot.COMMAND_SUCCESS:
            return response

        current_positions.pop(start_square)
        current_positions[end_square] = piece

        if end_square in expected_positions and expected_positions[end_square] == piece:
            expected_positions.pop(end_square)

        return robot.COMMAND_SUCCESS

    # First pass: move pieces directly to their target positions if possible
    for square, piece in list(expected_positions.items()):
        if piece in current_positions.values():
            for start_square, current_piece in list(current_positions.items()):
                if current_piece == piece:
                    response = move_piece_and_update(start_square, square)
                    return response, False

    # Second pass: move remaining pieces out of the way, using empty squares as intermediate holding spots
    for start_square, piece in list(current_positions.items()):
        if piece not in expected_positions.values():
            if empty_squares:
                temp_square = empty_squares.pop(0)
                response = move_piece_and_update(start_square, temp_square)
                return response, False

    # Third pass: place pieces in their final positions from temporary spots or off-board
    for square, piece in list(expected_positions.items()):
        origin_square = None
        for temp_square, current_piece in list(current_positions.items()):
            if current_piece == piece:
                origin_square = temp_square
                break
        if origin_square is None:
            origin_square = robot.off_board_square(piece.piece_type, piece.color)
        response = move_piece_and_update(origin_square, square)
        return response, False

    board.chess_board = expected_board.chess_board
    board.perspective = expected_board.perspective

    return robot.COMMAND_SUCCESS, True

