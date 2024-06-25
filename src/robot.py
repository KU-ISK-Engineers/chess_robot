import socket
import time
import chess
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
DELAY_TIMEOUT = 30

# Signal waiting return values
COMMAND_FAILURE = 0
COMMAND_SUCCESS = 1

ip_address = '192.168.1.6'
port = 6001

def setup_communication(new_ip_address: str = '192.168.1.6', new_port: int = 6001):
    global ip_address, port

    ip_address = new_ip_address
    port = new_port

def reset_state():
    return issue_command("99 99 99 99")

def off_board_square(piece_type: chess.PieceType, color: chess.Color) -> int:
    return OFF_BOARD_SQUARES[(piece_type, color)]

def form_command(from_square: chess.Square, to_square: chess.Square, offset: SquareOffset = SQUARE_CENTER, perspective: chess.Color = chess.WHITE) -> str:
    # Convert to decimal percentage
    offset_x = int(max(min(offset.x * 100, 100), -100))
    offset_y = int(max(min(offset.y * 100, 100), -100))

    if perspective == chess.BLACK:
        # Flip off board squares
        if -6 <= from_square < 0:
            from_square -= 6
        else:
            from_square += 6

        if -6 <= to_square < 0:
            to_square -= 6
        else:
            to_square += 6

    # Form the command parts as integers
    command_parts = [from_square, offset_x, offset_y, to_square]
    
    # Format the command as a space-separated string
    command_string = ' '.join(map(str, command_parts))
    
    return command_string

def issue_command(command: str, timeout_max=DELAY_TIMEOUT) -> int:
    robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    robot_socket.settimeout(timeout_max)

    try:
        robot_socket.connect((ip_address, port))
        logging.info(f"Connected to {ip_address}:{port}")
        
        # Convert command to a space-separated string and encode to bytes
        message = command.encode('utf-8')
                    
        # Send the message to the robot server
        robot_socket.sendall(message)
        
        # Wait for and receive a response from the robot server
        response = robot_socket.recv(1024)
        if response:
            decoded_response = response.decode('utf-8').strip()
            if decoded_response == "success":
                return COMMAND_SUCCESS

        return COMMAND_FAILURE
    except Exception as e:
        logging.exception(e)
        return COMMAND_FAILURE
    finally:
        robot_socket.close()

