import socket
import chess
import logging

from src.core.board import PieceOffset, flip_square
from src.core.moves import PieceMover

logger = logging.getLogger(__name__)


class TCPRobotHand(PieceMover):
    def __init__(self, ip: str = "192.168.1.6", port: int = 6001, timeout: int = 60):
        """
        Initializes the TCPRobotHand with IP address, port, and timeout for socket connection.

        Args:
            ip (str): The IP address of the robot hand.
            port (int): The port number for communication with the robot hand.
            timeout (int): The timeout for socket communication in seconds.
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout

        self.robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.robot_socket.settimeout(timeout)
        self._connect()

    def _connect(self) -> bool:
        try:
            self.robot_socket.connect((self.ip, self.port))
            logger.info(f"Connected to TCP robot hand {self.ip}:{self.port}")
            return True
        except socket.error as e:
            logger.error(
                f"Could not connect to TCP robot hand {self.ip}:{self.port}! Error: {e}"
            )
            return False

    def __del__(self):
        self.robot_socket.close()

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

    def issue_command(self, command: str) -> bool:
        """
        Sends a command to the robot hand and waits for a response, confirming command success or failure.

        Args:
            command (str): The command string to send to the robot.

        Returns:
            bool: True if the command was successfully acknowledged by the robot server with a "success" response;
                  False otherwise.
        """
        logger.info(f"Sending TCP command: {command}")

        try:
            self.robot_socket.sendall(command.encode("utf-8"))
            response = self.robot_socket.recv(1024)
            if response:
                decoded_response = response.decode("utf-8").strip()
                logger.info(f"Received TCP response: {decoded_response}")
                return decoded_response == "success"
            else:
                logger.warning("Received no TCP response")
        except (ConnectionResetError, BrokenPipeError) as e:
            logger.error(
                f"No connection to TCP robot hand {self.ip}:{self.port}, attempting reconnect! Error: {e}"
            )
            if self._connect():
                return self.issue_command(command)
        except socket.error as e:
            logger.error(
                f"Could not connect to TCP robot hand {self.ip}:{self.port}! Error: {e}"
            )

        return False
