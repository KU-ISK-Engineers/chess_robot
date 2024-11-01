import unittest
from src.core.moves import identify_move
import chess
from typing import Iterable
from abc import ABC


class MoveTestCase(unittest.TestCase, ABC):
    def assert_move(self,
                    board: chess.Board,
                    expected_move: chess.Move | str,
                    expected_legal: bool = True):
        if isinstance(expected_move, str):
            expected_move = chess.Move.from_uci(expected_move)

        after_board = chess.Board(fen=board.fen())
        make_test_move(after_board, expected_move)

        actual_move, legal = identify_move(board, after_board)

        # Ignore promotion
        if actual_move and not expected_move.promotion:
            actual_move.promotion = None

        def fmt_legal(x):
            return 'legal' if x else 'illegal'

        expected_msg = f"EXPECTED {fmt_legal(expected_legal)} move {expected_move.uci()}"
        actual_msg = f"ACTUAL {fmt_legal(legal)} move {actual_move and actual_move.uci()}"
        msg = expected_msg + ", " + actual_msg

        self.assertEqual(expected_move, actual_move, msg)
        self.assertEqual(expected_legal, legal, msg)

        return after_board

    def assert_moves(self,
                     board: chess.Board,
                     moves: Iterable[chess.Move | str],
                     legal: bool = True):
        for move in moves:
            self.assert_move(board, move, expected_legal=legal)


def make_test_move(board: chess.Board, move: chess.Move):
    if move in board.legal_moves:
        board.push(move)
    else:
        # Directly set the piece on the target square, bypassing legality checks
        piece = board.piece_at(move.from_square)
        if piece:
            board.remove_piece_at(move.from_square)
            board.set_piece_at(move.to_square, chess.Piece(move.promotion, piece.color) if move.promotion else piece)


class TestOpeningWhite(MoveTestCase):
    def setUp(self):
        self.board = chess.Board()

    def test_valid_moves(self):
        self.assert_moves(self.board, self.board.legal_moves)

    def test_invalid_rook(self):
        moves = ['a1a3', 'a1a2', 'a1b1', 'h1h3', 'h1h2', 'h1b1', 'h1b2']
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_knight(self):
        moves = ['b1b2', 'b1a2', 'g1g2', 'g1h2']
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_bishop(self):
        moves = ['c1c3', 'c1d2', 'f1e2', 'f1f2']
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_queen(self):
        moves = ['d1d3', 'd1e2', 'd1d2']
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_king(self):
        moves = ["e1e2", "e1f1"]
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_pawn_backwards(self):
        moves = ["a2a1", "b2b1"]
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_pawn_forwards(self):
        moves = ["c2c5", "d2d5"]
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_pawn_capture(self):
        moves = [
            "a2b3", "a2c3",  # Invalid pawn captures by a2
            "b2a3", "b2c3",  # Invalid pawn captures by b2
            "c2b3", "c2d3",  # Invalid pawn captures by c2
            "d2c3", "d2e3",  # Invalid pawn captures by d2
            "e2d3", "e2f3",  # Invalid pawn captures by e2
            "f2e3", "f2g3",  # Invalid pawn captures by f2
            "g2f3", "g2h3",  # Invalid pawn captures by g2
            "h2g3", "h2f3"   # Invalid pawn captures by h2
        ]
        self.assert_moves(self.board, moves, legal=False)


class TestOpeningBlack(MoveTestCase):
    def setUp(self):
        self.board = chess.Board()
        self.board.push_san('e2e4')

    def test_valid_moves(self):
        self.assert_moves(self.board, self.board.legal_moves)
        
    def test_invalid_rook(self):
        moves = ['a8a6', 'a8a7', 'a8b8', 'h8h6', 'h8h7', 'h8b8', 'h8b7']
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_knight(self):
        moves = ['b8b7', 'b8a7', 'g8g7', 'g8h7']
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_bishop(self):
        moves = ['c8c6', 'c8d7', 'f8e7', 'f8f7']
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_queen(self):
        moves = ['d8d6', 'd8e7', 'd8d7']
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_king(self):
        moves = ["e8e7", "e8f8"]
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_pawn_backwards(self):
        moves = ["a7a8", "b7b8"]
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_pawn_forwards(self):
        moves = ["c7c4", "d7d4"]
        self.assert_moves(self.board, moves, legal=False)

    def test_invalid_pawn_capture(self):
        moves = [
            "a7b6", "a7c6",  # Invalid pawn captures by a7
            "b7a6", "b7c6",  # Invalid pawn captures by b7
            "c7b6", "c7d6",  # Invalid pawn captures by c7
            "d7c6", "d7e6",  # Invalid pawn captures by d7
            "e7d6", "e7f6",  # Invalid pawn captures by e7
            "f7e6", "f7g6",  # Invalid pawn captures by f7
            "g7f6", "g7h6",  # Invalid pawn captures by g7
            "h7g6", "h7f6"   # Invalid pawn captures by h7
        ]
        self.assert_moves(self.board, moves, legal=False)


