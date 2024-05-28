import socket
import time
import chess
import random
import logging
from .board import SquareOffset, SQUARE_CENTER

OFF_BOARD_SQUARES = {
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

# Delay configuration
DELAY_TIMEOUT_MIN_S = 0.1
DELAY_TIMEOUT_MAX_S = 30
DELAY_WAIT_S = 0.1

# Signal waiting return values
RESPONSE_TIMEOUT = 0
RESPONSE_SUCCESS = 1

ip_address = '192.168.1.6'
port = 6001

def setup_communication(new_ip_address: str = '192.168.1.6', new_port: int = 6001):
    global ip_address, port

    ip_address = new_ip_address
    port = new_port

def off_board_square(piece_type: chess.PieceType, color: chess.Color) -> int:
    return OFF_BOARD_SQUARES[(piece_type, color)]

def form_command(from_square: chess.Square, to_square: chess.Square, offset: SquareOffset = SQUARE_CENTER, perspective: chess.Color = chess.WHITE) -> str:
    # Convert to decimal percentage
    offset_x = int(max(min(offset.x * 100, 100), -100))
    offset_y = int(max(min(offset.y * 100, 100), -100))

    # TODO: Test this part
    if perspective == chess.BLACK:
        # Invert square coordinates
        if 0 <= from_square <= 63:
            from_square = 63 - from_square
        else:
            # Flip groups
            if from_square >= -6:
                from_square -= 6
            else:
                from_square += 6

        if 0 <= to_square <= 63:
            to_square = 63 - to_square
        else:
            # Flip groups
            if to_square >= -6:
                to_square -= 6
            else:
                to_square += 6

        # Invert percentages to reflect direction of perspective
        offset_x = -offset_x
        offset_y = -offset_y

    # Form the command parts as integers
    command_parts = [from_square, offset_x, offset_y, to_square]
    
    # Format the command as a space-separated string
    command_string = ' '.join(map(str, command_parts))
    
    return command_string

def issue_command(command, timeout_max=DELAY_TIMEOUT_MAX_S):
    try:
        robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        robot_socket.settimeout(DELAY_TIMEOUT_MAX_S)
        robot_socket.connect((ip_address, port))
        logging.info(f"Connected to {ip_address}:{port}")
        
        # Convert command to a space-separated string and encode to bytes
        message = command.encode('utf-8')
                    
        # Send the message to the robot server
        robot_socket.sendall(message)
        
        # Wait for and receive a response from the robot server
        start_time = time.time()
        while (time.time() - start_time) < timeout_max:
            try:
                response = robot_socket.recv(1024)
                if response:
                    decoded_response = response.decode('utf-8').strip()
                    if decoded_response == "success":
                        return RESPONSE_SUCCESS
                    else:
                        return RESPONSE_TIMEOUT
            except socket.timeout:
                pass  # Continue waiting until timeout_max

        print(f"Response too slow (>{timeout_max}s)!")
        return RESPONSE_TIMEOUT
    except Exception:
        return RESPONSE_TIMEOUT

def main():
    # TCP/IP configuration
    robot_ip = '192.168.1.6'  # Replace with your robot's actual IP address
    robot_port = 6001         # Replace with your robot's actual port number

    logging.basicConfig(level=logging.INFO)

    setup_communication(robot_ip, robot_port)
    
    from_square = random.randint(0, 63)
    to_square = random.randint(0, 63)

    logging.info(f"Moving from {from_square} to {to_square}")

    command = form_command(from_square, to_square)
    result = issue_command(command)
    if result == RESPONSE_SUCCESS:
        logging.info("Command issued successfully")
    else:
        logging.error("Command failed")

if __name__ == '__main__':
    main()
