import gpiod
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

chip = None
line_dat = None
line_clk = None
line_resp = None

def setup_communication(chip_name='/dev/gpiochip4'):
    global chip, line_dat, line_clk, line_resp
    chip = gpiod.Chip(chip_name)

    # Get lines for the pins

    line_dat = chip.get_line(PIN_OUT_DAT)
    line_clk = chip.get_line(PIN_OUT_CLK)
    line_resp = chip.get_line(PIN_IN_RESP)

    # Configure the lines
    line_dat.request(consumer="gpioout", type=gpiod.LINE_REQ_DIR_OUT)
    line_clk.request(consumer="gpioout", type=gpiod.LINE_REQ_DIR_OUT)
    line_resp.request(consumer="gpioin", type=gpiod.LINE_REQ_DIR_IN)

def close_communication():
    global chip, line_dat, line_clk, line_resp

    # Release the lines
    if line_dat is not None:
        line_dat.release()
    if line_clk is not None:
        line_clk.release()
    if line_resp is not None:
        line_resp.release()

    # Close the chip
    if chip is not None:
        chip.close()

    # Reset the variables to None
    line_dat = None
    line_clk = None
    line_resp = None
    chip = None

    logging.info("GPIO lines and chip have been released.")

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
            line_dat.set_value(1)
        else:
            line_dat.set_value(0)

        line_clk.set_value(1)
        time.sleep(0.2)
        line_clk.set_value(0)
        time.sleep(0.2)
    
    time.sleep(0.2)  # Simulate delay for the response signal check
    
    return wait_for_signal()

def wait_for_signal():
    start_time = time.time()
    while (time.time() - start_time) < DELAY_TIMEOUT_MAX_S:
        signal = line_resp.get_value()
        if signal == 0:  # Assuming low signal indicates a response
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

if __name__ == '__main__':
    main()
