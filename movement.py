import logging
import chess

import communication

# Max pieces each player can have
_PIECE_COUNTS = {
    chess.PAWN: 8,
    chess.ROOK: 2,
    chess.BISHOP: 2,
    chess.KNIGHT: 2,
    chess.QUEEN: 1,
    chess.KING: 1,
}


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


def move_piece(from_square, to_square, prev_response=communication.RESPONSE_SUCCESS):
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


def reset_board(
    current_board: chess.Board, expected_board: chess.Board = chess.Board()
):
    """
    TODO: Not yet implemented
    Assume expected board can be created using current pieces
    """
    current_groups = _group_pieces(current_board)
    expected_groups = _group_pieces(expected_board)

    for player, groups in expected_groups.items():
        for piece_type, expected_pieces in groups.items():
            current_pieces = current_groups[player][piece_type]
            off_board_count = {
                piece: count - len(current_pieces)
                for piece, count in _PIECE_COUNTS.items()
            }

            # filter out pieces in correct spots
            i = 0
            j = 0
            while i < len(current_pieces) and j < len(expected_pieces):
                current_square = current_pieces[i]
                expected_square = expected_pieces[j]

                if current_square > expected_square:
                    j = j + 1
                elif expected_square > current_square:
                    i = i + 1
                else:
                    del current_pieces[i]
                    del expected_pieces[j]

            # TODO: validate signals
            i = 0
            j = 0
            while i < len(current_pieces) and j < len(expected_pieces):
                current_square = current_pieces[i]
                expected_square = expected_pieces[j]

                if current_square > expected_square:
                    if off_board_count[piece_type]:
                        origin_square = communication.off_board_square(
                            piece_type, player
                        )
                        move_piece(origin_square, expected_square)
                elif expected_square > current_square:
                    move_piece(current_square, expected_square)
                    i = i + 1
                else:
                    continue


def _group_pieces(board: chess.Board):
    """Ensures squares are sorted"""

    groups = {
        chess.WHITE: {
            chess.PAWN: [],
            chess.ROOK: [],
            chess.BISHOP: [],
            chess.KNIGHT: [],
            chess.QUEEN: [],
            chess.KING: [],
        },
        chess.BLACK: {
            chess.PAWN: [],
            chess.ROOK: [],
            chess.BISHOP: [],
            chess.KNIGHT: [],
            chess.QUEEN: [],
            chess.KING: [],
        },
    }

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            groups[piece.color][piece.piece_type].append(square)
    return groups


def _castle_rook_move(board: chess.Board, move: chess.Move):
    """Assume move is castling"""

    # Determine if the castling is kingside or queenside
    is_kingside = board.is_kingside_castling(move)

    king_from_square = move.from_square
    king_to_square = move.to_square

    # Calculate the rook's initial and final positions based on the king's movement
    if is_kingside:
        rook_from = king_from_square + 3  # Rook starts 3 squares right from the king
        rook_to = (
            king_to_square - 1
        )  # Rook ends up 1 square left from the king's destination
    else:
        rook_from = king_from_square - 4  # Rook starts 4 squares left from the king
        rook_to = (
            king_to_square + 1
        )  # Rook ends up 1 square right from the king's destination

    return chess.Move(rook_from, rook_to)


def _en_passant_captured(move: chess.Move):
    # Determine the direction of the pawn's movement to find the captured pawn's location
    direction = -8 if (move.to_square > move.from_square) else 8
    captured_square = move.to_square + direction
    return captured_square
