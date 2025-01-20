import socket
import chess
import logging
from typing import Optional

from src.core.board import PieceOffset, flip_square
from src.core.moves import PieceMover

logger = logging.getLogger(__name__)


class TCPRobotHand(PieceMover):
    def __init__(self, 
                 ip: str = "192.168.1.6", 
                 port: int = 6001, 
                 timeout: int = 60):
        """
        Initializes the TCPRobotHand with IP address, port, and timeout for socket connection.

        Args:
            ip (str): The IP address of the robot's server. 
            port (int): The port number for communication with the robot's server.
            timeout (int): The timeout for socket communication in seconds. 
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def reset(self) -> bool:
        """
        Resets the robot hand to its initial state by issuing a reset command.

        Returns:
            bool: True if the reset command succeeded and was acknowledged by the robot; False otherwise.
        """
        return self.issue_command("reset")

    def move_piece(
        self,
        from_square: int,
        to_square: int,
        color: chess.Color,
        origin_offset: PieceOffset,
    ) -> bool:
        """
        Moves a piece from one square to another using the robot hand, adjusting for perspective.
        
        Note: First row is at the bottom of the robot hand's perspective.

        Args:
            from_square (int): The starting square (0-63) in integer notation.
            to_square (int): The destination square (0-63) in integer notation.
            color (chess.Color): The color perspective (chess.WHITE or chess.BLACK) affecting board orientation.
            origin_offset (PieceOffset): The offset for piece placement on the square, adjusting in x and y directions.

        Returns:
            bool: True if the move command succeeded and was acknowledged by the robot; False otherwise.
        """
        command = self.form_move_command(from_square, to_square, color, origin_offset)
        return self.issue_command(command)

    def form_move_command(
        self,
        from_square: chess.Square,
        to_square: chess.Square,
        color: chess.Color,
        origin_offset: PieceOffset,
    ) -> str:
        """
        Forms a command string for moving a piece, accounting for offset and color perspective.
        
        Note: First row is at the bottom of the robot hand's perspective.

        Args:
            from_square (chess.Square): The starting square in 0-63 notation.
            to_square (chess.Square): The destination square in 0-63 notation.
            color (chess.Color): The color perspective (chess.WHITE or chess.BLACK), flipping board orientation if black.
            origin_offset (PieceOffset): Offset for piece placement in x and y directions, relative to the square's center.

        Returns:
            str: The formatted command string for the robot, including square positions and offsets.
        """
        # Last row is next to the robot hand
        # TODO: Make this opposite
        if color == chess.BLACK:
            from_square = flip_square(from_square)
            to_square = flip_square(to_square)

        # Convert offsets to integer percentages
        offset_x = int(max(min(origin_offset.x * 100, 100), -100))
        offset_y = int(max(min(origin_offset.y * 100, 100), -100))

        # Form command parts as space-separated string
        command_parts = [from_square, offset_x, offset_y, to_square]
        move_string = " ".join(map(str, command_parts))
        command_string = "move " + move_string

        return command_string

    def issue_command(self, command: str, timeout: Optional[int] = None) -> bool:
        """
        Sends a command to the robot hand and waits for a response, confirming command success or failure.

        Args:
            command (str): The command string to send to the robot.
            timeout (Optional[int]): Timeout in seconds for the socket connection. Defaults to the instance timeout.

        Returns:
            bool: True if the command was successfully acknowledged by the robot server with a "success" response;
                  False otherwise.
        """
        if timeout is None:
            timeout = self.timeout

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as robot_socket:
                robot_socket.settimeout(timeout)
                robot_socket.connect((self.ip, self.port))
                logger.info(f"Connected to TCP robot hand {self.ip}:{self.port}")
                logger.info(f"Sending TCP command: {command}")

                robot_socket.sendall(command.encode("utf-8"))

                response = robot_socket.recv(1024)
                if response:
                    decoded_response = response.decode("utf-8").strip()
                    logger.info(f"Received TCP response: {decoded_response}")
                    if decoded_response == "success":
                        return True
            return False
        except Exception as e:
            logger.error(f"Could not connect to TCP robot hand {self.ip}:{self.port}! Error: {e}")
            return False