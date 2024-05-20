import cv2
import chess
import numpy as np

def detect(image, model):
    # For greyscale
    image = cv2.merge([image, image, image])

    results = model(image)
    bbox = []
    label = []
    conf = []
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()
        confs = result.boxes.conf.cpu().numpy()
        class_ids = result.boxes.cls.cpu().numpy().astype(int)
        labels = result.names
        for box, cf, class_id in zip(boxes, confs, class_ids):
            if cf > 0.5:
                x1, y1, x2, y2 = map(int, box)
                bbox.append([x1, y1, x2 - x1, y2 - y1])
                label.append(class_id)
                conf.append(cf)
    return bbox, label, conf

def annotate_bboxes(image, bbox, label, confidence, labels):
    for box, lbl, cf in zip(bbox, label, confidence):
        if cf > 0.5:  # Filter out low confidence detections
            x, y, w, h = box
            label_text = f"{labels[lbl]}: {cf:.2f}"
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

def map_bboxes_to_squares(image, bbox, label, confidence):
    img_height, img_width = image.shape[:2]
    square_width = img_width // 8
    square_height = img_height // 8
    mapped_squares = []

    # Calculate the maximum possible distance (half the diagonal of the square)
    max_distance = np.sqrt((square_width / 2) ** 2 + (square_height / 2) ** 2)

    for box, lbl, cf in zip(bbox, label, confidence):
        if cf > 0.5:
            x1, y1, x2, y2 = box[0], box[1], box[0] + box[2], box[1] + box[3]
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            col = int(center_x // square_width)
            row = int(center_y // square_height)

            center_col = col * square_width + square_width / 2
            center_row = row * square_height + square_height / 2

            distance = np.sqrt((center_x - center_col) ** 2 + (center_y - center_row) ** 2)
            distance_percentage = 1 - (distance / max_distance)

            if distance_percentage >= 0.6:
                mapped_squares.append((row, col, lbl, cf, distance_percentage))
    return mapped_squares

# Annotate squares on the chessboard
def annotate_squares(image, mapped_squares, bbox, label, conf, labels):
    rows = 8
    cols = 8
    square_width = image.shape[1] // cols
    square_height = image.shape[0] // rows

    for row in range(rows):
        for col in range(cols):
            top_left = (col * square_width, row * square_height)
            bottom_right = ((col + 1) * square_width, (row + 1) * square_height)
            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

    # piece letters
    for (row, col, lbl, _, dist) in mapped_squares:
        piece_letter = map_label_to_char(lbl, labels)
        center_x = col * square_width + square_width // 2
        center_y = row * square_height + square_height // 2
        cv2.putText(image, piece_letter + f"({dist:.2f})", (center_x - 10, center_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

    return image


# Map label to chess notation character
def map_label_to_char(lbl, labels):
    label_to_char = {
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
    label_name = labels[lbl]
    return label_to_char.get(label_name, "?")

def detect_squares(image, model):
    bbox, label, conf = detect(image, model)
    mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)
    return mapped_squares


# ----------------- TESTING -----------------

from pypylon import pylon
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
            bbox, label, conf = detect(image, model)
            annotate_bboxes(image, bbox, label, conf, model.names)

            mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)
            annotate_squares(image, mapped_squares, bbox, label, conf, model.names)

            cv2.namedWindow('Processed Image', cv2.WINDOW_NORMAL)
            cv2.imshow('Processed Image', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == "__main__":
    main()