import socket
import time
import logging
import argparse

# Delay configuration
DELAY_TIMEOUT_MIN_S = 0.1
DELAY_TIMEOUT_MAX_S = 30
DELAY_WAIT_S = 0.1

# Signal waiting return values
RESPONSE_TIMEOUT = 0
RESPONSE_SUCCESS = 1

# TCP/IP configuration
ip_address = '192.168.1.6'
port = 6001

def form_command(from_square, to_square, offset_x, offset_y) -> str:
    command_parts = [from_square, offset_x, offset_y, to_square]
    command_string = ' '.join(map(str, command_parts))
    return command_string

def issue_command(command, timeout_max=DELAY_TIMEOUT_MAX_S):
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

def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Send chess move command to robot.")
    parser.add_argument("from_square", type=int, help="Source square (0-63)")
    parser.add_argument("offset_x", type=int, help="Offset x (-100 to 100)")
    parser.add_argument("offset_y", type=int, help="Offset y (-100 to 100)")
    parser.add_argument("to_square", type=int, help="Destination square (0-63)")

    args = parser.parse_args()

    from_square = args.from_square
    to_square = args.to_square
    offset_x = args.offset_x
    offset_y = args.offset_y

    command = form_command(from_square, to_square, offset_x, offset_y)

    print(f'Command: {command}')

    result = issue_command(command)
    if result == RESPONSE_SUCCESS:
        logging.info("Command issued successfully")
    else:
        logging.error("Command failed")

if __name__ == '__main__':
    main()
