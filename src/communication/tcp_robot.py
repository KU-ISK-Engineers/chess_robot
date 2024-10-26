import socket
import chess
import logging
from typing import Optional

from src.core.board import OFFSET_SQUARE_CENTER, PieceOffset
from src.core.moves import PieceMover

logger = logging.getLogger(__name__)


# TODO: Write specific perspectives


class TCPRobotHand(PieceMover):
    def __init__(
        self, ip: str = "192.168.1.6", port: int = 6001, timeout: int = 30
    ):
        """Initializes the TCPRobotHand with IP address, port, and timeout for socket connection.

        Args:
            ip (str): The IP address of the robot's server. Defaults to "192.168.1.6".
            port (int): The port number for communication with the robot's server. Defaults to 6001.
            timeout (int): The timeout for socket communication in seconds. Defaults to 30 seconds.
        """
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def reset(self) -> bool:
        """Resets the robot hand to its initial state by issuing a reset command.

        Returns:
            bool: True if the reset command succeeded, False otherwise.
        """
        return self.issue_command("99 99 99 99")

    def move_piece(
        self,
        from_square: int,
        to_square: int,
        piece_offset: PieceOffset = OFFSET_SQUARE_CENTER,
        physical_perspective: chess.COLOR = chess.WHITE,
    ) -> bool:
        """Moves a piece from one square to another using the robot hand, adjusting for perspective.

        Args:
            from_square (int): The starting square in integer notation.
            to_square (int): The destination square in integer notation.
            piece_offset (PieceOffset): Offset for the piece's placement on the square. Defaults to the center.
            physical_perspective (chess.COLOR): The color perspective (chess.WHITE or chess.BLACK) affecting board orientation.

        Returns:
            bool: True if the move command succeeded, False otherwise.
        """
        command = self.form_command(
            from_square, to_square, piece_offset, physical_perspective
        )
        return self.issue_command(command)

    def form_command(
        self,
        from_square: chess.Square,
        to_square: chess.Square,
        offset: PieceOffset = OFFSET_SQUARE_CENTER,
        perspective: chess.Color = chess.WHITE,
    ) -> str:
        """Forms a command string for moving a piece, accounting for offset and perspective.

        Args:
            from_square (chess.Square): The starting square in chess notation.
            to_square (chess.Square): The destination square in chess notation.
            offset (PieceOffset): Offset for piece placement in x and y directions. Defaults to the square center.
            perspective (chess.Color): The color perspective (chess.WHITE or chess.BLACK). If chess.BLACK, flips board orientation.

        Returns:
            str: The formatted command string for the robot, including square positions and offsets.
        """
        # Convert offsets to integer percentages
        offset_x = int(max(min(offset.x * 100, 100), -100))
        offset_y = int(max(min(offset.y * 100, 100), -100))

        if perspective == chess.BLACK:
            # Adjust square positions for black perspective
            if -6 <= from_square < 0:
                from_square -= 6
            else:
                from_square += 6

            if -6 <= to_square < 0:
                to_square -= 6
            else:
                to_square += 6

        # Form command parts as space-separated string
        command_parts = [from_square, offset_x, offset_y, to_square]
        command_string = " ".join(map(str, command_parts))

        return command_string

    def issue_command(self, command: str, timeout: Optional[int] = None) -> bool:
        """Sends a command to the robot hand and waits for a response, confirming command success or failure.

        Args:
            command (str): The command string to send to the robot.
            timeout (Optional[int]): Timeout in seconds for the socket connection. Defaults to the instance timeout.

        Returns:
            bool: True if the command was successfully acknowledged by the robot, False otherwise.
        """
        if timeout is None:
            timeout = self.timeout

        # Initialize socket connection to robot
        robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        robot_socket.settimeout(timeout)

        try:
            robot_socket.connect((self.ip, self.port))
            logger.info(f"Connected to {self.ip}:{self.port}")

            # Send command to the robot server
            message = command.encode("utf-8")
            robot_socket.sendall(message)

            # Receive and decode the response from the robot server
            response = robot_socket.recv(1024)
            if response:
                decoded_response = response.decode("utf-8").strip()
                if decoded_response == "success":
                    return True

            return False
        except Exception as e:
            logger.exception("Error issuing command:", exc_info=e)
            return False
        finally:
            robot_socket.close()
