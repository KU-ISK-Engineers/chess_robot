import chess

from src.core.board import PieceOffset
from src.core.moves import PieceMover


class SimulatedPieceMover(PieceMover):
    """Simulated implementation of the `PieceMover` class for testing purposes.

    This mock class simulates the movement of chess pieces on a physical board interface.
    Since this is a simulated environment, the methods return success responses without
    performing any physical actions, allowing for testing of logical flow in systems that
    interact with the `PieceMover` hardware.
    """

    def move_piece(
        self,
        from_square: chess.Square,
        to_square: chess.Square,
        color: chess.Color,
        origin_offset: PieceOffset,
    ) -> bool:
        """Simulates moving a piece from one square to another on a physical board.

        This method does not perform any actual movement but returns `True` to simulate
        a successful move operation. Useful for testing code that depends on the `PieceMover`
        interface.

        Args:
            from_square (chess.Square): The starting square of the piece to be "moved."
            to_square (chess.Square): The destination square for the piece.
            color (chess.Color): The color of the mover (e.g., chess.WHITE or chess.BLACK).
            origin_offset (PieceOffset): The offset of the piece's original location on the `from_square`,
                relative to the square's center.

        Returns:
            bool: Always returns `True` to indicate a successful simulated move.
        """
        return True

    def reset(self) -> bool:
        """Simulates resetting the `PieceMover` state.

        Since this is a simulated class, the method simply returns `True` without
        performing any state reset, representing a successful reset operation. This
        is useful for testing components that depend on `PieceMover` state resets.

        Returns:
            bool: Always returns `True` to indicate a successful simulated reset.
        """
        return True
