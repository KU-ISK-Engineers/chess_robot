import cv2
from typing import NamedTuple, Optional
from ultralytics import YOLO
import chess
import chess.svg
import numpy as np
from .board import RealBoard, SquareOffset

# Minimum piece detection confidence threshold
THRESHOLD_CONFIDENCE = 0.5

# Minimum distance percentage of the piece from the square center
THRESHOLD_DISTANCE = 0.7

class MappedSquare(NamedTuple):
    chess_square: chess.Square
    offset: SquareOffset
    label: str
    confidence: float

# --- PIECE DETECTION ---

def detect_greyscale(image: np.ndarray, model: YOLO) -> tuple[list, list[str], list[float]]:
    # For greyscale
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

# --- MAPPING TO SQUARES ---

def map_bboxes_to_squares(image: np.ndarray, bbox: list, label: list[str], confidence: list[float]) -> list[MappedSquare]:
    img_height, img_width = image.shape[:2]
    square_width = img_width // 8
    square_height = img_height // 8
    mapped_squares = []

    # Calculate the maximum possible distance from square center (half the diagonal of the square)
    max_center_dx = square_width // 2
    max_center_dy = square_height // 2

    for box, lbl, cf in zip(bbox, label, confidence):
        # Calculate to which square piece belongs
        x1, y1, x2, y2 = box[0], box[1], box[0] + box[2], box[1] + box[3]
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2

        col = int(center_x // square_width)
        row = int(center_y // square_height)

        square = chess.square(col, row)

        # Calculate if piece is close enough to the square center
        center_col = col * square_width + square_width // 2
        center_row = row * square_height + square_height // 2

        dx_offset = (center_x - center_col) / max_center_dx
        dy_offset = (center_y - center_row) / max_center_dy

        offset = SquareOffset(dx_offset, dy_offset)

        # Filter out pieces too far from the square center
        if abs(dx_offset) <= THRESHOLD_DISTANCE and abs(dy_offset) <= THRESHOLD_DISTANCE:
            mapped_squares.append(MappedSquare(square, offset, lbl, cf))

    return mapped_squares

# --- MAPPING TO BOARD ---
def map_squares_to_board(mapped_squares: list[MappedSquare], flip: bool = False) -> RealBoard:
    board = RealBoard()
    board.clear_board()
    
    for mapped_square in mapped_squares:
        if flip:
            chess_square = 63 - mapped_square.chess_square
            offset = SquareOffset(-mapped_square.offset.x, -mapped_square.offset.y)
        else:
            chess_square = mapped_square.chess_square
            offset = mapped_square.offset

        piece = label_to_piece(mapped_square.label)
        
        # Place the piece on the board
        board.set_piece_at(chess_square, piece, offset=offset)
        
    return board

def label_to_piece(label: str) -> Optional[chess.Piece]:
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

def greyscale_to_board(image: np.ndarray, model: YOLO, flip: bool = False) -> RealBoard:
    bbox, label, conf = detect_greyscale(image, model)
    mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)

    board = map_squares_to_board(mapped_squares, flip)
    return board

def crop_image_by_area(image: np.ndarray, area) -> np.ndarray:
    (tl, tr, bl, br) = area
    width_top = np.linalg.norm(tr - tl)
    width_bottom = np.linalg.norm(br - bl)
    max_width = max(int(width_top), int(width_bottom))

    height_left = np.linalg.norm(bl - tl)
    height_right = np.linalg.norm(br - tr)
    max_height = max(int(height_left), int(height_right))

    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]], dtype="float32")

    M = cv2.getPerspectiveTransform(area, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    return warped

