import unittest
from src.movement import identify_move
import chess
from typing import Iterable


class TestIdentifyMoveStart(unittest.TestCase):
    def setUp(self):
        self.board = chess.Board()

    def test_valid_moves_white(self):
        assert_identify_moves(self, self.board, self.board.legal_moves, as_sequence=False)

    def test_valid_moves_black(self):
        valid_moves = self.board.legal_moves
        for move in valid_moves:
            board = chess.Board(fen=self.board.fen())
            board.push(move)
            assert_identify_moves(self, board, board.legal_moves, as_sequence=False)

    def test_invalid_moves_white(self):
        moves = [
            "a1a3", "a1b1",  # Rook invalid moves
            "b1b2", "b1a2",  # Knight invalid moves
            "c1c3", "c1d2",  # Bishop invalid moves
            "d1d3", "d1e2",  # Queen invalid moves
            "e1e2", "e1f1",  # King invalid moves
            "a2a1", "b2b1",  # Pawn invalid backward moves
            "c2c5", "d2d5",  # Pawn invalid forward moves (2 steps after initial move)
            "e2e3", "f2f3",  # Pawn moves obstructed by own pieces
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


def assert_identify_move(test_case: unittest.TestCase, 
                         board: chess.Board, 
                         expected_move: chess.Move | str,
                         expected_legal: bool = True):
    if isinstance(expected_move, str):
        expected_move = chess.Move.from_uci(expected_move)

    after_board = chess.Board(fen=board.fen())
    make_move(after_board, expected_move)
    actual_move, legal = identify_move(board, after_board)

    test_case.assertEqual(expected_move, actual_move)
    test_case.assertEqual(expected_legal, legal)

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
