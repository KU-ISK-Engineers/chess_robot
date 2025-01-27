from src.core.moves import off_board_square
from tests.hardware.robot_test_case import RobotTestCase
import chess
import unittest


class TestMovePieceHumanAsWhite(RobotTestCase):
    def test_move_pieces_up(self) -> None:
        self.assert_rearrange_board(chess.Board(), human_color=chess.WHITE)
        for row in range(2):
            for col in range(8):
                from_square = chess.square(col, row)
                to_square = chess.square(col, row + 2)
                self.assert_move_piece(from_square, to_square)

        for row in range(7, 5, -1):
            for col in range(8):
                from_square = chess.square(col, row)
                to_square = chess.square(col, row - 2)
                self.assert_move_piece(from_square, to_square)

    def test_move_pieces_diagonal(self) -> None:
        self.assert_rearrange_board(chess.Board(), human_color=chess.WHITE)
        for row in range(2):
            for col in range(8):
                from_square = chess.square(col, row)
                to_square = chess.square(7 - col, row + 2)
                self.assert_move_piece(from_square, to_square)

        for row in range(7, 5, -1):
            for col in range(8):
                from_square = chess.square(col, row)
                to_square = chess.square(7 - col, row - 2)
                self.assert_move_piece(from_square, to_square)

    def test_remove_white_pieces(self) -> None:
        board = chess.Board()
        self.assert_rearrange_board(board, human_color=chess.WHITE)
        for row in range(2):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )
                    
    def test_remove_black_pieces(self) -> None:
        board = chess.Board()
        self.assert_rearrange_board(board, human_color=chess.WHITE)
        for row in range(7, 5, -1):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )

    @unittest.skip("No pieces reserve for both colors")
    def test_remove_all_pieces(self) -> None:
        pass

    def test_remove_and_put_white_pieces(self) -> None:
        board = chess.Board()
        self.assert_rearrange_board(board, human_color=chess.WHITE)

        # remove and put back per piece
        for row in range(2):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )
                    self.assert_move_piece(
                        off_board_square(piece.piece_type, piece.color), square
                    )

        # remove all pieces and put them back
        for row in range(2):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )

        for row in range(2):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        off_board_square(piece.piece_type, piece.color), square
                    )
                    
    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_white_extra_pieces(self) -> None:
        pass

    def test_remove_and_put_black_pieces(self) -> None:
        board = chess.Board()
        self.assert_rearrange_board(board, human_color=chess.WHITE)

        # remove and put back per piece
        for row in range(7, 5, -1):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )
                    self.assert_move_piece(
                        off_board_square(piece.piece_type, piece.color), square
                    )

        # remove all pieces and put them back
        for row in range(7, 5, -1):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )

        for row in range(7, 5, -1):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        off_board_square(piece.piece_type, piece.color), square
                    )

    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_black_extra_pieces(self) -> None:
        pass

    @unittest.skip("No pieces reserve for both colors")
    def test_remove_and_put_all_pieces(self) -> None:
        pass

    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_all_extra_pieces(self) -> None:
        pass


class TestMovePieceHumanAsBlack(RobotTestCase):
    def test_move_pieces_up(self) -> None:
        self.assert_rearrange_board(chess.Board(), human_color=chess.BLACK)
        for row in range(2):
            for col in range(8):
                from_square = chess.square(col, row)
                to_square = chess.square(col, row + 2)
                self.assert_move_piece(from_square, to_square)

        for row in range(7, 5, -1):
            for col in range(8):
                from_square = chess.square(col, row)
                to_square = chess.square(col, row - 2)
                self.assert_move_piece(from_square, to_square)

    def test_move_pieces_diagonal(self) -> None:
        self.assert_rearrange_board(chess.Board(), human_color=chess.BLACK)
        for row in range(2):
            for col in range(8):
                from_square = chess.square(col, row)
                to_square = chess.square(7 - col, row + 2)
                self.assert_move_piece(from_square, to_square)

        for row in range(7, 5, -1):
            for col in range(8):
                from_square = chess.square(col, row)
                to_square = chess.square(7 - col, row - 2)
                self.assert_move_piece(from_square, to_square)

    def test_remove_white_pieces(self) -> None:
        board = chess.Board()
        self.assert_rearrange_board(board, human_color=chess.BLACK)
        for row in range(2):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )

    def test_remove_black_pieces(self) -> None:
        board = chess.Board()
        self.assert_rearrange_board(board, human_color=chess.BLACK)
        for row in range(7, 5, -1):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )

    @unittest.skip("No pieces reserve for both colors")
    def test_remove_all_pieces(self) -> None:
        pass

    def test_remove_and_put_white_pieces(self) -> None:
        board = chess.Board()
        self.assert_rearrange_board(board, human_color=chess.BLACK)

        # remove and put back per piece
        for row in range(2):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )
                    self.assert_move_piece(
                        off_board_square(piece.piece_type, piece.color), square
                    )

        # remove all pieces and put them back
        for row in range(2):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )

        for row in range(2):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        off_board_square(piece.piece_type, piece.color), square
                    )

    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_white_extra_pieces(self) -> None:
        pass

    def test_remove_and_put_black_pieces(self) -> None:
        board = chess.Board()
        self.assert_rearrange_board(board, human_color=chess.BLACK)

        # remove and put back per piece
        for row in range(7, 5, -1):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )
                    self.assert_move_piece(
                        off_board_square(piece.piece_type, piece.color), square
                    )

        # remove all pieces and put them back
        for row in range(7, 5, -1):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        square, off_board_square(piece.piece_type, piece.color)
                    )

        for row in range(7, 5, -1):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)
                if piece:
                    self.assert_move_piece(
                        off_board_square(piece.piece_type, piece.color), square
                    )

    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_black_extra_pieces(self) -> None:
        pass

    @unittest.skip("No pieces reserve for both colors")
    def test_remove_and_put_all_pieces(self) -> None:
        pass

    @unittest.skip("No pieces reserve for extra pieces")
    def test_remove_and_put_all_extra_pieces(self) -> None:
        pass
