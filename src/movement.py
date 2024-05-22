import logging
from typing import List, Optional
import chess
import time
from . import communication
from .board import BoardWithOffsets, SQUARE_CENTER

def reflect_move(board: BoardWithOffsets, move: chess.Move) -> int:
    """
    Makes move physically, does not save the move in board
    """

    response = communication.RESPONSE_SUCCESS
    from_square, to_square = (move.from_square, move.to_square)

    if board.chess_board.is_castling(move):
        rook_move = _castle_rook_move(board, move)

        response = move_piece(board, from_square, to_square, response)
        response = move_piece(board, rook_move.from_square, rook_move.to_square, response)
    else:  # Regular moves
        if board.chess_board.is_capture(move):
            captured_piece = board.piece_at(to_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = communication.off_board_square(piece_type, color)

            # Remove captured piece
            response = move_piece(board, to_square, off_board_place, response)
        if board.chess_board.is_en_passant(move):
            captured_square = _en_passant_captured(move)
            captured_piece = board.piece_at(captured_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = communication.off_board_square(piece_type, color)

            # Remove captured piece
            response = move_piece(board, captured_square, off_board_place, response)
        if move.promotion:
            removed_piece = board.piece_at(move.from_square)
            piece_type, color = (removed_piece.piece_type, removed_piece.color)
            off_board_place_removed = communication.off_board_square(piece_type, color)
            off_board_place_promoted = communication.off_board_square(
                move.promotion, color
            )

            # Remove original piece off the board
            response = move_piece(board, from_square, off_board_place_removed, response)

            # Set new piece to be moved
            from_square = off_board_place_promoted

        response = move_piece(board, from_square, to_square, response)

    return response

# TODO: Test this function
def move_piece(board: BoardWithOffsets, from_square: chess.Square, to_square: chess.Square, prev_response=communication.RESPONSE_SUCCESS) -> int:
    """Assume move is valid, call before pushing move in memory!"""
    if prev_response == communication.RESPONSE_SUCCESS:
        from_str = chess.square_name(from_square)
        to_str = chess.square_name(to_square)
        move_str = f"{from_str} -> {to_str}"
        logging.info(f"Making move: {move_str}")

        offset = board.offset(from_square)

        command = communication.form_command(from_square, to_square, offset, perspective=board.perspective)
        response = communication.issue_command(command)

        if response == communication.RESPONSE_SUCCESS:
            logging.info(f"Move {move_str} success")

            # Update board offsets
            if 0 >= from_square <= 63:
                board.set_offset(from_square, SQUARE_CENTER)

            if 0 >= to_square <= 63:
                board.set_offset(to_square, SQUARE_CENTER)
        else:
            logging.warning(f"Move {move_str} failed!")

        return response
    else:
        return prev_response

# TODO: Check offsets, flip board if perspectives differ
def reset_board(board: BoardWithOffsets, expected_board: Optional[chess.Board] = None, perspective: Optional[chess.Color] = None) -> int:
    """
    Assumes expected_board can be created using current pieces.
    """

    if expected_board is None:
        expected_board = chess.Board()

    # Create mappings for current and expected piece positions
    current_positions = {square: board.piece_at(square) for square in chess.SQUARES if board.piece_at(square)}
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
    def move_piece_and_update(start_square: chess.Square, end_square: chess.Square) -> int:
        response = move_piece(board, start_square, end_square)
        if response != communication.RESPONSE_SUCCESS:
            return response

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

    board.chess_board = expected_board
    if perspective:
        board.perspective = perspective
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

    # Validate normal and promotion moves
    if len(dissapeared) == 1 and len(appeared) == 1:
        move = chess.Move(dissapeared[0], appeared[0])

        # En passant exception
        if _is_en_passant(prev_board, move):
            return None
            
        # Castling exception
        if prev_board.is_castling(move):
            return None
        
        # Check for promotion
        if prev_board.piece_at(move.from_square).piece_type == chess.PAWN and chess.square_rank(move.to_square) in (0,7):
            promotion_piece_type = current_board.piece_at(move.to_square).piece_type
            move.promotion = promotion_piece_type

        return move

    # Validate castling move
    elif len(dissapeared) == 2 and len(appeared) == 2:
        if prev_board.piece_at(dissapeared[0]).piece_type != chess.KING:
            dissapeared = [dissapeared[1], dissapeared[0]]
        if current_board.piece_at(appeared[0]).piece_type != chess.KING:
            appeared = [appeared[1], appeared[0]]

        king_move = chess.Move(dissapeared[0], appeared[0])
        rook_move = chess.Move(dissapeared[1], appeared[1])

        if not prev_board.is_castling(king_move):
            return None 
        
        # Rook checks
        color = prev_board.piece_at(king_move.from_square).color
        expected_rook = chess.Piece(chess.ROOK, color)

        if prev_board.piece_at(rook_move.from_square) != expected_rook or current_board.piece_at(rook_move.to_square) != expected_rook:
            return None
        
        if rook_move != _castle_rook_move(prev_board, king_move):
            return None

        return king_move

    # Validate en passant
    elif len(dissapeared) == 2 and len(appeared) == 1:
        pawn_move_to = appeared[0]
        if prev_board.is_en_passant(chess.Move(dissapeared[0], pawn_move_to)):
            pawn_move_from = dissapeared[0]
            en_passant_square = dissapeared[1]
        elif prev_board.is_en_passant(chess.Move(dissapeared[1], pawn_move_to)):
            pawn_move_from = dissapeared[1]
            en_passant_square = dissapeared[0]
        else:
            return None

        move = chess.Move(pawn_move_from, pawn_move_to)

        if _en_passant_captured(move) != en_passant_square:
            return None

        return move

    return None
 
def _castle_rook_move(board: chess.Board, king_move: chess.Move) -> chess.Move:
    if board.piece_at(king_move.from_square).piece_type == chess.KING and board.is_castling(king_move):
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
        return chess.Move(rook_from, rook_to)
    return None


def _en_passant_captured(move: chess.Move):
    # Determine the direction of the pawn's movement to find the captured pawn's location
    direction = -8 if (move.to_square > move.from_square) else 8
    captured_square = move.to_square + direction
    return captured_square

def _is_en_passant(board, move):
    if board.piece_at(move.from_square).piece_type == chess.PAWN:
        if abs(move.from_square - move.to_square) in (7, 9) and not board.piece_at(move.to_square):
            return True
    return False

# ---- TESTING ---

import sys
from .camera import CameraDetection
from ultralytics import YOLO
from .detection import visualise_chessboard
from pypylon import pylon
import cv2

def setup_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate.SetValue(5)
    camera.ExposureAuto.SetValue('Continuous')
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("RGB8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    return camera

def main():
    # if len(sys.argv) != 2:
    #     print("Usage: python script.py path_to_model")
    #     sys.exit(1)

    # model = YOLO(sys.argv[1])
    model = YOLO("../training/chess_200.pt")

    camera = setup_camera()

    detection = CameraDetection(camera, model)

    prev_board = BoardWithOffsets(perspective=chess.BLACK)
    print(prev_board)

    communication.setup_communication()

    while True:
        #image = detection.capture_image()
        board = detection.capture_board(perspective=chess.BLACK)
        visualise_chessboard(board)

        if prev_board:
            move = identify_move(prev_board.chess_board, board.chess_board)

            if not move:
                continue
            
            print(move.uci())

            if move not in prev_board.legal_moves():
                pass
                #print('Illegal move')
            else:

                visualize_move_with_arrow(prev_board, move, 'move_before.svg')
                visualize_move_with_arrow(board, move, 'move_after.svg')

                response = reflect_move(prev_board, move)
                if response == communication.RESPONSE_SUCCESS:
                    print('response Success')

                    prev_board.push(move)
                else:
                    print('response fail')
                    time.sleep(5)

def visualize_move_with_arrow(board: BoardWithOffsets, move: chess.Move, filename: str):
    """
    Visualize a move on the chessboard with an arrow from the starting square to the ending square.
    
    :param board: The chess.Board object.
    :param move_uci: The move in UCI format (e.g., "e2e4").
    """
    arrow = (move.from_square, move.to_square)
    
    # Display the board with the arrow
    svg_before = chess.svg.board(board=board.chess_board, size=400, arrows=[arrow])

    # Save the SVG image to a file
    with open(filename, 'w') as f:
        f.write(svg_before)

if __name__ == "__main__":
    main()
