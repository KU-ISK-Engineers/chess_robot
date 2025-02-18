from typing import NamedTuple, Optional, List
import cv2
from ultralytics import YOLO
import chess
import numpy as np

from src.core.board import PhysicalBoard, PieceOffset, flip_square


class MappedSquare(NamedTuple):
    """Represents a detected piece mapped to a square on a chessboard.

    Attributes:
        chess_square (chess.Square): The identified square on the board.
        offset (PieceOffset): Positional offset of the piece relative to the square center.
        piece (chess.Piece): Detected piece.
        confidence (float): Confidence score of the piece detection.
    """

    chess_square: chess.Square
    offset: PieceOffset
    piece: chess.Piece
    confidence: float


class DetectionResult(NamedTuple):
    """Results from detecting chess pieces on a chessboard.

    Attributes:
        bounding_boxes (List[List[int]]): Bounding boxes for detected pieces in [x, y, width, height] format.
        labels (List[str]): Labels for each detected piece (e.g., 'black-knight').
        confidences (List[float]): Confidence scores for each detected piece.
    """

    bounding_boxes: List[List[int]]
    labels: List[str]
    confidences: List[float]


def detect_grayscale(
    grayscale_image: np.ndarray,
    model: YOLO,
    conf_threshold: float = 0.5,
    iou_threshold: float = 0.45,
) -> DetectionResult:
    """Detects chess pieces in a grayscale image using a YOLO model.

    Converts a grayscale image to a 3-channel format for YOLO processing, then detects chess pieces
    based on confidence and IoU thresholds.

    Args:
        grayscale_image (np.ndarray): The grayscale image in which to detect chess pieces.
        model (YOLO): The YOLO model for detecting objects.
        conf_threshold (float, optional): Minimum confidence threshold for valid detections. Defaults to 0.5.
        iou_threshold (float, optional): IoU threshold for non-maximum suppression. Defaults to 0.45.

    Returns:
        DetectionResult: Contains bounding boxes, labels, and confidence scores for each detected piece.
                         Empty lists are returned if no detections meet the thresholds.
    """
    image = cv2.merge([grayscale_image] * 3)
    results = model.predict(image, conf=conf_threshold, iou=iou_threshold)
    labels = model.names

    bbox, label, conf = [], [], []

    if results and results[0].boxes:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        confs = results[0].boxes.conf.cpu().numpy()
        class_ids = results[0].boxes.cls.cpu().numpy().astype(int)

        for box, cf, class_id in zip(boxes, confs, class_ids):
            x1, y1, x2, y2 = map(int, box)
            bbox.append([x1, y1, x2 - x1, y2 - y1])
            label.append(labels[class_id])
            conf.append(cf)

    return DetectionResult(bounding_boxes=bbox, labels=label, confidences=conf)


