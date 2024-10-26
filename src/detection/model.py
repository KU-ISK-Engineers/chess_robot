from typing import NamedTuple, Optional
import cv2
from ultralytics import YOLO
import chess
import chess.svg
import numpy as np

from src.core.board import PhysicalBoard, PieceOffset

# Minimum piece detection confidence threshold
THRESHOLD_CONFIDENCE = 0.5

# Minimum distance percentage of the piece from the square center
THRESHOLD_DISTANCE = 0.7


class MappedSquare(NamedTuple):
    """Represents a mapped square with a detected piece on a chessboard.

    Attributes:
        chess_square (chess.Square): The identified square on the board.
        offset (PieceOffset): The positional offset of the piece relative to the square center.
        label (str): The detected label of the piece (e.g., 'white-pawn').
        confidence (float): Confidence score of the piece detection.
    """
    chess_square: chess.Square
    offset: PieceOffset
    label: str
    confidence: float


def detect_greyscale(image: np.ndarray, model: YOLO) -> tuple[list, list[str], list[float]]:
    """Detects pieces on a grayscale image using the YOLO model.

    Args:
        image (np.ndarray): The grayscale image in which to detect chess pieces.
        model (YOLO): The YOLO model used for detecting objects.

    Returns:
        tuple: Contains lists of bounding boxes, labels, and confidence scores.
            - list: Bounding boxes of detected objects in [x, y, width, height] format.
            - list[str]: Labels of detected objects (e.g., 'black-knight').
            - list[float]: Confidence scores for each detected object.
    """
    # Convert grayscale to 3-channel image
    image = cv2.merge([image, image, image])

    results = model(image)
    bbox = []
    label = []
    conf = []

    labels = model.names
    
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)

        for box, cf, class_id in zip(boxes, confs, class_ids):
            if cf >= THRESHOLD_CONFIDENCE:
                x1, y1, x2, y2 = map(int, box)
                bbox.append([x1, y1, x2 - x1, y2 - y1])
                label.append(labels[class_id])
                conf.append(cf)
    return bbox, label, conf


def map_bboxes_to_squares(image: np.ndarray, bbox: list, label: list[str], confidence: list[float]) -> list[MappedSquare]:
    """Maps bounding boxes to chessboard squares based on detected piece positions.

    Args:
        image (np.ndarray): The grayscale image of the chessboard.
        bbox (list): List of bounding boxes in [x, y, width, height] format.
        label (list[str]): List of detected piece labels.
        confidence (list[float]): List of confidence scores for each piece detection.

    Returns:
        list[MappedSquare]: List of MappedSquare instances for each detected piece within acceptable distance from square centers.
    """
    img_height, img_width = image.shape[:2]
    square_width = img_width // 8
    square_height = img_height // 8
    mapped_squares = []

    max_center_dx = square_width // 2
    max_center_dy = square_height // 2

    for box, lbl, cf in zip(bbox, label, confidence):
        # Calculate center of detected bounding box
        x1, y1, x2, y2 = box[0], box[1], box[0] + box[2], box[1] + box[3]
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        col = int(center_x // square_width)
        row = int(center_y // square_height)

        square = chess.square(col, row)

        center_col = col * square_width + square_width // 2
        center_row = row * square_height + square_height // 2

        dx_offset = (center_x - center_col) / max_center_dx
        dy_offset = (center_y - center_row) / max_center_dy

        offset = PieceOffset(dx_offset, dy_offset)

        # Only include pieces within the acceptable distance from square center
        if abs(dx_offset) <= THRESHOLD_DISTANCE and abs(dy_offset) <= THRESHOLD_DISTANCE:
            mapped_squares.append(MappedSquare(square, offset, lbl, cf))

    return mapped_squares


def map_squares_to_board(mapped_squares: list[MappedSquare], flip: bool = False) -> PhysicalBoard:
    """Maps detected pieces to a PhysicalBoard instance.

    Args:
        mapped_squares (list[MappedSquare]): List of MappedSquare objects representing pieces.
        flip (bool): Whether to flip the board for perspective (True if black perspective). Defaults to False.

    Returns:
        PhysicalBoard: A PhysicalBoard instance with pieces set on detected squares.
    """
    board = PhysicalBoard()
    board.chess_board.clear_board()
    
    for mapped_square in mapped_squares:
        if flip:
            chess_square = 63 - mapped_square.chess_square
            offset = PieceOffset(-mapped_square.offset.x, -mapped_square.offset.y)
        else:
            chess_square = mapped_square.chess_square
            offset = mapped_square.offset

        piece = label_to_piece(mapped_square.label)
        
        # Place the piece on the board
        board.chess_board.set_piece_at(chess_square, piece)
        board.set_piece_offset(chess_square, offset)
        
    return board


def label_to_piece(label: str) -> Optional[chess.Piece]:
    """Converts a piece label to a chess.Piece instance.

    Args:
        label (str): Label of the piece (e.g., 'white-queen').

    Returns:
        Optional[chess.Piece]: Corresponding chess.Piece instance if label is valid, None otherwise.
    """
    piece_mapping = {
        "black-bishop": chess.Piece(chess.BISHOP, chess.BLACK),
        "black-king": chess.Piece(chess.KING, chess.BLACK),
        "black-knight": chess.Piece(chess.KNIGHT, chess.BLACK),
        "black-pawn": chess.Piece(chess.PAWN, chess.BLACK),
        "black-queen": chess.Piece(chess.QUEEN, chess.BLACK),
        "black-rook": chess.Piece(chess.ROOK, chess.BLACK),
        "white-bishop": chess.Piece(chess.BISHOP, chess.WHITE),
        "white-king": chess.Piece(chess.KING, chess.WHITE),
        "white-knight": chess.Piece(chess.KNIGHT, chess.WHITE),
        "white-pawn": chess.Piece(chess.PAWN, chess.WHITE),
        "white-queen": chess.Piece(chess.QUEEN, chess.WHITE),
        "white-rook": chess.Piece(chess.ROOK, chess.WHITE)
    }

    return piece_mapping.get(label)


def greyscale_to_board(image: np.ndarray, model: YOLO, flip: bool = False) -> PhysicalBoard:
    """Converts a grayscale image of a chessboard to a PhysicalBoard instance by detecting and mapping pieces.

    Args:
        image (np.ndarray): The grayscale image of the chessboard.
        model (YOLO): The YOLO model used to detect pieces in the image.
        flip (bool): Whether to flip the board orientation for black perspective. Defaults to False.

    Returns:
        PhysicalBoard: The resulting PhysicalBoard with detected pieces mapped to squares.
    """
    bbox, label, conf = detect_greyscale(image, model)
    mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)

    board = map_squares_to_board(mapped_squares, flip)
    return board
