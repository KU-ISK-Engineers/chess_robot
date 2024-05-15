import RPi.GPIO as GPIO
import logging
import time
import chess

# Pin configuration
PIN_OUT_DAT = 11
PIN_OUT_CLK = 13
PIN_IN_RESP = 15

# Delay configuration
DELAY_TIMEOUT_MIN_S = 0.5
DELAY_TIMEOUT_MAX_S = 10
DELAY_WAIT_S = 0.1

# Signal waiting return values
RESPONSE_TIMEOUT = 0
RESPONSE_SUCCESS = 1

# Off the board pieces identifiers
OFF_BOARD_PIECES = {
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


def off_board_square(piece_type, color):
    return OFF_BOARD_PIECES[(piece_type, color)]


def setup_communication():
    logging.info("Setting up GPIO pins...")

    GPIO.setmode(GPIO.BOARD)

    # Pin directions
    GPIO.setup(PIN_OUT_CLK, GPIO.OUT)
    GPIO.setup(PIN_OUT_DAT, GPIO.OUT)
    GPIO.setup(PIN_IN_RESP, GPIO.IN)

    # Initial values
    GPIO.output(PIN_OUT_CLK, GPIO.LOW)
    GPIO.output(PIN_OUT_DAT, GPIO.LOW)


def close_communication():
    logging.info("Cleaning up GPIO pins...")

    GPIO.cleanup()


def form_command(from_square, to_square):
    # Shift the high byte by 8 to the left
    to_square_shifted = to_square << 8
    # Combine the high byte and low byte to form a 16-bit number
    command = to_square_shifted | from_square
    return command


def issue_command(command):
    logging.info(f"Sending command {command}...")

    # 16 bits command
    for bit in range(16):
        bit_value = (command >> (15 - bit)) & 1

        GPIO.output(PIN_OUT_DAT, GPIO.HIGH if bit_value else GPIO.LOW)

        # Toggle the clock to signal data is ready
        # TODO: If necessary switch to pigpio for more accurate timing precision
        GPIO.output(PIN_OUT_CLK, GPIO.HIGH)
        time.sleep(0.0001)
        GPIO.output(PIN_OUT_CLK, GPIO.LOW)
        time.sleep(0.0001)

    # Wait for signal
    time_started = time.time()

    while DELAY_TIMEOUT_MAX_S > time.time() - time_started:
        signal = GPIO.input(PIN_IN_RESP)
        if signal == GPIO.HIGH:
            if DELAY_TIMEOUT_MIN_S > time.time() - time_started:
                logging.warning(f"Response too quick (<{DELAY_TIMEOUT_MIN_S}s)!")
                return RESPONSE_TIMEOUT

            logging.info("Response success")
            return RESPONSE_SUCCESS
        time.sleep(DELAY_WAIT_S)

    logging.warning(f"Response too slow (>{DELAY_TIMEOUT_MAX_S}s)!")
    return RESPONSE_TIMEOUT


def is_available():
    signal = GPIO.input(PIN_IN_RESP)
    return signal == GPIO.HIGH
