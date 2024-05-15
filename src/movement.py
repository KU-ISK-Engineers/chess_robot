import logging
from typing import List, Optional
import chess

from . import communication

# TODO: Make moves in consideration of what the camera is showing (/ whatever the fuck the user is currently doing)

def make_move(board: chess.Board, move: chess.Move):
    """Assume move is valid, call before pushing move in memory!"""

    move_san = board.san(move)
    logging.info(f"Making move {move_san}...")

    response = communication.RESPONSE_SUCCESS
    from_square, to_square = (move.from_square, move.to_square)

    if board.is_castling(move):
        rook_move = _castle_rook_move(board, move)

        response = move_piece(from_square, to_square, response)
        response = move_piece(rook_move.from_square, rook_move.to_square, response)
    else:  # Regular moves
        if board.is_capture(move):
            captured_piece = board.piece_at(to_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = communication.off_board_square(piece_type, color)

            # Remove captured piece
            response = move_piece(to_square, off_board_place, response)
        if board.is_en_passant(move):
            captured_square = _en_passant_captured(move)
            captured_piece = board.piece_at(captured_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = communication.off_board_square(piece_type, color)

            # Remove captured piece
            response = move_piece(captured_square, off_board_place, response)
        if move.promotion:
            removed_piece = board.piece_at(move.from_square)
            piece_type, color = (removed_piece.piece_type, removed_piece.color)
            off_board_place_removed = communication.off_board_square(piece_type, color)
            off_board_place_promoted = communication.off_board_square(
                move.promotion, color
            )

            # Remove original piece off the board
            response = move_piece(from_square, off_board_place_removed, response)

            # Set new piece to be moved
            from_square = off_board_place_promoted

        response = move_piece(from_square, to_square, response)

    if response == communication.RESPONSE_TIMEOUT:
        logging.warning(f"Move {move_san} timed out!")
    else:
        logging.info(f"Move {move_san} success!")

    return response


def move_piece(from_square: chess.Square, to_square: chess.Square, prev_response=communication.RESPONSE_SUCCESS):
    """Assume move is valid, call before pushing move in memory!"""
    if prev_response == communication.RESPONSE_SUCCESS:
        from_str = chess.square_name(from_square)
        to_str = chess.square_name(to_square)
        logging.info(f"Making move: {from_str} -> {to_str}")

        return communication.issue_command(
            communication.form_command(from_square, to_square)
        )
    else:
        return prev_response


def reset_board(current_board: chess.Board, expected_board: Optional[chess.Board] = None) -> int:
    """
    Assumes expected_board can be created using current pieces.
    """

    if expected_board is None:
        expected_board = chess.Board()

    # Create mappings for current and expected piece positions
    current_positions = {square: current_board.piece_at(square) for square in chess.SQUARES if current_board.piece_at(square)}
    expected_positions = {square: expected_board.piece_at(square) for square in chess.SQUARES if expected_board.piece_at(square)}

    # Find pieces that are correctly placed, to avoid unnecessary moves
    correctly_placed = {square: piece for square, piece in expected_positions.items() if current_positions.get(square) == piece}

    # Remove correctly placed pieces from current and expected mappings
    for square in correctly_placed:
        current_positions.pop(square, None)
        expected_positions.pop(square, None)

    # Use list to track empty squares on the board
    empty_squares = [square for square in chess.SQUARES if square not in current_positions and square not in expected_positions]

    # Helper function to move a piece and update mappings
    def move_piece_and_update(start_square, end_square):
        if move_piece(start_square, end_square) == communication.RESPONSE_TIMEOUT:
            return communication.RESPONSE_TIMEOUT
        piece = current_board.remove_piece_at(start_square)
        current_board.set_piece_at(end_square, piece)
        current_positions.pop(start_square)
        current_positions[end_square] = piece
        if end_square in expected_positions and expected_positions[end_square] == piece:
            expected_positions.pop(end_square)
        return communication.RESPONSE_SUCCESS

    # First pass: move pieces directly to their target positions if possible
    for square, piece in expected_positions.copy().items():
        if piece in current_positions.values():
            for start_square, current_piece in current_positions.items():
                if current_piece == piece and move_piece_and_update(start_square, square) == communication.RESPONSE_TIMEOUT:
                    return communication.RESPONSE_TIMEOUT

    # Second pass: move remaining pieces out of the way, using empty squares as intermediate holding spots
    for start_square, piece in current_positions.copy().items():
        if piece not in expected_positions.values():
            if empty_squares:
                temp_square = empty_squares.pop(0)
                if move_piece_and_update(start_square, temp_square) == communication.RESPONSE_TIMEOUT:
                    return communication.RESPONSE_TIMEOUT

    # Third pass: place pieces in their final positions from temporary spots or off-board
    for square, piece in expected_positions.items():
        origin_square = None
        for temp_square in current_positions:
            if current_positions[temp_square] == piece:
                origin_square = temp_square
                break
        if origin_square is None:
            origin_square = communication.off_board_square(piece.piece_type, piece.color)
        if move_piece_and_update(origin_square, square) == communication.RESPONSE_TIMEOUT:
            return communication.RESPONSE_TIMEOUT

    return communication.RESPONSE_SUCCESS

def identify_move(prev_board: chess.Board, current_board: chess.Board) -> Optional[chess.Move]:
    """
    Don't forget to validate move afterwards before using it
    """

    # Find piece differences
    dissapeared: List[chess.Square] = []
    appeared: List[chess.Square] = []

    for square in chess.SQUARES:
        prev_piece = prev_board.piece_at(square)
        curr_piece = current_board.piece_at(square)

        if prev_piece != curr_piece:
            if prev_piece is not None and curr_piece is None:
                dissapeared.append(square)
            else: # New piece or captured
                appeared.append(square)

    # Handle castling
    if len(dissapeared) == 2 and len(appeared) == 2:
        if prev_board.piece_at(dissapeared[0]).piece_type != chess.KING:
            dissapeared = [dissapeared[1], dissapeared[0]]
        if current_board.piece_at(appeared[0]).piece_type != chess.KING:
            appeared = [appeared[1], appeared[0]]

        king_move_from, king_move_to = dissapeared[0], appeared[0]
        rook_move_from, rook_move_to = dissapeared[1], appeared[1]

        expected_king = prev_board.piece_at(king_move_from)
        if expected_king.piece_type != chess.KING:
            return None # No king in origin square
        
        if current_board.piece_at(king_move_to) != expected_king:
            return None # Not correct piece where king is supposed to be
        
        expected_rook = chess.Piece(chess.ROOK, expected_king.color)
        if prev_board.piece_at(rook_move_from) != expected_rook or current_board.piece_at(rook_move_to) != expected_rook:
            return None # Rooks aren't in respective squares

        dx = chess.square_file(king_move_from) - chess.square_file(king_move_to)
        if abs(dx) != 2:
            return None # King wrong movement
        if chess.square_file(king_move_from) != 4:
            return None # King wrong place for castling
        
        king_move = chess.Move(king_move_from, king_move_to)
        rook_move = _castle_rook_move(prev_board, king_move)
        if rook_move.from_square != rook_move_from or rook_move.to_square != rook_move_to:
            return None # Rook invalid move
        
        return king_move

    # Handle en passant
    elif len(dissapeared) == 2 and len(appeared) == 1:
        pawn_move_from = None
        en_passant_square = None
        pawn_move_to = appeared[0]

        if prev_board.piece_at(dissapeared[0]).piece_type == chess.PAWN and chess.square_file(dissapeared[0]) != chess.square_file(pawn_move_to):
            pawn_move_from = dissapeared[0]
            en_passant_square = dissapeared[1]
        else:
            pawn_move_from = dissapeared[1]
            en_passant_square = dissapeared[0]

        move = chess.Move(pawn_move_from, pawn_move_to)
        if not prev_board.is_en_passant(move):
            return None
        if _en_passant_captured(move) != en_passant_square:
            return None
        return move

    # Handle normal and promotion moves
    elif len(dissapeared) == 1 and len(appeared) == 1:
        move = chess.Move(dissapeared[0], appeared[0])
        
        # Check for promotion
        if prev_board.piece_at(dissapeared[0]).piece_type == chess.PAWN and chess.square_rank(appeared[0]) in (0,7):
            promotion_piece_type = current_board.piece_at(appeared[0]).piece_type
            move = chess.Move(dissapeared[0], appeared[0], promotion=promotion_piece_type)

        return move

    return None
 
def _castle_rook_move(board: chess.Board, move: chess.Move) -> chess.Move:
    """Assume move is castling"""

    is_kingside = board.is_kingside_castling(move)

    king_from_square = move.from_square
    king_to_square = move.to_square

    if is_kingside:
        rook_from = king_from_square + 3  # Rook starts 3 squares right from the king
        rook_to = king_to_square - 1 # Rook ends up 1 square left from the king's destination
    else:
        rook_from = king_from_square - 4  # Rook starts 4 squares left from the king
        rook_to = king_to_square + 1 # Rook ends up 1 square right from the king's destination

    return chess.Move(rook_from, rook_to)


def _en_passant_captured(move: chess.Move):
    # Determine the direction of the pawn's movement to find the captured pawn's location
    direction = -8 if (move.to_square > move.from_square) else 8
    captured_square = move.to_square + direction
    return captured_square
