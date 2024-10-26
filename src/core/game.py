from typing import Optional
import logging

import chess
import chess.engine

from src.core.board import PhysicalBoard, BoardDetection, boards_are_equal
from src.core.moves import PieceMover, reflect_move, identify_move, iter_reset_board

logger = logging.getLogger(__name__)

HUMAN = 0
ROBOT = 1


# TODO: Check if perspectives align
class Game:
    """Represents a game of chess played on a physical board with robot and human players.

    Attributes:
        detection (BoardDetection): Instance responsible for detecting the board's state.
        depth (int): The depth of search for the engine's move calculations.
        engine (chess.engine.SimpleEngine): The chess engine used to calculate moves.
        piece_mover (PieceMover): Responsible for physically moving pieces on the board.
        board (PhysicalBoard): Represents the physical state of the chess board.
        player (int): Indicates the current player (HUMAN or ROBOT).
        player_color (chess.Color): The color that the human player controls (chess.WHITE or chess.BLACK).
        resigned (bool): Flag indicating if a player has resigned.
    """

    def __init__(
        self,
        detection: BoardDetection,
        piece_mover: PieceMover,
        engine: chess.engine.SimpleEngine,
        chess_board: Optional[chess.Board] = None,
        player_color: chess.Color = chess.WHITE,
        depth: int = 4,
    ) -> None:
        """Initializes the Game with detection, movement, engine, board, player color, and depth.

        Args:
            detection (BoardDetection): The detection system to capture the board's state.
            piece_mover (PieceMover): The system that physically moves pieces.
            engine (chess.engine.SimpleEngine): The chess engine used for move calculations.
            chess_board (Optional[chess.Board]): Initial logical state of the chess board. Defaults to a new game.
            player_color (chess.Color): The color that the human player controls (chess.WHITE or chess.BLACK).
            depth (int): The search depth for the engine's move calculations. Defaults to 4.
        """
        self.detection = detection
        self.depth = depth
        self.engine = engine
        self.piece_mover = piece_mover

        if not chess_board:
            chess_board = chess.Board()

        self.board = PhysicalBoard(chess_board=chess_board, perspective=player_color)

        if player_color == chess.WHITE:
            self.player = HUMAN
        else:
            self.player = ROBOT

        self.resigned = False
        self.piece_mover.reset()

    def reset_board(
        self,
        chess_board: Optional[chess.Board] = None,
        player_color: Optional[chess.Color] = None,
        move_pieces: bool = False,
    ) -> None:
        """Resets the board to a new or specified state with the given perspective.

        Args:
            chess_board (Optional[chess.Board]): A new chess board state. Defaults to a new game.
            player_color (chess.Color): The color that the human player controls (chess.WHITE or chess.BLACK).
            move_pieces (bool): If True, moves pieces to match the expected board state.

        Raises:
            RuntimeError: If the board fails to reset to the expected state when `move_pieces` is True.
        """
        if player_color is None:
            player_color = self.board.perspective

        if not chess_board:
            board = chess.Board()

        self.board = PhysicalBoard(chess_board=board, perspective=player_color)

        fen = self.board.chess_board.fen()
        logger.info(
            f"Resetting board {'white' if player_color == chess.WHITE else 'black'} perspective FEN {fen}"
        )

        if move_pieces and not self._reshape_board(self.board):
            if not self._reshape_board(self.board):
                raise RuntimeError("Failed to reshape the board")

        if self.board.perspective == chess.WHITE:
            self.player = HUMAN
        else:
            self.player = ROBOT

        self.resigned = False
        self.piece_mover.reset()

    def set_depth(self, depth: int = 4) -> None:
        """Sets the depth for engine's move calculations and configures the engine's skill level.

        Args:
            depth (int): The depth level for the chess engine calculations. Defaults to 4.
        """
        # FIXME: Does not work, rename method, fix logic
        self.depth = depth
        self.engine.configure({"Skill Level": depth})

    def robot_makes_move(
        self, move: Optional[chess.Move] = None
    ) -> Optional[chess.Move]:
        """Executes the robot's move on the physical board.

        If no move is provided, it calculates the move using the chess engine.

        Args:
            move (Optional[chess.Move]): The move to execute. If None, the engine calculates the move.

        Returns:
            Optional[chess.Move]: The move made by the robot, or None if an error occurs.
        """
        new_board = self.detection.capture_board(perspective=self.board.perspective)
        if not new_board:
            return None

        if not boards_are_equal(self.board.chess_board, new_board.chess_board):
            logger.info(
                "Detected board does not match previous legal board for robot to move, waiting to reposition"
            )
            return None

        if move is None:
            result = self.engine.play(
                self.board.chess_board, chess.engine.Limit(depth=self.depth)
            )
            move = result.move

        logger.info("Robot making move %s", move and move.uci())

        if not move or move not in self.board.chess_board.legal_moves:
            logger.error("Invalid robot move: %s", move and move.uci())
            return None

        self.board.piece_offsets = new_board.piece_offsets
        if not reflect_move(self.piece_mover, self.board, move):
            return None

        self.player = HUMAN
        self.board.chess_board.push(move)
        return move

    def player_made_move(self) -> tuple[Optional[chess.Move], bool]:
        """Detects and validates the move made by the human player.

        Returns:
            tuple[Optional[chess.Move], bool]: The detected move and a boolean indicating if it was legal.
        """
        new_board = self.detection.capture_board(perspective=self.board.perspective)
        if not new_board:
            return None, False

        move, legal = identify_move(self.board.chess_board, new_board.chess_board)
        if move:
            logger.info(
                f"Player made {'legal' if legal else 'illegal'} move {move.uci()}"
            )
            if legal:
                self.board.chess_board.push(move)
                self.board.piece_offsets = new_board.piece_offsets
                self.player = ROBOT

        return move, legal

    def result(self) -> str:
        """Determines the current game result from the player's perspective.

        Returns:
            str: The result of the game ("1-0", "0-1", "1/2-1/2", or "resigned").
        """
        # TODO: Win / lose not on white or black, but on human or robot
        if not self.resigned:
            return self.board.chess_board.result()

        return "resigned"

    def resign_player(self):
        """Sets the player's status to resigned."""
        self.resigned = True

    def chess_board(self) -> chess.Board:
        """Returns the current logical chess board state.

        Returns:
            chess.Board: The current logical state of the chess board.
        """
        return self.board.chess_board

    def _reshape_board(self, expected_board: PhysicalBoard) -> bool:
        """Adjusts the physical board to match the expected board state.

        Args:
            expected_board (PhysicalBoard): The target board state to align the physical board with.

        Returns:
            bool: True if the board was successfully reshaped, False otherwise.
        """
        logger.info("Reshaping game board")

        current_board = self.board

        done = False
        while not done:
            current_board = self.detection.capture_board(
                perspective=expected_board.perspective
            )
            if not current_board:
                continue

            moved, done = iter_reset_board(self.piece_mover, self.board, expected_board)
            if not moved:
                break

        if done and current_board:
            self.board = current_board
        return done
