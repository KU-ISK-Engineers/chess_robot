import RPi.GPIO as GPIO
import logging
import time
import chess

# Pin configuration
_PIN_OUT_DAT = 11
_PIN_OUT_CLK = 13
_PIN_IN_RESP = 15

# Delay configuration
_DELAY_TIMEOUT_MIN_S = 0.5
_DELAY_TIMEOUT_MAX_S = 10
_DELAY_WAIT_S = 0.1

# Signal waiting return values
RESPONSE_TIMEOUT = 0
RESPONSE_SUCCESS = 1

# Off the board pieces identifiers 
_OFF_BOARD_PIECES = {
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

def setup_communication():
    logging.info("Setting up GPIO pins...")

    GPIO.setmode(GPIO.BOARD)

    # Pin directions
    GPIO.setup(_PIN_OUT_CLK, GPIO.OUT)
    GPIO.setup(_PIN_OUT_DAT, GPIO.OUT)
    GPIO.setup(_PIN_IN_RESP, GPIO.IN)

    # Initial values
    GPIO.output(_PIN_OUT_CLK, GPIO.LOW)
    GPIO.output(_PIN_OUT_DAT, GPIO.LOW)

def close_communication():
    logging.info("Cleaning up GPIO pins...")

    GPIO.cleanup()

def make_move(board: chess.Board, move: chess.Move):
    """Assume move is valid, call before pushing move in memory!"""

    response = RESPONSE_SUCCESS
    from_square, to_square = (move.from_square, move.to_square)
    move_san = board.san(move)
    logging.info(f'Making move {move_san}...')

    if board.is_castling(move):
        rook_move = _castle_rook_move(board, move)

        response = move(from_square, to_square, response)
        response = move(rook_move.from_square, rook_move.to_square, response)
    else: # Regular moves
        if board.is_capture(move):
            captured_piece = board.piece_at(to_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = _OFF_BOARD_PIECES[(piece_type, color)]

            # Remove captured piece
            response = move(to_square, off_board_place, response)
        elif board.is_en_passant(move):
            captured_square = _en_passant_captured(move)
            captured_piece = board.piece_at(captured_square)
            piece_type, color = (captured_piece.piece_type, captured_piece.color)
            off_board_place = _OFF_BOARD_PIECES[(piece_type, color)]

            # Remove captured piece
            response = move(captured_square, off_board_place, response)
        elif move.promotion:
            removed_piece = board.piece_at(move.from_square)
            piece_type, color = (removed_piece.piece_type, removed_piece.color)
            off_board_place_removed = _OFF_BOARD_PIECES[(piece_type, color)]
            off_board_place_promoted = _OFF_BOARD_PIECES[(move.promotion, color)]

            # Remove original piece off the board
            response = move(from_square, off_board_place_removed, response)

            # Set new piece to be moved
            from_square = off_board_place_promoted

        response = move(from_square, to_square, response)

    if response == RESPONSE_TIMEOUT:
        logging.warning(f'Move {move_san} timed out!')
    else:
        logging.info(f'Move {move_san} success!')

    return response

def move(board, from_square, to_square, prev_response = RESPONSE_SUCCESS):
    if prev_response == RESPONSE_SUCCESS:
        from_str = chess.square_name(from_square)
        to_str = chess.square_name(to_square)
        logging.info(f'Making move: {from_str} -> {to_str}')

        return _issue_command(_command(from_square, to_square))
    else:
        return prev_response
                                   
def _castle_rook_move(board: chess.Board, move: chess.Move):
    # Determine if the castling is kingside or queenside
    is_kingside = board.is_kingside_castling(move)
    
    king_from_square = move.from_square
    king_to_square = move.to_square

    # Calculate the rook's initial and final positions based on the king's movement
    if is_kingside:
        rook_from = king_from_square + 3  # Rook starts 3 squares right from the king
        rook_to = king_to_square - 1      # Rook ends up 1 square left from the king's destination
    else:
        rook_from = king_from_square - 4  # Rook starts 4 squares left from the king
        rook_to = king_to_square + 1      # Rook ends up 1 square right from the king's destination

    return chess.Move(rook_from, rook_to)

def _en_passant_captured(move: chess.Move):
    # Determine the direction of the pawn's movement to find the captured pawn's location
    direction = -8 if (move.to_square > move.from_square) else 8
    captured_square = move.to_square + direction
    return captured_square

def _command(from_square, to_square):
    # Shift the high byte by 8 to the left
    to_square_shifted = to_square << 8
    # Combine the high byte and low byte to form a 16-bit number
    command = to_square_shifted | from_square
    return command

def _issue_command(command):
    logging.info(f'Sending command {command}...')

    # 16 bits command
    for bit in range(16):
        bit_value = (command >> (15 - bit)) & 1

        GPIO.output(_PIN_OUT_DAT, GPIO.HIGH if bit_value else GPIO.LOW)
        
        # Toggle the clock to signal data is ready
        GPIO.output(_PIN_OUT_CLK, GPIO.HIGH)
        time.sleep(0.0001)    
        GPIO.output(_PIN_OUT_CLK, GPIO.LOW)
        time.sleep(0.0001)    

    # Wait for signal
    time_started = time.time()

    while _DELAY_TIMEOUT_MAX_S > time.time() - time_started:
        signal = GPIO.input(_PIN_IN_RESP)
        # Wait for low signal
        if signal == GPIO.LOW:
            if _DELAY_TIMEOUT_MIN_S > time.time() - time_started:
                logging.warning(f'Response too quick (<{_DELAY_TIMEOUT_MIN_S}s)!')
                return RESPONSE_TIMEOUT

            logging.info('Response success')
            return RESPONSE_SUCCESS
        time.sleep(_DELAY_WAIT_S)

    logging.warning(f'Response too slow (>{_DELAY_TIMEOUT_MAX_S}s)!')
    return RESPONSE_TIMEOUT


