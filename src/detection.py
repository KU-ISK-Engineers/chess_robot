import cv2
from typing import List, Tuple
from collections import namedtuple
from ultralytics import YOLO
import chess
import chess.svg
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from .board import BoardWithOffsets, SquareOffset, SQUARE_CENTER

# Minimum piece detection confidence threshold
THRESHOLD_CONFIDENCE = 0.5

# Minimum distance percentage of the piece from the square center
THRESHOLD_DISTANCE = 0.7

MappedSquare = namedtuple('MappedSquare', ['row', 'col', 'dx_offset', 'dy_offset', 'label', 'confidence'])

# --- PIECE DETECTION ---

def detect_greyscale(image: cv2.Mat, model: YOLO):
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

def annotate_bboxes(image: cv2.Mat, bbox, label, confidence):
    for box, lbl, cf in zip(bbox, label, confidence):
        x, y, w, h = box
        label_text = f"{lbl}: {cf:.2f}"
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(image, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    return image

# --- MAPPING TO SQUARES ---

def map_bboxes_to_squares(image: cv2.Mat, bbox, label, confidence) -> List[MappedSquare]:
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

        # Calculate if piece is close enough to the square center
        center_col = col * square_width + square_width // 2
        center_row = row * square_height + square_height // 2

        dx_offset = (center_x - center_col) / max_center_dx
        dy_offset = (center_y - center_row) / max_center_dy

        # Filter out pieces too far from the square center
        if abs(dx_offset) <= THRESHOLD_DISTANCE and abs(dy_offset) <= THRESHOLD_DISTANCE:
            mapped_squares.append(MappedSquare(row, col, dx_offset, dy_offset, lbl, cf))

    return mapped_squares

def annotate_squares(image: cv2.Mat, mapped_squares: List[MappedSquare]) -> cv2.Mat:
    square_height = image.shape[0] // 8
    square_width = image.shape[1] // 8

    # Draw rectangles around the squares
    for row in range(8):
        for col in range(8):
            top_left = (col * square_width, row * square_height)
            bottom_right = ((col + 1) * square_width, (row + 1) * square_height)
            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

    # Draw piece letter in the center of the square
    for square in mapped_squares:
        piece_letter = label_to_char(square.label)
        center_x = square.col * square_width + square_width // 2
        center_y = square.row * square_height + square_height // 2

        text = piece_letter + f"({square.dx_offset:.2f},{square.dy_offset:.2f})"
        cv2.putText(image, text, (center_x - 10, center_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    return image

def label_to_char(label: str):
    pieces = {
        "black-bishop": "b",
        "black-king": "k",
        "black-knight": "n",
        "black-pawn": "p",
        "black-queen": "q",
        "black-rook": "r",
        "white-bishop": "B",
        "white-king": "K",
        "white-knight": "N",
        "white-pawn": "P",
        "white-queen": "Q",
        "white-rook": "R"
    }
    return pieces.get(label, "?")

# --- MAPPING TO BOARD ---
def map_squares_to_board(mapped_squares: List[MappedSquare], perspective: chess.Color = chess.WHITE) -> BoardWithOffsets:
    board = chess.Board()
    board.clear_board()

    offsets = [[SQUARE_CENTER for _ in range(8)] for _ in range(8)]
    
    for square in mapped_squares:
        # Map perspective
        if perspective == chess.WHITE:
            row = 7 - square.row
            col = 7 - square.col
        else:
            row = square.row
            col = square.col

        piece_label = square.label
        
        # Calculate chessboard square index
        square_index = chess.square(col, row)
        piece_type, color = label_to_piece(piece_label)
        piece = chess.Piece(piece_type, color)
        
        # Place the piece on the board
        board.set_piece_at(square_index, piece)
        
        # Store the distance percentages
        offsets[chess.square_rank(square_index)][chess.square_file(square_index)] = SquareOffset(square.dx_offset, square.dy_offset)

    return BoardWithOffsets(board, offsets, perspective)

def label_to_piece(label: str) -> Tuple[chess.Piece, chess.Color]:
    piece_mapping = {
        "black-bishop": (chess.BISHOP, chess.BLACK),
        "black-king": (chess.KING, chess.BLACK),
        "black-knight": (chess.KNIGHT, chess.BLACK),
        "black-pawn": (chess.PAWN, chess.BLACK),
        "black-queen": (chess.QUEEN, chess.BLACK),
        "black-rook": (chess.ROOK, chess.BLACK),
        "white-bishop": (chess.BISHOP, chess.WHITE),
        "white-king": (chess.KING, chess.WHITE),
        "white-knight": (chess.KNIGHT, chess.WHITE),
        "white-pawn": (chess.PAWN, chess.WHITE),
        "white-queen": (chess.QUEEN, chess.WHITE),
        "white-rook": (chess.ROOK, chess.WHITE)
    }
    return piece_mapping.get(label)

def visualise_chessboard(board: BoardWithOffsets):
    # Generate the SVG image of the board
    svg_image = chess.svg.board(board=board.chess_board)

    # Save the SVG image to a file
    with open('chess_board.svg', 'w') as f:
        f.write(svg_image)

def image_to_board(image: cv2.Mat, model: YOLO, perspective: chess.Color = chess.WHITE) -> BoardWithOffsets:
    bbox, label, conf = detect_greyscale(image, model)
    mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)
    board = map_squares_to_board(mapped_squares, perspective)
    return board

