import logging
import random
import time
import chess

# Constants
PIN_OUT_DAT = 11
PIN_OUT_CLK = 13
PIN_IN_RESP = 15

DELAY_TIMEOUT_MIN_S = 0.5
DELAY_TIMEOUT_MAX_S = 10
DELAY_WAIT_S = 0.1

RESPONSE_TIMEOUT = 0
RESPONSE_SUCCESS = 1

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

class MockGPIO:
    BOARD = 'BOARD'
    OUT = 'OUT'
    IN = 'IN'
    LOW = 0
    HIGH = 1

    @staticmethod
    def setmode(mode):
        logging.info(f"Mock set mode: {mode}")

    @staticmethod
    def setup(pin, mode):
        logging.info(f"Mock setup pin: {pin}, mode: {mode}")

    @staticmethod
    def output(pin, state):
        logging.info(f"Mock set pin: {pin}, state: {state}")

    @staticmethod
    def input(pin):
        # Simulate the response pin
        return MockGPIO.HIGH if random.random() > 0.5 else MockGPIO.LOW

    @staticmethod
    def cleanup():
        logging.info("Mock cleanup")

def setup_communication():
    logging.info("Setting up GPIO pins...")

    MockGPIO.setmode(MockGPIO.BOARD)

    # Pin directions
    MockGPIO.setup(PIN_OUT_CLK, MockGPIO.OUT)
    MockGPIO.setup(PIN_OUT_DAT, MockGPIO.OUT)
    MockGPIO.setup(PIN_IN_RESP, MockGPIO.IN)

    # Initial values
    MockGPIO.output(PIN_OUT_CLK, MockGPIO.LOW)
    MockGPIO.output(PIN_OUT_DAT, MockGPIO.LOW)

def close_communication():
    logging.info("Cleaning up GPIO pins...")

    MockGPIO.cleanup()

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

        MockGPIO.output(PIN_OUT_DAT, MockGPIO.HIGH if bit_value else MockGPIO.LOW)

        # Toggle the clock to signal data is ready
        MockGPIO.output(PIN_OUT_CLK, MockGPIO.HIGH)
        time.sleep(0.0001)
        MockGPIO.output(PIN_OUT_CLK, MockGPIO.LOW)
        time.sleep(0.0001)

    # Wait for signal
    time_started = time.time()

    while DELAY_TIMEOUT_MAX_S > time.time() - time_started:
        signal = MockGPIO.input(PIN_IN_RESP)
        if signal == MockGPIO.HIGH:
            if DELAY_TIMEOUT_MIN_S > time.time() - time_started:
                logging.warning(f"Response too quick (<{DELAY_TIMEOUT_MIN_S}s)!")
                return RESPONSE_TIMEOUT

            logging.info("Response success")
            return RESPONSE_SUCCESS
        time.sleep(DELAY_WAIT_S)

    logging.warning(f"Response too slow (>{DELAY_TIMEOUT_MAX_S}s)!")
    return RESPONSE_TIMEOUT

def is_available():
    signal = MockGPIO.input(PIN_IN_RESP)
    return signal == MockGPIO.HIGH