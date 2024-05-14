import sys
import cv2
from pypylon import pylon
from cvlib.object_detection import YOLO

def test():
    original = image.copy()  # Keep a copy of the original for drawing

    bbox, label, conf = yolo.detect_objects(image)

    # Manual bounding box drawing for debugging
    for box, lbl, cf in zip(bbox, label, conf):
        if cf > 0.5:  # Filter out low confidence detections
            x, y, w, h = box
            cv2.rectangle(original, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(original, f"{lbl} {cf:.2f}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

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
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    height, width = image.shape[:2]
    new_width = 800
    new_height = int((new_width / width) * height)
    image = cv2.resize(image, (new_width, new_height))

    return image

def setup_points(file_path):
    with open(file_path, 'r') as file:
        points = list(map(int, file.readline().strip().split()))
    if len(points) != 4:
        raise ValueError("Expected four integers in the file.")
    return points

def crop_image(image, points):
    y_min, y_max, x_min, x_max = points
    cropped_image = image[y_min:y_max, x_min:x_max]
    return cropped_image

def setup_yolo(weights_f):
    config = "yolov4-tiny-custom.cfg"
    labels = "obj.names"
    yolo = YOLO(weights_f, config, labels)
    return yolo

def detect(image, yolo):
    bbox, label, conf = yolo.detect_objects(image)

    height, width, _ = image.shape
    resize_factor = 416

    # Resized bboxes
    for i in range(len(bbox)):
        x1, y1, x2, y2 = bbox[i]
        x1 = int(x1 * width / resize_factor)
        y1 = int(y1 * height / resize_factor)
        x2 = int(x2 * width / resize_factor)
        y2 = int(y2 * height / resize_factor)
        bbox[i] = [x1, y1, x2, y2]

    return bbox, label, conf

def draw_bbox(image, bbox, label, confidence):
    for box, lbl, cf in zip(bbox, label, confidence):
        if cf > 0.5:  # Filter out low confidence detections
            x1, y1, x2, y2 = box

            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(image, f"{lbl} {cf:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

def map_bboxes_to_squares(image, bbox, label, confidence):
    img_height, img_width, _ = image.shape

    square_width = img_width // 8
    square_height = img_height // 8
    
    mapped_squares = []
    
    for box, lbl, cf in zip(bbox, label, confidence):
        if cf > 0.5:
            x1, y1, x2, y2 = box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            col = center_x // square_width
            row = center_y // square_height
            
            mapped_squares.append((row, col, lbl, cf))
    
    return mapped_squares

def map_label_to_char(lbl):
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
    
    return label_to_char.get(lbl, "?")  

def annotate_squares(image, mapped_squares):
    # Define the number of rows and columns in the chessboard
    rows = 8
    cols = 8

    # Calculate the width and height of each square
    square_width = image.shape[1] // cols
    square_height = image.shape[0] // rows

    # Draw the annotations and squares on the image
    for row in range(rows):
        for col in range(cols):
            # Calculate the top-left and bottom-right corners of the current square
            top_left = (col * square_width, row * square_height)
            bottom_right = ((col + 1) * square_width, (row + 1) * square_height)

            # Draw the square using a rectangle
            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)  # Green color, 2 px thickness

    # Draw the pieces on their corresponding squares
    for (row, col, lbl, _) in mapped_squares:
        piece_letter = map_label_to_char(lbl)

        # Calculate the center for placing text
        center_x = col * square_width + square_width // 2
        center_y = row * square_height + square_height // 2

        # Draw the piece letter on the image
        cv2.putText(image, piece_letter, (center_x - 10, center_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)  

    return image

def main(camera, yolo, points):
    try:
        while camera.IsGrabbing():
            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                image = grab_result.Array
                image = preprocess_image(image)
                image = crop_image(image, points)

                bbox, label, conf = detect(image, yolo)
                #draw_bbox(image, bbox, label, conf)

                #print(bbox)

                

                mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)                
                #print(mapped_squares)
                image = annotate_squares(image, mapped_squares)

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
    yolo = setup_yolo(sys.argv[1])
    points = setup_points(sys.argv[2])

    main(camera, yolo, points)