class TestEnPassantWhite(MoveTestCase):
    def setUp(self):
        self.board = chess.Board("rnbqkbnr/pppp1ppp/8/4pP2/8/8/PPPP2PP/RNBQKBNR w KQkq e6 0 1")

    def test_valid_en_passant(self):
        self.assert_move(self.board, 'f5e6', expected_legal=True)

    def test_invalid_en_passant(self):
        self.assert_move(self.board, 'f5g6', expected_legal=False)


class TestEnPassantBlack(MoveTestCase):
    def setUp(self):
        self.board = chess.Board("rnbqkbnr/pppp2pp/8/8/4Pp2/8/PPPP1PpP/RNBQKBNR b KQkq e3 0 1")

    def test_valid_en_passant(self):
        self.assert_move(self.board, 'f4e3', expected_legal=True)

    def test_invalid_en_passant(self):
        self.assert_move(self.board, 'f4g3', expected_legal=False)


class TestCastlingWhite(MoveTestCase):
    def setUp(self):
        self.board_kingside = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")
        self.board_queenside = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1")

    def test_valid_kingside_castling(self):
        self.assert_move(self.board_kingside, 'e1g1', expected_legal=True)

    def test_invalid_kingside_castling(self):
        self.board_kingside.push(chess.Move.from_uci('h1h3'))  # Move rook first
        self.assert_move(self.board_kingside, 'e1g1', expected_legal=False)

    def test_valid_queenside_castling(self):
        self.assert_move(self.board_queenside, 'e1c1', expected_legal=True)

    def test_invalid_queenside_castling(self):
        self.board_queenside.push(chess.Move.from_uci('a1a3'))  # Move rook first
        self.assert_move(self.board_queenside, 'e1c1', expected_legal=False)


class TestCastlingBlack(MoveTestCase):
    def setUp(self):
        self.board_kingside = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")
        self.board_queenside = chess.Board("r3k2r/8/8/8/8/8/8/R3K2R b KQkq - 0 1")

    def test_valid_kingside_castling(self):
        self.assert_move(self.board_kingside, 'e8g8', expected_legal=True)

    def test_invalid_kingside_castling(self):
        self.board_kingside.push(chess.Move.from_uci('h8h6'))  # Move rook first
        self.assert_move(self.board_kingside, 'e8g8', expected_legal=False)

    def test_valid_queenside_castling(self):
        self.assert_move(self.board_queenside, 'e8c8', expected_legal=True)

    def test_invalid_queenside_castling(self):
        self.board_queenside.push(chess.Move.from_uci('a8a6'))  # Move rook first
        self.assert_move(self.board_queenside, 'e8c8', expected_legal=False)


class TestPromotionWhite(MoveTestCase):
    def setUp(self):
        self.board = chess.Board("3bk3/4P1P1/8/8/8/8/8/4K3 w - - 0 1")

    def test_valid_promotion_upwards(self):
        self.assert_move(self.board, 'g7g8q', expected_legal=True)

    def test_invalid_promotion_upwards(self):
        self.assert_move(self.board, 'g7g8k', expected_legal=False)  # Promoting to king is invalid
        self.assert_move(self.board, 'g7g8p', expected_legal=False)  # Promoting to pawn is invalid

    def test_valid_promotion_capture(self):
        self.assert_move(self.board, 'e7d8q', expected_legal=True)

    def test_invalid_promotion_capture(self):
        self.assert_move(self.board, 'e7f8q', expected_legal=False)  # Capturing on f8 is invalid
        self.assert_move(self.board, 'e7d8k', expected_legal=False)  # Invalid promotion piece (king)

    def test_pawn_moves_upwards_with_king(self):
        self.assert_move(self.board, 'e7e8k', expected_legal=False)  # Invalid promotion piece (king)
        self.assert_move(self.board, 'e7e8p', expected_legal=False)  # Invalid promotion piece (pawn)


class TestPromotionBlack(MoveTestCase):
    def setUp(self):
        self.board = chess.Board("4k3/8/8/8/8/8/4p1p1/3BK3 b - - 0 1")

    def test_valid_promotion_upwards(self):
        self.assert_move(self.board, 'g2g1q', expected_legal=True)

    def test_invalid_promotion_upwards(self):
        self.assert_move(self.board, 'g2g1k', expected_legal=False)  # Promoting to king is invalid
        self.assert_move(self.board, 'g2g1p', expected_legal=False)  # Promoting to pawn is invalid

    def test_valid_promotion_capture(self):
        self.assert_move(self.board, 'e2d1q', expected_legal=True)

    def test_invalid_promotion_capture(self):
        self.assert_move(self.board, 'e2f1q', expected_legal=False)  # Capturing on f1 is invalid
        self.assert_move(self.board, 'e2d1k', expected_legal=False)  # Invalid promotion piece (king)

    def test_pawn_moves_upwards_with_king(self):
        self.assert_move(self.board, 'e2e1k', expected_legal=False)  # Invalid promotion piece (king)
        self.assert_move(self.board, 'e2e1p', expected_legal=False)  # Invalid promotion piece (pawn)


if __name__ == '__main__':
    unittest.main()
