import sys
import cv2
from pypylon import pylon
import numpy as np
import os

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
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def setup_points(file_path):
    with open(file_path, 'r') as file:
        points = list(map(int, file.readline().strip().split()))
    if len(points) != 4:
        raise ValueError("Expected four integers in the file.")
    return points

def crop_image(image, points):
    return image
    y_min, y_max, x_min, x_max = points
    cropped_image = image[y_min:y_max, x_min:x_max]
    return cropped_image

def detect_objects(image, net, output_layers):
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    detections = net.forward(output_layers)

    bbox = []
    label = []
    conf = []

    h, w = image.shape[:2]

    for output in detections:
        for detection in output:
            scores = detection[5:]
            class_id = int(scores.argmax())
            confidence = scores[class_id]
            if confidence > 0.5:
                box = detection[0:4] * [w, h, w, h]
                (centerX, centerY, width, height) = box.astype("int")

                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                bbox.append([x, y, int(width), int(height)])
                label.append(class_id)
                conf.append(float(confidence))

    return bbox, label, conf

def map_bboxes_to_squares(image, bbox, label, confidence):
    img_height, img_width = image.shape[:2]

    square_width = img_width // 8
    square_height = img_height // 8

    mapped_squares = []

    for box, lbl, cf in zip(bbox, label, confidence):
        if cf > 0.5:
            x1, y1, x2, y2 = box[0], box[1], box[0] + box[2], box[1] + box[3]
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            col = center_x // square_width
            row = center_y // square_height

            mapped_squares.append((row, col, lbl, cf))

    return mapped_squares

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

def annotate_squares(image, mapped_squares, bbox, label, conf, labels):
    rows = 8
    cols = 8

    square_width = image.shape[1] // cols
    square_height = image.shape[0] // rows

    for row in range(rows):
        for col in range(cols):
            top_left = (col * square_width, row * square_height)
            bottom_right = ((col + 1) * square_width, (row + 1) * square_height)

            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)  # Green color, 2 px thickness

    for (row, col, lbl, _) in mapped_squares:
        piece_letter = map_label_to_char(lbl, labels)

        center_x = col * square_width + square_width // 2
        center_y = row * square_height + square_height // 2

        cv2.putText(image, piece_letter, (center_x - 10, center_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        for (box, lbl, cf) in zip(bbox, label, conf):
            if cf > 0.5:
                x, y, w, h = box
                label_text = f"{labels[lbl]}: {cf:.2f}"
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(image, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    return image

def main(camera, points):
    config_path = "yolov4-tiny.cfg"
    weights_path = "yolov4-tiny.weights"
    labels_path = "obj.names"

    # Check if files exist
    if not os.path.isfile(config_path):
        print(f"Error: {config_path} does not exist.")
        sys.exit(1)
    if not os.path.isfile(weights_path):
        print(f"Error: {weights_path} does not exist.")
        sys.exit(1)
    if not os.path.isfile(labels_path):
        print(f"Error: {labels_path} does not exist.")
        sys.exit(1)

    try:
        net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
        with open(labels_path, "r") as f:
            labels = f.read().strip().split("\n")
        layer_names = net.getLayerNames()
        output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

        while camera.IsGrabbing():
            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                image = grab_result.Array
                image = crop_image(image, points)
                image = preprocess_image(image)

                bbox, label, conf = detect_objects(image, net, output_layers)



                mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)
                image = annotate_squares(image, mapped_squares, bbox, label, conf, labels)
                cv2.namedWindow('Camera View', cv2.WINDOW_NORMAL)
                cv2.imshow('Camera View', image)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    finally:
        camera.StopGrabbing()
        camera.Close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python identify_real_time.py path_to_weights path_to_points")
        sys.exit(1)

    camera = setup_camera()
    points = setup_points(sys.argv[2])

    main(camera, points)
