import RPi.GPIO as GPIO
import logging
import time
import chess
import random

# Pin configuration
PIN_OUT_DAT = 22
PIN_OUT_CLK = 27
PIN_IN_RESP = 17

# Delay configuration
DELAY_TIMEOUT_MIN_S = 0.1
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

def setup_communication():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_OUT_DAT, GPIO.OUT)
    GPIO.setup(PIN_OUT_CLK, GPIO.OUT)
    GPIO.setup(PIN_IN_RESP, GPIO.IN)

def close_communication():
    GPIO.cleanup()
    logging.info("GPIO pins have been released.")

def off_board_square(piece_type, color):
    return OFF_BOARD_PIECES[(piece_type, color)]

def form_command(from_square, to_square, perspective=chess.WHITE):
    if perspective == chess.BLACK:
        from_square = 63 - from_square
        to_square = 63 - to_square

    command = (from_square << 8) | to_square
    return command

def issue_command(command):
    for bit in range(16):
        bit_value = (command >> (15 - bit)) & 1

        if bit_value:
            GPIO.output(PIN_OUT_DAT, GPIO.HIGH)
        else:
            GPIO.output(PIN_OUT_DAT, GPIO.LOW)

        GPIO.output(PIN_OUT_CLK, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(PIN_OUT_CLK, GPIO.LOW)
        time.sleep(0.2)
    
    time.sleep(0.1)  # Simulate delay for the response signal check
    
    return wait_for_signal()

def wait_for_signal():
    start_time = time.time()
    while (time.time() - start_time) < DELAY_TIMEOUT_MAX_S:
        signal = GPIO.input(PIN_IN_RESP)
        if signal == GPIO.LOW:  # Assuming low signal indicates a response
            elapsed = time.time() - start_time
            if elapsed < DELAY_TIMEOUT_MIN_S:
                logging.info(f"Response too quick (<{DELAY_TIMEOUT_MIN_S}s)!")
                return RESPONSE_TIMEOUT
            else:
                logging.info("Response success")
                return RESPONSE_SUCCESS
        time.sleep(DELAY_WAIT_S)
    logging.info(f"Response too slow (>{DELAY_TIMEOUT_MAX_S}s)!")
    return RESPONSE_TIMEOUT

def main():
    logging.basicConfig(level=logging.INFO)
    
    from_square = random.randint(0, 63)
    to_square = random.randint(0, 63)

    setup_communication()

    logging.info(f"Moving from {from_square} to {to_square}")

    command = form_command(from_square, to_square)

    result = issue_command(command)
    if result == RESPONSE_SUCCESS:
        logging.info("Command issued successfully")
    else:
        logging.error("Command failed")

    close_communication()

if __name__ == '__main__':
    main()
