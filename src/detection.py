import cv2
from typing import List
from collections import namedtuple
from ultralytics import YOLO

# Minimum piece detection confidence threshold
THRESHOLD_CONFIDENCE = 0.5

# Minimum distance percentage of the piece from the square center
THRESHOLD_DISTANCE = 0.3

MappedSquare = namedtuple('MappedSquare', ['row', 'col', 'dx_percent', 'dy_percent', 'label', 'confidence'])

def detect_greyscale(image, model):
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

def annotate_bboxes(image, bbox, label, confidence):
    for box, lbl, cf in zip(bbox, label, confidence):
        x, y, w, h = box
        label_text = f"{lbl}: {cf:.2f}"
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(image, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    return image

def map_bboxes_to_squares(image, bbox, label, confidence) -> List[MappedSquare]:
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

        dx_percent = (center_x - center_col) / max_center_dx
        dy_percent = (center_y - center_row) / max_center_dy

        # Filter out pieces too far from the square center
        if abs(dx_percent) <= THRESHOLD_DISTANCE and abs(dy_percent) <= THRESHOLD_DISTANCE:
            mapped_squares.append(MappedSquare(row, col, dx_percent, dy_percent, lbl, cf))

    return mapped_squares

def annotate_squares(image, mapped_squares: List[MappedSquare]):
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

        text = piece_letter + f"({square.dx_percent:.2f},{square.dy_percent:.2f})"
        cv2.putText(image, text, (center_x - 10, center_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    return image

def label_to_char(label):
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

def detect_squares(image, model) -> List[MappedSquare]:
    bbox, label, conf = detect_greyscale(image, model)
    mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)
    return mapped_squares

# ----------------- TESTING -----------------

#from pypylon import pylon
from ultralytics import YOLO
import sys

def setup_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate.SetValue(5)
    camera.ExposureAuto.SetValue('Continuous')
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("RGB8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    return camera

def preprocess_image(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py path_to_model")
        sys.exit(1)

    model = YOLO(sys.argv[1])
    camera = setup_camera()

    while camera.IsGrabbing():
        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if grab_result.GrabSucceeded():
            image = grab_result.Array
            grab_result.Release()
            image = preprocess_image(image)

            # For yolo model
            bbox, labels, confs = detect_greyscale(image, model)
            annotate_bboxes(image, bbox, labels, confs)

            mapped_squares = map_bboxes_to_squares(image, bbox, labels, confs)
            annotate_squares(image, mapped_squares, bbox, labels, confs)

            cv2.namedWindow('Processed Image', cv2.WINDOW_NORMAL)
            cv2.imshow('Processed Image', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def image_main():
    if len(sys.argv) != 3:
        print("Usage: python script.py path_to_model path_to_image")
        sys.exit(1)

    model = YOLO(sys.argv[1])
    image = cv2.imread(sys.argv[2])
    image = preprocess_image(image)

    # For yolo model
    bbox, label, conf = detect_greyscale(image, model)
    annotate_bboxes(image, bbox, label, conf)

    mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)
    annotate_squares(image, mapped_squares)

    cv2.namedWindow('Processed Image', cv2.WINDOW_NORMAL)
    cv2.imshow('Processed Image', image)
    cv2.waitKey()

if __name__ == "__main__":
    image_main()