def map_results_to_squares(
    img_width: int,
    img_height: int,
    detection_result: DetectionResult,
    max_piece_offset: float = 0.4,
) -> List[MappedSquare]:
    """Maps detection results to squares on an 8x8 chessboard.

    Divides the chessboard image into an 8x8 grid and maps each detected piece to its nearest square.
    Only includes pieces within a specified distance threshold from the square center.

    Note: Considers bottom-part of the image as first row.

    Args:
        img_width (int): Width of the chessboard image.
        img_height (int): Height of the chessboard image.
        detection_result (DetectionResult): Detected pieces with bounding boxes, labels, and confidence scores.
        max_piece_offset (float, optional): Maximum distance from square center to include piece. Defaults to 0.4.

    Returns:
        List[MappedSquare]: List of MappedSquare instances for detected pieces within the acceptable distance.
    """
    square_width = img_width / 8
    square_height = img_height / 8
    mapped_squares: list[MappedSquare] = []

    max_center_dx = square_width / 2
    max_center_dy = square_height / 2

    for box, lbl, cf in zip(
        detection_result.bounding_boxes,
        detection_result.labels,
        detection_result.confidences,
    ):
        x1, y1, x2, y2 = box[0], box[1], box[0] + box[2], box[1] + box[3]
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        col = int(center_x // square_width)
        row = int(center_y // square_height)
        square = chess.square(
            col, 7 - row
        )  # subtracted to make first row at the bottom of the image.

        center_col = col * square_width + square_width / 2
        center_row = row * square_height + square_height / 2

        dx_offset = (center_x - center_col) / max_center_dx
        dy_offset = (
            center_y - center_row
        ) / -max_center_dy  # inverted to make Y offset negative when it's below center.
        offset = PieceOffset(dx_offset, dy_offset)

        piece = label_to_piece(lbl)
        if (
            piece is not None
            and abs(dx_offset) <= max_piece_offset
            and abs(dy_offset) <= max_piece_offset
        ):
            mapped_squares.append(MappedSquare(square, offset, piece, cf))

    return mapped_squares


def map_squares_to_board(
    mapped_squares: List[MappedSquare], bottom_color: chess.Color
) -> PhysicalBoard:
    """Maps detected pieces to a PhysicalBoard instance based on the pieces color at the bottom of the image.

    Args:
        mapped_squares (List[MappedSquare]): List of detected pieces mapped to squares.
        bottom_color (chess.Color): Physical board color at the bottom used for creating virtual board, where white is always at the bottom.

    Returns:
        PhysicalBoard: A PhysicalBoard instance with pieces set on mapped squares.
    """
    board = PhysicalBoard()
    board.chess_board.clear_board()

    for mapped_square in mapped_squares:
        chess_square = (
            flip_square(mapped_square.chess_square)
            if bottom_color == chess.BLACK
            else mapped_square.chess_square
        )

        board.chess_board.set_piece_at(chess_square, mapped_square.piece)
        board.set_piece_offset(chess_square, bottom_color, mapped_square.offset)

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
        "white-rook": chess.Piece(chess.ROOK, chess.WHITE),
    }

    return piece_mapping.get(label)


def draw_bounding_boxes(
    chessboard_image: np.ndarray, detections: DetectionResult
) -> np.ndarray:
    """
    Draws bounding boxes for detected chess pieces.

    Args:
        chessboard_image (np.ndarray): The chessboard image.
        detections (DetectionResult): Object detection results.

    Returns:
        np.ndarray: Annotated chessboard image with bounding boxes.
    """
    annotated_image = chessboard_image.copy()

    for box in detections.bounding_boxes:
        x, y, width, height = box
        x2, y2 = x + width, y + height

        cv2.rectangle(annotated_image, (x, y), (x2, y2), (0, 255, 0), 2)

    return annotated_image


def draw_square_bounds(
    chessboard_image: np.ndarray,
) -> np.ndarray:
    """
    Draws grid lines to outline squares on the chessboard image.

    Args:
        chessboard_image (np.ndarray): The chessboard image.

    Returns:
        np.ndarray: Annotated image with grid lines drawn.
    """
    annotated_image = chessboard_image.copy()

    square_width = annotated_image.shape[1] / 8
    square_height = annotated_image.shape[0] / 8

    for col in range(1, 8):  # Start at 1 to avoid drawing over the left edge
        x = round(col * square_width)
        cv2.line(annotated_image, (x, 0), (x, annotated_image.shape[0]), (0, 255, 0), 1)

    for row in range(1, 8):  # Start at 1 to avoid drawing over the top edge
        y = round(row * square_height)
        cv2.line(annotated_image, (0, y), (annotated_image.shape[1], y), (0, 255, 0), 1)

    return annotated_image


def draw_mapped_squares(
    chessboard_image: np.ndarray, mapped_squares: list[MappedSquare]
) -> np.ndarray:
    """
    Visualizes mapped squares on the chessboard image.

    Args:
        image (np.ndarray): The chessboard image.
        mapped_squares (list[MappedSquare]): Mapped squares with piece information.

    Returns:
        np.ndarray: Annotated chessboard image.
    """
    annotated_image = chessboard_image.copy()

    square_width = annotated_image.shape[1] / 8
    square_height = annotated_image.shape[0] / 8

    for mapped_square in mapped_squares:
        chess_square = mapped_square.chess_square
        offset = mapped_square.offset
        piece_symbol = mapped_square.piece.symbol()

        col = chess.square_file(chess_square)
        row = 7 - chess.square_rank(chess_square)  # Convert to top-left origin

        square_center_x = round(col * square_width + square_width / 2)
        square_center_y = round(row * square_height + square_height / 2)

        piece_x = round(square_center_x + offset.x * square_width / 2)
        piece_y = round(square_center_y - offset.y * square_height / 2)

        cv2.circle(annotated_image, (piece_x, piece_y), 5, (255, 0, 0), -1)

        cv2.putText(
            annotated_image,
            piece_symbol,
            (square_center_x - 10, square_center_y + 10),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.7,
            color=(0, 255, 0),
            thickness=2,
        )

        cv2.putText(
            annotated_image,
            f"{offset.x:.2f}",
            (square_center_x - 30, square_center_y + 40),
            fontFace=cv2.FONT_HERSHEY_COMPLEX,
            fontScale=0.7,
            color=(255, 255, 255),
            thickness=2,
        )

        cv2.putText(
            annotated_image,
            f"{offset.y:.2f}",
            (square_center_x - 30, square_center_y + 60),
            fontFace=cv2.FONT_HERSHEY_COMPLEX,
            fontScale=0.7,
            color=(255, 255, 255),
            thickness=2,
        )

    return annotated_image


def grayscale_to_board(
    grayscale_image: np.ndarray,
    bottom_color: chess.Color,
    model: YOLO,
    conf_threshold: float = 0.5,
    iou_threshold: float = 0.45,
    max_piece_offset: float = 0.4,
    visualize: bool = False,
) -> PhysicalBoard:
    """Detects and maps chess pieces from a grayscale board image to a PhysicalBoard.

    Divides a top-down grayscale image of a chessboard into an 8x8 grid and maps detected pieces to their closest squares.
    The `perspective` parameter sets the board orientation, with `chess.WHITE` positioning white at the image's bottom.

    Args:
        grayscale_image (np.ndarray): Grayscale chessboard image from a top-down view.
        bottom_color (chess.Color): Color at the bottom of the image.
        model (YOLO): YOLO model used to detect pieces.
        conf_threshold (float, optional): Confidence threshold for object detection. Defaults to 0.5.
        iou_threshold (float, optional): IoU threshold for non-maximum suppression. Defaults to 0.45.
        max_piece_offset (float, optional): Max distance offset from square center for mapping. Defaults to 0.4.

    Returns:
        PhysicalBoard: PhysicalBoard with mapped pieces and offsets.
    """
    detection = detect_grayscale(grayscale_image, model, conf_threshold, iou_threshold)
    mapped_squares = map_results_to_squares(
        grayscale_image.shape[1], grayscale_image.shape[0], detection, max_piece_offset
    )
    board = map_squares_to_board(mapped_squares, bottom_color)

    if visualize:
        image = cv2.cvtColor(grayscale_image, cv2.COLOR_GRAY2BGR)
        image = draw_square_bounds(image)
        image = draw_bounding_boxes(image, detection)
        image = draw_mapped_squares(image, mapped_squares)

        cv2.waitKey(1)

        resized_image = cv2.resize(image, (1280, 720))
        cv2.imshow("Board detection visualization", resized_image)
        cv2.waitKey(1)

    return board
