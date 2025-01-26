from src.core.board import PhysicalBoard
from tests.hardware.robot_test_case import RobotTestCase
import chess
import unittest


class TestResetBoard(RobotTestCase):
    def test_reset_initial(self):
        expected_board = PhysicalBoard()
        self.assert_set_board(expected_board, chess.WHITE)
        self.assert_set_board(expected_board, chess.BLACK)
        
    def test_reset_correct(self):
        expected_board = PhysicalBoard()
        self.assert_set_board(expected_board, chess.WHITE)
        self.assert_set_board(expected_board, chess.WHITE)
        self.assert_set_board(expected_board, chess.BLACK)
        self.assert_set_board(expected_board, chess.BLACK)
        
    def test_reset_no_white_pieces(self):
        current_fen = "rnbqkbnr/pppppppp/8/8/8/8/8/8 b KQkq - 0 1"
        board = chess.Board(current_fen)

        self.assert_set_board(PhysicalBoard(board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(board), human_color=chess.BLACK)

    def test_reset_no_black_pieces(self):
        current_fen = "8/8/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        board = chess.Board(current_fen)

        self.assert_set_board(PhysicalBoard(board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(board), human_color=chess.BLACK)
        
    def test_unnecessary_pawn(self):
        current_board = chess.Board()
        current_board.set_piece_at(chess.parse_square("e3"), chess.Piece(chess.PAWN, chess.WHITE))

        expected_board = chess.Board()

        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.BLACK)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.BLACK)
        
    def test_kings_with_queens_swapped(self):
        current_fen = "rnbkqbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBKQBNR w KQkq - 0 1"
        current_board = chess.Board(current_fen)

        expected_board = chess.Board()

        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.BLACK)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.BLACK)


    def test_bishops_with_knights_swapped(self):
        current_fen = "rbnqknbr/pppppppp/8/8/8/8/PPPPPPPP/RBNQKNBR w KQkq - 0 1"
        current_board = chess.Board(current_fen)

        expected_board = chess.Board()

        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.BLACK)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.BLACK)
        
    def test_move_board_center(self):
        current_fen = "8/8/pppppppp/rnbqkbnr/PPPPPPPP/RNBQKBNR/8/8 w KQkq - 0 1"
        current_board = chess.Board(current_fen)

        expected_board = chess.Board()

        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.BLACK)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.BLACK)
    
    def test_cyclic_dependencies(self):
        # Create a cycle: knight on b1 must go to c3, bishop on c3 must go to e4, and pawn on e4 must go to b1
        starting_board = chess.Board()
        starting_board.clear()
        starting_board.set_piece_at(chess.parse_square("b1"), chess.Piece(chess.KNIGHT, chess.WHITE))
        starting_board.set_piece_at(chess.parse_square("c3"), chess.Piece(chess.BISHOP, chess.WHITE))
        starting_board.set_piece_at(chess.parse_square("e4"), chess.Piece(chess.PAWN, chess.WHITE))

        ending_board = chess.Board()
        ending_board.clear()
        ending_board.set_piece_at(chess.parse_square("c3"), chess.Piece(chess.KNIGHT, chess.WHITE))
        ending_board.set_piece_at(chess.parse_square("e4"), chess.Piece(chess.BISHOP, chess.WHITE))
        ending_board.set_piece_at(chess.parse_square("b1"), chess.Piece(chess.PAWN, chess.WHITE))

        self.assert_set_board(PhysicalBoard(starting_board), chess.WHITE)
        self.assert_set_board(PhysicalBoard(ending_board), chess.WHITE)
        self.assert_set_board(PhysicalBoard(starting_board), chess.BLACK)
        self.assert_set_board(PhysicalBoard(ending_board), chess.BLACK)
    
    @unittest.skip("Reserve for both colors not implemented yet")
    def test_reset_empty(self):
        board = chess.Board()
        board.clear()
        self.assert_set_board(PhysicalBoard(board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(board), human_color=chess.BLACK)

    @unittest.skip("Reserve for both colors not implemented yet")
    def test_remove_and_put_corner_pieces(self):
        current_fen = "1nbqkbn1/pppppppp/8/8/8/8/PPPPPPPP/1NBQKBN1 w KQkq - 0 1"
        current_board = chess.Board(current_fen)

        expected_board = chess.Board()

        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.WHITE)
        self.assert_set_board(PhysicalBoard(current_board), human_color=chess.BLACK)
        self.assert_set_board(PhysicalBoard(expected_board), human_color=chess.BLACK)
        
    @unittest.skip("Reserve for both colors not implemented yet")
    def test_reset_empty_to_full(self):
        empty_board = PhysicalBoard(chess.Board())
        empty_board.chess_board.clear()
        
        full_board = PhysicalBoard(chess.Board())

        self.assert_set_board(empty_board, human_color=chess.WHITE)
        self.assert_set_board(full_board, human_color=chess.WHITE)
        self.assert_set_board(empty_board, human_color=chess.BLACK)
        self.assert_set_board(full_board, human_color=chess.BLACK)
        
    def test_repeated_resets(self):
        expected_board = PhysicalBoard()
        for _ in range(10):  
            self.assert_set_board(expected_board, chess.WHITE)
            self.assert_set_board(expected_board, chess.BLACK)
            