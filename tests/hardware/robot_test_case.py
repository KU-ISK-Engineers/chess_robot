import unittest

from ultralytics import YOLO
from src.communication.tcp_robot import TCPRobotHand
from src.core.board import PhysicalBoard, are_boards_equal
from src.core.moves import move_piece, iter_reset_board
from src.detection.basler_camera import (
    CameraBoardCapture,
    Orientation,
)
import chess
from typing import Union
from abc import ABC
import logging

CAMERA_ORIENTATION = Orientation.HUMAN_BOTTOM
MODEL_PATH = "training/models/yolo8_200.pt"
MAX_PIECE_OFFSET = 0.99

logging.getLogger("ultralytics").setLevel(logging.CRITICAL)


class RobotTestCase(unittest.TestCase, ABC):
    def setUp(self) -> None:
        self.board_capture = CameraBoardCapture(
            model=YOLO(MODEL_PATH),
            physical_orientation=CAMERA_ORIENTATION,
            conf_threshold=0.5,
            iou_threshold=0.45,
            max_piece_offset=MAX_PIECE_OFFSET,
            timeout=5000,
        )

        self.robot_hand = TCPRobotHand()
        self.human_color = chess.WHITE
        self.robot_color = not self.human_color
        self.chess_board = chess.Board()
        self.pieces_reserve: dict[int, list[chess.Piece]] = {}

    def capture_board(self, human_color) -> PhysicalBoard:
        captured_board = self.board_capture.capture_board(human_color)
        if captured_board is None:
            raise RuntimeError("Failed to capture board")
        return captured_board

    def assert_rearrange_board(
        self, expected_board: chess.Board, human_color: chess.Color
    ) -> None:
        robot_color = not human_color
        done = False
        while not done:
            captured_board = self.capture_board(human_color)
            moved, done = iter_reset_board(
                self.robot_hand,
                captured_board,
                PhysicalBoard(expected_board),
                robot_color,
            )
            if not moved:
                break

        self.assertTrue(done, "Function sync board failed")

        captured_board = self.capture_board(human_color)
        self.assertTrue(
            are_boards_equal(captured_board.chess_board, expected_board),
            "Boards do not match after board rearrangement",
        )

        self.chess_board = expected_board.copy()
        self.human_color = human_color
        self.robot_color = robot_color
        self.pieces_reserve.clear()  # Pieces reserve simulated as a stack

    def assert_move_piece(
        self,
        from_square: Union[chess.Square, str],
        to_square: Union[chess.Square, str],
    ) -> None:
        if isinstance(from_square, str):
            from_square = chess.parse_square(from_square)
        if isinstance(to_square, str):
            to_square = chess.parse_square(to_square)

        captured_board = self.capture_board(self.human_color)
        self.assertTrue(
            are_boards_equal(captured_board.chess_board, self.chess_board),
            "Board arrangement in memory does not match physical board arrangement",
        )

        origin_piece = (
            self.chess_board.piece_at(from_square)
            if from_square in chess.SQUARES
            else self.pieces_reserve[from_square][-1]
        )
        if origin_piece is None:
            raise ValueError("Cannot move empty square")

        expected_chess_board = self.chess_board.copy()
        if from_square in chess.SQUARES:
            expected_chess_board.remove_piece_at(from_square)

        if to_square in chess.SQUARES:
            expected_chess_board.set_piece_at(to_square, origin_piece)

        done = move_piece(
            self.robot_hand, captured_board, from_square, to_square, self.robot_color
        )
        self.assertTrue(done, "Function move piece failed")

        captured_board = self.capture_board(self.human_color)
        self.assertTrue(
            are_boards_equal(captured_board.chess_board, expected_chess_board),
            "Boards do not match after move",
        )

        if from_square in chess.SQUARES:
            self.chess_board.remove_piece_at(from_square)
        else:
            self.pieces_reserve[from_square].pop()

        if to_square in chess.SQUARES:
            self.chess_board.set_piece_at(to_square, origin_piece)
        else:
            self.pieces_reserve.setdefault(to_square, []).append(origin_piece)
