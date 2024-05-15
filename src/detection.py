import cv2
import chess

BBOX_RESIZE_FACTOR = 416

def detect(image, yolo):
    bbox, label, conf = yolo.detect_objects(image)

    height, width, _ = image.shape

    # Resized bboxes
    for i in range(len(bbox)):
        x1, y1, x2, y2 = bbox[i]
        x1 = int(x1 * width / BBOX_RESIZE_FACTOR)
        y1 = int(y1 * height / BBOX_RESIZE_FACTOR)
        x2 = int(x2 * width / BBOX_RESIZE_FACTOR)
        y2 = int(y2 * height / BBOX_RESIZE_FACTOR)
        bbox[i] = [x1, y1, x2, y2]

    return bbox, label, conf

def draw_bbox(image, bbox, label, confidence):
    for box, lbl, cf in zip(bbox, label, confidence):
        if cf > 0.5:  # Filter out low confidence detections
            x1, y1, x2, y2 = box

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, f"{lbl} {cf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


def bbox_to_board(image, bbox, label, confidence):
    img_height, img_width, _ = image.shape

    square_width = img_width // 8
    square_height = img_height // 8
    
    board = chess.Board(empty=True)
    
    for box, lbl, cf in zip(bbox, label, confidence):
        if cf > 0.5 and lbl in label_to_piece:
            x1, y1, x2, y2 = box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            col = center_x // square_width
            row = center_y // square_height

            # Calculate chessboard square
            square_index = (7 - row) * 8 + col
            piece_type, color = label_to_piece[lbl]
            piece = chess.Piece(piece_type, color)
            
            # Place the piece on the board
            board.set_piece_at(square_index, piece)
    
    return board


def label_to_piece(label):
    pieces = {
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

    return pieces[label]

def annotate_squares(image, board):
    # Define the number of rows and columns in the chessboard
    rows = 8
    cols = 8

    # Calculate the width and height of each square
    square_width = image.shape[1] // cols
    square_height = image.shape[0] // rows

    # Draw the squares on the image
    for row in range(rows):
        for col in range(cols):
            # Calculate the top-left and bottom-right corners of the current square
            top_left = (col * square_width, row * square_height)
            bottom_right = ((col + 1) * square_width, (row + 1) * square_height)

            # Draw the square using a rectangle
            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)  # Green color, 2 px thickness

    # Draw the pieces on their corresponding squares
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            piece_letter = piece.symbol()

            # Calculate the row and column from the square index
            row = 7 - (square // 8)
            col = square % 8

            # Calculate the center for placing text
            center_x = col * square_width + square_width // 2
            center_y = row * square_height + square_height // 2

            # Draw the piece letter on the image
            cv2.putText(image, piece_letter, (center_x - 10, center_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)  # Yellow color, 2 px thickness

    return image

def image_to_board(image, yolo):
    bbox, label, conf = detect(image, yolo)
    return bbox_to_board(image, bbox, label, conf)

