import unittest

from ultralytics import YOLO
from src.communication.tcp_robot import TCPRobotHand
from src.core.board import PhysicalBoard, are_boards_equal
from src.core.moves import execute_move, move_piece, iter_reset_board
from src.detection.basler_camera import CameraBoardCapture, Orientation, default_camera_setup
import chess
from typing import Union
from abc import ABC

CAMERA_ORIENTATION = Orientation.HUMAN_BOTTOM
MODEL_PATH = "training/models/yolo8_200.pt"
MAX_PIECE_OFFSET = 0.99

class RobotTestCase(unittest.TestCase, ABC):
    def setUp(self) -> None:
        camera = default_camera_setup()
        if camera is None:
            raise RuntimeError("Failed to start camera")
        
        self.board_capture = CameraBoardCapture(
            model=YOLO(MODEL_PATH),
            camera=camera,
            physical_orientation=CAMERA_ORIENTATION,
            conf_threshold=0.5,
            iou_threshold=0.45,
            max_piece_offset=MAX_PIECE_OFFSET,
            timeout=5000
        )
        
        self.robot_hand = TCPRobotHand()
        self.human_color = chess.WHITE
        self.robot_color = not self.human_color
        self.board = PhysicalBoard()
        
    def capture_board(self) -> PhysicalBoard:
        captured_board = self.board_capture.capture_board(self.human_color)
        if captured_board is None:
            raise RuntimeError("Failed to capture board")
        return captured_board

    def set_board(self, expected_board: PhysicalBoard, human_color: chess.Color) -> bool:
        self.human_color = human_color
        self.robot_color = not human_color
        
        captured_board = None
        done = False
        while not done:
            captured_board = self.capture_board()
            moved, done = iter_reset_board(self.robot_hand, captured_board, expected_board, self.robot_color)
            if not moved:
                break
            
        if done and captured_board is not None:
            self.board = captured_board

        return done
    
    def assert_set_board(self, expected_board: PhysicalBoard, human_color: chess.Color) -> None:
        done = self.set_board(expected_board, human_color)
        self.assertTrue(done, "Function sync board failed")

        captured_board = self.capture_board()
        self.assertTrue(are_boards_equal(captured_board.chess_board, expected_board.chess_board), "Boards do not match after board rearrangement")
    
    def assert_move_piece(
        self,
        from_square: Union[chess.Square, str],
        to_square: Union[chess.Square, str],
    ) -> None:
        if isinstance(from_square, str):
            from_square = chess.parse_square(from_square)
        if isinstance(to_square, str):
            to_square = chess.parse_square(to_square)
            
        starting_board = self.capture_board()
        self.assertTrue(are_boards_equal(starting_board.chess_board, self.board.chess_board), "Board arrangement in memory does not match physical board arrangement")

        origin_piece = starting_board.chess_board.piece_at(from_square)
        target_piece = starting_board.chess_board.piece_at(to_square)
        if target_piece is not None:
            raise ValueError("Piece already exists in target square")
        
        expected_chess_board = starting_board.chess_board.copy()
        expected_chess_board.remove_piece_at(from_square)
        expected_chess_board.set_piece_at(to_square, origin_piece)
        
        done = move_piece(self.robot_hand, starting_board, from_square, to_square, self.robot_color)
        self.assertTrue(done, "Function move piece failed")

        captured_board = self.capture_board()
        self.assertTrue(are_boards_equal(captured_board.chess_board, expected_chess_board), "Boards do not match after move")

        self.board.chess_board.remove_piece_at(from_square)
        self.board.chess_board.set_piece_at(to_square, origin_piece)
    
    def assert_execute_move(
        self,
        move: Union[chess.Move, str],
    ) -> None:
        if isinstance(move, str):
            move = chess.Move.from_uci(move)
            
        starting_board = self.capture_board()
        self.assertTrue(are_boards_equal(starting_board.chess_board, self.board.chess_board), "Board arrangement in memory does not match physical board arrangement")
            
        expected_board = self.board.chess_board.copy()
        expected_board.push(move)
            
        self.board.piece_offsets = starting_board.piece_offsets
        done = execute_move(self.robot_hand, self.board, move, self.robot_color)
        self.assertTrue(done, "Function execute move failed")
        
        captured_board = self.capture_board()
        self.assertTrue(are_boards_equal(captured_board.chess_board, expected_board), "Boards do not match after move")
        
        self.board.chess_board.push(move)
        