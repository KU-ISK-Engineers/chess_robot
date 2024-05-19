import sys
import cv2
import os
from ultralytics import YOLO

def preprocess_image(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def detect_objects(image, model):
    # YOLOv8 expects 3-channel images; converting grayscale to 3-channel
    image = cv2.merge([image, image, image])
    
    # Perform object detection
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
            print(label_text)
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    return image

def process_image(image_path, model):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at the specified path: {image_path}")

    image = preprocess_image(image)

    bbox, label, conf = detect_objects(image, model)

    mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)
    image = annotate_squares(image, mapped_squares, bbox, label, conf, model.names)
    
    cv2.namedWindow('Processed Image', cv2.WINDOW_NORMAL)
    cv2.imshow('Processed Image', image)
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

def main(folder_path, model_path):
    try:
        model = YOLO(model_path)

        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_path = os.path.join(folder_path, filename)
                print(f"Processing {image_path}")
                process_image(image_path, model)

    except Exception as e:
        print("An error occurred:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python identify_images_in_folder.py path_to_folder path_to_model")
        sys.exit(1)

    folder_path = sys.argv[1]
    model_path = sys.argv[2]
    main(folder_path, model_path)