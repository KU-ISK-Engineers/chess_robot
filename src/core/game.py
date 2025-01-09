from typing import Optional, Tuple
import logging

import chess
import chess.engine

from src.core.board import PhysicalBoard, BoardCapture, are_boards_equal
from src.core.moves import PieceMover, execute_move, identify_move, iter_reset_board

logger = logging.getLogger(__name__)

HUMAN = 0
ROBOT = 1


class Game:
    """Represents a game of chess played on a physical board with robot and human players.

    Attributes:
        board_capture (BoardCapture): Responsible for capturing the current board state.
        piece_mover (PieceMover): Responsible for physically moving pieces on the board.
        depth (int): The depth of search for the engine's move calculations.
        engine (chess.engine.SimpleEngine): The chess engine used to calculate moves.
        physical_board (PhysicalBoard): Current physical state of the chess board.
        current_player (int): Indicates the current player (HUMAN or ROBOT).
        human_color (chess.Color): The color that the human player controls (chess.WHITE or chess.BLACK).
        robot_color (chess.Color): The color assigned to the robot player, opposite of `player_color`.
        resigned (bool): Flag indicating if the human player has resigned.
    """

    def __init__(
        self,
        board_capture: BoardCapture,
        piece_mover: PieceMover,
        engine: chess.engine.SimpleEngine,
        chess_board: Optional[chess.Board] = None,
        human_color: chess.Color = chess.WHITE,
        depth: int = 4,
        skill_level: int = 0
    ) -> None:
        """Initializes the Game with board capture, movement, engine, player color, and depth.

        Args:
            board_capture (BoardCapture): The system to capture the board's state.
            piece_mover (PieceMover): The system that physically moves pieces.
            engine (chess.engine.SimpleEngine): The chess engine used for move calculations.
            chess_board (Optional[chess.Board]): The current logical board state. Defaults to a new game.
            human_color (chess.Color): The color the human player controls (chess.WHITE or chess.BLACK).
            depth (int): The search depth for the engine's move calculations. Defaults to 4.
        """
        if not chess_board:
            chess_board = chess.Board()

        if chess_board.turn == human_color:
            self.current_player = HUMAN
        else:
            self.current_player = ROBOT

        self.robot_color = not human_color
        self.board_capture = board_capture
        self.piece_mover = piece_mover
        self.engine = engine
        self.depth = depth
        self.skill_level = skill_level
        self.human_color = human_color
        self.physical_board = PhysicalBoard(chess_board)
        self.resigned = False
        self.piece_mover.reset()

        self.set_skill_level(self.skill_level)

    def reset_state(
        self,
        chess_board: Optional[chess.Board] = None,
        human_color: Optional[chess.Color] = None,
    ) -> None:
        """Resets the game to a specified or new board position.

        Reinitializes the game state to a given board configuration or a default start position,
        and sets the human player's color if provided. Note that this method does
        not physically move pieces on the board.

        Args:
            chess_board (Optional[PhysicalBoard]): The physical board state to reset to.
                If None, defaults to a new game state with an initial position.
            human_color (Optional[chess.Color]): The color that the human player controls
                (chess.WHITE or chess.BLACK). Defaults to the previously set `player_color`.
        """
        if not chess_board:
            chess_board = chess.Board()

        if not human_color:
            human_color = self.human_color

        if chess_board.turn == human_color:
            self.current_player = HUMAN
        else:
            self.current_player = ROBOT

        fen = chess_board.fen()
        logger.info(
            f"Resetting board to {'white' if human_color == chess.WHITE else 'black'} perspective with FEN {fen}"
        )

        self.robot_color = not human_color
        self.human_color = human_color
        self.physical_board = PhysicalBoard(chess_board)
        self.resigned = False
        self.piece_mover.reset()

    def sync_board(self) -> bool:
        """Synchronizes the physical board with the logical board state.

        Adjusts the positions of physical pieces to match the expected logical state
        in memory.

        Returns:
            bool: True if the physical board successfully matches the logical board
            in memory; False if synchronization fails.
        """
        logger.info("Synchronizing physical board")

        expected_board = self.physical_board.chess_board
        current_board = None

        done = False
        while not done:
            current_board = self.board_capture.capture_board(self.human_color)
            if not current_board:
                continue  # Keeps trying until a valid board capture

            moved, done = iter_reset_board(
                self.piece_mover, self.physical_board, expected_board, self.robot_color
            )
            if not moved:
                break

        if done and current_board:
            self.physical_board.piece_offsets = current_board.piece_offsets

        return done
    
    def set_skill_level(self, skill_level: int = 0) -> None:
        self.skill_level = skill_level
        self.engine.configure({"Skill Level": skill_level})  


    def set_depth(self, depth: int = 4) -> None:
        """Sets the depth for engine's move calculations and configures engine's skill level.

        Args:
            depth (int): The depth level for the chess engine calculations. Defaults to 4.
        """
        self.depth = depth
        

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
        new_board = self.board_capture.capture_board(self.human_color)
        if not new_board:
            return None

        if not are_boards_equal(self.physical_board.chess_board, new_board.chess_board):
            logger.info(
                "Detected board does not match previous legal board for robot to move; waiting for realignment"
            )
            return None

        if move is None:
            result = self.engine.play(
                self.physical_board.chess_board, chess.engine.Limit(depth=self.depth)
            )
            move = result.move

        logger.info("Robot making move %s", move and move.uci())

        if not move or move not in self.physical_board.chess_board.legal_moves:
            logger.error("Invalid robot move: %s", move and move.uci())
            return None

        self.physical_board.piece_offsets = new_board.piece_offsets
        if not execute_move(
            self.piece_mover, self.physical_board, move, self.robot_color
        ):
            return None

        self.current_player = HUMAN
        self.physical_board.chess_board.push(move)
        return move

    def human_made_move(self) -> Tuple[Optional[chess.Move], bool]:
        """Detects and validates the move made by the human player.

        Returns:
            Tuple[Optional[chess.Move], bool]: The detected move and a boolean indicating if it was legal.
        """
        new_board = self.board_capture.capture_board(self.human_color)
        if not new_board:
            return None, False

        move, legal = identify_move(
            self.physical_board.chess_board, new_board.chess_board
        )
        if move:
            logger.info(
                f"Human made {'legal' if legal else 'illegal'} move {move.uci()}"
            )
            if legal:
                self.physical_board.chess_board.push(move)
                self.physical_board.piece_offsets = new_board.piece_offsets
                self.current_player = ROBOT

        return move, legal

    def result(self) -> str:
        """Determines the current game result from the human player's perspective.

        Returns:
            str: The result of the game ("1-0", "0-1", "1/2-1/2", or "resigned").

        Note:
            If the human player is Black, the result is flipped to reflect the
            player's perspective.
        """
        if self.resigned:
            return "resigned"

        result = self.physical_board.chess_board.result()

        if self.human_color == chess.BLACK:
            # Flip result for black's perspective
            if result == "1-0":
                result = "0-1"
            elif result == "0-1":
                result = "1-0"

        return result

    def resign_human(self):
        """Marks the human player as resigned, ending the game for them.

        This sets the `resigned` flag to True, indicating the human player has resigned.
        It does not affect the robot player.
        """
        self.resigned = True

    def get_chess_board(self) -> chess.Board:
        """Returns the current logical chess board state.

        Returns:
            chess.Board: The current logical state of the chess board.
        """
        return self.physical_board.chess_board
