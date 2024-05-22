import socket
import time
import chess
import random
import logging

# TCP/IP configuration
ROBOT_IP = '192.168.1.6'  # Replace with your robot's actual IP address
ROBOT_PORT = 6001         # Replace with your robot's actual port number

# Delay configuration
DELAY_TIMEOUT_MIN_S = 0.1
DELAY_TIMEOUT_MAX_S = 10
DELAY_WAIT_S = 0.1

# Signal waiting return values
RESPONSE_TIMEOUT = 0
RESPONSE_SUCCESS = 1

def off_board_square(piece_type: chess.PieceType, color: chess.Color, perspective: chess.Color = chess.WHITE) -> int:
    pieces_white_perspective = {
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

    piece_value = pieces_white_perspective[(piece_type, color)]
    if perspective == chess.BLACK:
        # Flip groups
        if piece_value >= -6:
            piece_value -= 6
        else:
            piece_value += 6

    return piece_value

def form_command(from_square: chess.Square, to_square: chess.Square, offset_x: float = 0, offset_y: float = 0, perspective: chess.Color = chess.WHITE) -> str:
    # Convert to decimal percentage
    offset_x = int(max(min(offset_x * 100, 100), -100))
    offset_y = int(max(min(offset_y * 100, 100), -100))

    if perspective == chess.BLACK:
        # Invert square coordinates
        if 0 <= from_square <= 63:
            from_square = 63 - from_square
        if 0 <= to_square <= 63:
            to_square = 63 - to_square

        # Invert percentages to reflect direction of perspective
        offset_x = -offset_x
        offset_y = -offset_y

    # Form the command parts as integers
    command_parts = [from_square, offset_x, offset_y, to_square]
    
    # Format the command as a space-separated string
    command_string = ' '.join(map(str, command_parts))
    
    return command_string

def send_command_to_robot(ip, port, command, timeout_max=DELAY_TIMEOUT_MAX_S):
    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Set a timeout for the socket
        s.settimeout(timeout_max)
        
        # Connect to the robot server
        s.connect((ip, port))
        
        # Convert command to a space-separated string and encode to bytes
        message = command.encode('utf-8')
                    
        # Send the message to the robot server
        s.sendall(message)
        
        # Wait for and receive a response from the robot server
        start_time = time.time()
        while (time.time() - start_time) < timeout_max:
            try:
                response = s.recv(1024)
                if response:
                    print('Received', repr(response))
                    return RESPONSE_SUCCESS
            except socket.timeout:
                pass  # Continue waiting until timeout_max

        print(f"Response too slow (>{timeout_max}s)!")
        return RESPONSE_TIMEOUT

def main():
    logging.basicConfig(level=logging.INFO)
    
    from_square = random.randint(0, 63)
    to_square = random.randint(0, 63)

    logging.info(f"Moving from {from_square} to {to_square}")

    command = form_command(from_square, to_square)

    result = send_command_to_robot(ROBOT_IP, ROBOT_PORT, command)
    if result == RESPONSE_SUCCESS:
        logging.info("Command issued successfully")
    else:
        logging.error("Command failed")

if __name__ == '__main__':
    main()
