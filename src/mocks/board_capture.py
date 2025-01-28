from typing import Optional
import chess
import chess.engine
from src.core.board import BoardCapture, PhysicalBoard
from src.core.game import Game, Player


class SimulatedBoardCapture(BoardCapture):
    """Mock implementation of the `BoardCapture` class for testing purposes.

    This mock simulates a chessboard capture system that tracks the game state and
    alternates between the player's and robot's turns. On the player's turn, it
    generates a move using an engine, updates the board, and returns the updated
    `PhysicalBoard` instance. On the robot's turn, it returns the current state of
    the `PhysicalBoard` without any changes.

    Attributes:
        engine (chess.engine.SimpleEngine): The chess engine instance used to generate moves.
        game (Optional[Game]): The current game instance being tracked.
    """

    def __init__(
        self, engine: chess.engine.SimpleEngine, game: Optional[Game] = None
    ) -> None:
        """
        Initializes the mock board capture with an engine for move generation.
        Note: A `Game` instance must be set before `capture_board` can be used.

        Args:
            engine (chess.engine.SimpleEngine): The engine used to generate moves on the player's turn.
            game (Optional[Game]): The game instance to track (optional at initialization).
        """
        self.engine = engine
        self.game = game
        self.engine.configure({"Skill Level": 4})

    def track_game(self, game: Game) -> None:
        """Associates a game instance with this board capture instance.

        Args:
            game (Game): The game instance to be tracked.
        """
        self.game = game

    def capture_board(self, human_color: chess.Color) -> Optional[PhysicalBoard]:
        """Captures and updates the state of the physical board based on whose turn it is.

        On the player's turn (HUMAN), this method generates a move using
        the provided chess engine, updates the board, and returns the updated `PhysicalBoard`.
        On the robot's turn (ROBOT), it returns the current `PhysicalBoard` without any changes.

        Args:
            human_perspective (chess.Color): The color perspective (`chess.WHITE` or `chess.BLACK`)
                from which to capture the board's state.

        Returns:
            Optional[PhysicalBoard]: The updated `PhysicalBoard` instance after the player's move
                or the current state if it's the robot's turn.

        Raises:
            RuntimeError: If a game instance has not been set before calling this method.
            ValueError: If `current_player` in the game is neither `HUMAN` nor `ROBOT`.
        """

        if not self.game:
            raise RuntimeError("Game instance must be set before capturing the board.")

        chess_board = self.game.get_chess_board().copy()

        if self.game.current_player == Player.HUMAN:
            result = self.engine.play(
                chess_board,
                chess.engine.Limit(time=0.1, depth=4),
            )
            if not result or not result.move:
                return None

            chess_board.push(result.move)
            return PhysicalBoard(chess_board)

        elif self.game.current_player == Player.ROBOT:
            return PhysicalBoard(chess_board)

        raise ValueError("Unknown player type. Expected HUMAN or ROBOT.")
