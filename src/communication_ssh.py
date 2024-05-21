import paramiko
import logging
import time
import chess
import random
from pprint import pprint

# TODO: Modify script to include distances between 

# Constants for SSH connection
IP_ADDRESS = "192.168.0.248"  # Replace with your Raspberry Pi's IP address
USERNAME = "user"             # Replace with your Raspberry Pi's username
PASSWORD = "1234567890"       # Replace with your Raspberry Pi's password

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

ssh = None

def off_board_square(piece_type, color):
    return OFF_BOARD_PIECES[(piece_type, color)]

def generate_pinctrl_commands():
    commands = [
        # Output pins
        f"pinctrl set {PIN_OUT_CLK},{PIN_OUT_DAT} op",

        # Input pins
        f"pinctrl set {PIN_IN_RESP} ip",

        # Initial values
        f"pinctrl set {PIN_OUT_CLK},{PIN_OUT_DAT} dl",
    ]
    return commands

def form_command(from_square, to_square, perspective = chess.WHITE):
    if perspective == chess.BLACK:
        from_square = 63 - from_square
        to_square = 63 - to_square

    command = (from_square << 8) | to_square
    return command

def generate_issue_command_sequence(command):
    sequence = []
    for bit in range(16):
        bit_value = (command >> (15 - bit)) & 1

        if bit_value:
            bit_value = "dh"
        else:
            bit_value = "dl"

        sequence.append(f"pinctrl set {PIN_OUT_DAT} {bit_value}")
        sequence.append(f"pinctrl set {PIN_OUT_CLK} dh")
        sequence.append(f"sleep 0.08")
        sequence.append(f"pinctrl set {PIN_OUT_CLK} dl")
        sequence.append("sleep 0.08")  # Sleep to simulate delay for clock pulse
    
    sequence.append("sleep 0.1")  # Simulate delay for the response signal check
    # sequence.append(f"pinctrl get {PIN_IN_RESP}")
    
    return sequence

def wait_for_signal():
    wait_commands = []
    wait_commands.append(f"start_time=$(date +%s.%N)")
    wait_commands.append(f"while (( $(echo \"$(date +%s.%N) - $start_time < {DELAY_TIMEOUT_MAX_S}\" | bc -l) )); do")
    wait_commands.append(f"  signal=$(pinctrl get {PIN_IN_RESP})")
    wait_commands.append(f"  if [[ \"$signal\" == *\"lo\"* ]]; then")
    wait_commands.append(f"    elapsed=$(echo \"$(date +%s.%N) - $start_time\" | bc)")
    wait_commands.append(f"    if (( $(echo \"$elapsed < {DELAY_TIMEOUT_MIN_S}\" | bc -l) )); then")
    wait_commands.append(f"      echo \"Response too quick (<{DELAY_TIMEOUT_MIN_S}s)!\"")
    wait_commands.append(f"      exit {RESPONSE_TIMEOUT}")
    wait_commands.append(f"    else")
    wait_commands.append(f"      echo \"Response success\"")
    wait_commands.append(f"      exit {RESPONSE_SUCCESS}")
    wait_commands.append(f"    fi")
    wait_commands.append(f"  fi")
    wait_commands.append(f"  sleep {DELAY_WAIT_S}")
    wait_commands.append(f"done")
    wait_commands.append(f"echo \"Response too slow (>{DELAY_TIMEOUT_MAX_S}s)!\"")
    wait_commands.append(f"exit {RESPONSE_TIMEOUT}")
    return "\n".join(wait_commands)


def execute_remote_command(ssh, commands):
    # Join all commands into a single command string separated by " && "
    command_string = " && ".join(commands)
    stdin, stdout, stderr = ssh.exec_command(command_string)

    stdout_output = stdout.read().decode()
    stderr_output = stderr.read().decode()

    if stdout_output:
        logging.info(stdout_output)

    if stderr_output:
        logging.error(stderr_output)
        return False
    
    return True

def setup_communication():
    global ssh

    logging.info("Setting up SSH...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(IP_ADDRESS, username=USERNAME, password=PASSWORD)

    logging.info("Setting up GPIO pins...")

    commands = [
        # Output pins
        f"pinctrl set {PIN_OUT_CLK},{PIN_OUT_DAT} op",

        # Input pins
        f"pinctrl set {PIN_IN_RESP} ip",

        # Initial values
        f"pinctrl set {PIN_OUT_CLK},{PIN_OUT_DAT} dl",
    ]

    return execute_remote_command(ssh, commands)

def issue_command(command):
    global ssh
    if ssh is None:
        raise RuntimeError("SSH connection is not established")
    
    commands = generate_issue_command_sequence(command)

    # Add the signal wait commands
    signal_wait_commands = wait_for_signal()
    commands.append(signal_wait_commands)
    
    execute_remote_command(ssh, commands)


def close_communication():
    global ssh
    if ssh is not None:
        logging.info("Turning off SSH connection...")
        ssh.close()
        ssh = None

def main():
    logging.basicConfig(level=logging.INFO)

    setup_communication()
    
    from_square = random.randint(0, 63)
    to_square = random.randint(0, 63)

    logging.info(f"Moving from {from_square} to {to_square}")

    command = form_command(from_square, to_square)

    issue_command(command)

    close_communication()

if __name__ == '__main__':
    main()
