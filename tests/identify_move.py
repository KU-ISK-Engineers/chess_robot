import unittest
from src.movement import identify_move
import chess
from typing import Iterable


class TestOpeningWhite(unittest.TestCase):
    def setUp(self):
        self.board = chess.Board()

    def test_valid_moves(self):
        assert_identify_moves(self, self.board, self.board.legal_moves)

    def test_invalid_rook(self):
        moves = ['a1a3', 'a1a2', 'a1b1', 'h1h3', 'h1h2', 'h1b1', 'h1b2']
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_knight(self):
        moves = ['b1b2', 'b1a2', 'g1g2', 'g1h2']
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_bishop(self):
        moves = ['c1c3', 'c1d2', 'f1e2', 'f1f2']
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_queen(self):
        moves = ['d1d3', 'd1e2', 'd1d2']
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_king(self):
        moves = ["e1e2", "e1f1"]
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_pawn_backwards(self):
        moves = ["a2a1", "b2b1"]
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_pawn_forwards(self):
        moves = ["c2c5", "d2d5"]
        assert_identify_moves(self, self.board, moves, legal=False)

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
        assert_identify_moves(self, self.board, moves, legal=False)


class TestOpeningBlack(unittest.TestCase):
    def setUp(self):
        self.board = chess.Board()
        self.board.push_san('e2e4')

    def test_valid_moves(self):
        assert_identify_moves(self, self.board, self.board.legal_moves)
        
    def test_invalid_rook(self):
        moves = ['a8a6', 'a8a7', 'a8b8', 'h8h6', 'h8h7', 'h8b8', 'h8b7']
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_knight(self):
        moves = ['b8b7', 'b8a7', 'g8g7', 'g8h7']
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_bishop(self):
        moves = ['c8c6', 'c8d7', 'f8e7', 'f8f7']
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_queen(self):
        moves = ['d8d6', 'd8e7', 'd8d7']
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_king(self):
        moves = ["e8e7", "e8f8"]
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_pawn_backwards(self):
        moves = ["a7a8", "b7b8"]
        assert_identify_moves(self, self.board, moves, legal=False)

    def test_invalid_pawn_forwards(self):
        moves = ["c7c4", "d7d4"]
        assert_identify_moves(self, self.board, moves, legal=False)

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
        assert_identify_moves(self, self.board, moves, legal=False)


def assert_identify_move(test_case: unittest.TestCase,
                         board: chess.Board, 
                         expected_move: chess.Move | str,
                         expected_legal: bool = True):
    if isinstance(expected_move, str):
        expected_move = chess.Move.from_uci(expected_move)

    after_board = chess.Board(fen=board.fen())
    make_move(after_board, expected_move)
    actual_move, legal = identify_move(board, after_board)

    # Ignore promotion
    if not expected_move.promotion:
        actual_move.promotion = None

    def fmt_legal(x):
        return 'legal' if x else 'illegal'

    msg = f"EXPECTED {fmt_legal(expected_legal)} move {expected_move.uci()}, ACTUAL {fmt_legal(legal)} move {actual_move.uci()}"
    test_case.assertEqual(expected_move, actual_move, msg)
    test_case.assertEqual(expected_legal, legal, msg)

    return after_board


def assert_identify_moves(test_case: unittest.TestCase, 
                          board: chess.Board, 
                          moves: Iterable[chess.Move | str],
                          as_sequence: bool = False, 
                          legal: bool = True):
    for move in moves:
        after_board = assert_identify_move(test_case, board, move, expected_legal=legal)
        if as_sequence:
            board = after_board

    return board


def make_move(board: chess.Board, move: chess.Move):
    # Directly set the piece on the target square, bypassing legality checks
    piece = board.piece_at(move.from_square)
    if piece:
        board.remove_piece_at(move.from_square)
        board.set_piece_at(move.to_square, piece)
    else:
        raise ValueError(f"No piece at the starting square {move.from_square}")


if __name__ == '__main__':
    unittest.main()
