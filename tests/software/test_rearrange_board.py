# TODO: Move these to software tests and test using a mock object

from abc import ABC
from src.core.board import PhysicalBoard
from src.mocks.piece_mover import SimulatedPieceMover
import chess
import unittest

# TODO: Mock, counting how many rearrangements it does, and assert_rearraneg_board max rearrangements


class RearrangeBoardTestCase(unittest.TestCase, ABC):
    def assert_rearrange_board(
        self, expected_board: chess.Board, human_color: chess.Color
    ) -> int:
        return 0


class TestRearrangeBoard(unittest.TestCase):
    def test_already_expected_board(self) -> None:
        pass

    def test_pieces_moved_up(self) -> None:
        pass

    def test_pieces_moved_diagonally(self) -> None:
        pass

    def test_swapped_rows(self) -> None:
        pass

    def test_swapped_rows_diagonally(self) -> None:
        pass

    def test_swap_human_colors(self) -> None:
        pass

    def test_remove_and_put_white_pieces(self) -> None:
        pass

    def test_remove_and_put_black_pieces(self) -> None:
        pass

    def test_remove_and_put_white_pieces_swapped(self) -> None:
        pass

    def test_remove_and_put_black_pieces_swapped(self) -> None:
        pass

    @unittest.skip("No pieces reserve for both color")
    def test_remove_and_put_all_pieces(self) -> None:
        pass

    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_black_extra_pieces(self) -> None:
        pass

    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_white_extra_pieces(self) -> None:
        pass

    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_all_extra_pieces(self) -> None:
        pass
