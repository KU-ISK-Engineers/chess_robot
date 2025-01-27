from src.core.board import PhysicalBoard
from src.core.moves import off_board_square
from tests.hardware.robot_test_case import RobotTestCase
import chess
import unittest


class TestMovePiece(RobotTestCase):
    def test_move_piece_up(self):
        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        self.assert_move_piece(from_square="e2", to_square="e4")
        self.assert_move_piece(from_square="e7", to_square="e5")

        # self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        # self.assert_move_piece(from_square="e2", to_square="e4", expected_piece="P")
        # self.assert_move_piece(from_square="e7", to_square="e5", expected_piece="p")
    
    def test_move_pieces_up(self):
        moves = [("d2", "d4"), ("b2", "b4"), ("c2", "c4")]
        
        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        for from_square, to_square in moves:
            self.assert_move_piece(from_square=from_square, to_square=to_square)

        self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        for from_square, to_square in moves:
            self.assert_move_piece(from_square=from_square, to_square=to_square)

    def test_move_piece_diagonal(self):
        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        self.assert_move_piece(from_square="a2", to_square="h4")
        self.assert_move_piece(from_square="h7", to_square="a5")

        self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        self.assert_move_piece(from_square="a2", to_square="h4")
        self.assert_move_piece(from_square="h7", to_square="a5")

    def test_move_pieces_diagonal(self):
        moves = [("b2", "g4"), ("c2", "f4"), ("d2", "e4")]

        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        for from_square, to_square in moves:
            self.assert_move_piece(from_square=from_square, to_square=to_square)

        self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        for from_square, to_square in moves:
            self.assert_move_piece(from_square=from_square, to_square=to_square)

    def test_remove_piece(self):
        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        self.assert_move_piece(from_square="e2", to_square=off_board_square(chess.PAWN, chess.WHITE))

        self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        self.assert_move_piece(from_square="e2", to_square=off_board_square(chess.PAWN, chess.WHITE))

    def test_remove_white(self):
        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        for square in chess.SQUARES:
            piece = self.board.chess_board.piece_at(square)
            if piece and piece.color == chess.WHITE:
                self.assert_move_piece(
                    from_square=square,
                    to_square=off_board_square(piece.piece_type, chess.WHITE),
                )

        self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        for square in chess.SQUARES:
            piece = self.board.chess_board.piece_at(square)
            if piece and piece.color == chess.WHITE:
                self.assert_move_piece(
                    from_square=square,
                    to_square=off_board_square(piece.piece_type, chess.WHITE),
                )

    def test_remove_black(self):
        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        for square in chess.SQUARES:
            piece = self.board.chess_board.piece_at(square)
            if piece and piece.color == chess.BLACK:
                self.assert_move_piece(
                    from_square=square,
                    to_square=off_board_square(piece.piece_type, chess.BLACK),
                )

        self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        for square in chess.SQUARES:
            piece = self.board.chess_board.piece_at(square)
            if piece and piece.color == chess.BLACK:
                self.assert_move_piece(
                    from_square=square,
                    to_square=off_board_square(piece.piece_type, chess.BLACK),
                )

    @unittest.skip("No pieces reserve for both colors")
    def test_remove_all(self):
        pass
    
    @unittest.skip("No pieces reserve for both colors")
    def test_remove_all_and_put(self):
        pass

    def test_remove_and_put(self):
        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        self.assert_move_piece(from_square="e2", to_square=off_board_square(chess.PAWN, chess.WHITE))
        self.assert_move_piece(from_square=off_board_square(chess.PAWN, chess.WHITE), to_square="e2")

        self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        self.assert_move_piece(from_square="e2", to_square=off_board_square(chess.PAWN, chess.WHITE))
        self.assert_move_piece(from_square=off_board_square(chess.PAWN, chess.WHITE), to_square="e2")

    def test_repeated_moves(self):
        self.set_board(PhysicalBoard(), human_color=chess.WHITE)
        for _ in range(10):
            self.assert_move_piece(from_square="e2", to_square="h4")
            self.assert_move_piece(from_square="h4", to_square="e2")

        self.set_board(PhysicalBoard(), human_color=chess.BLACK)
        for _ in range(10):
            self.assert_move_piece(from_square="e2", to_square="h4")
            self.assert_move_piece(from_square="h4", to_square="e2")
