import cv2
import numpy as np
from pypylon import pylon
import sys
from ultralytics import YOLO

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

def centroid(rectangle):
    x_coords = [point[0] for point in rectangle]
    y_coords = [point[1] for point in rectangle]
    centroid_x = sum(x_coords) / len(x_coords)
    centroid_y = sum(y_coords) / len(y_coords)
    return centroid_x, centroid_y

def find_rectangles(pts):
    grouped_rectangles = [pts[i:i + 4] for i in range(0, len(pts), 4)]

    # Calculate centroids for all rectangles
    centroids = [centroid(rect) for rect in grouped_rectangles]

    # Pair centroids with their respective rectangles
    centroids_rectangles = list(zip(centroids, grouped_rectangles))

    # Sort by y-coordinate (to separate top and bottom)
    sorted_by_y = sorted(centroids_rectangles, key=lambda x: x[0][1])

    # Top two rectangles
    top_two = sorted_by_y[:2]
    # Bottom two rectangles
    bottom_two = sorted_by_y[2:]

    # Sort top two by x-coordinate (to get left and right)
    top_left, top_right = sorted(top_two, key=lambda x: x[0][0])

    # Sort bottom two by x-coordinate (to get left and right)
    bottom_left, bottom_right = sorted(bottom_two, key=lambda x: x[0][0])

    # Extract the rectangles from the sorted pairs
    top_left_rect = top_left[1]
    top_right_rect = top_right[1]
    bottom_left_rect = bottom_left[1]
    bottom_right_rect = bottom_right[1]

    return top_left_rect, top_right_rect, bottom_left_rect, bottom_right_rect

def sort_rectangle_points(points):
    # Calculate the centroid of the rectangle
    centroid = np.mean(points, axis=0)
    
    # Calculate the angle of each point with respect to the centroid
    angles = np.arctan2(points[:, 1] - centroid[1], points[:, 0] - centroid[0])
    
    # Sort points based on the angles
    sorted_points = points[np.argsort(angles)]
    
    # Ensure points are in the order: top-left, top-right, bottom-right, bottom-left
    top_left = sorted_points[0]
    top_right = sorted_points[1]
    bottom_right = sorted_points[2]
    bottom_left = sorted_points[3]
    
    return top_left, top_right, bottom_left, bottom_right


def order_points(pts, image):
    top_left_rect, top_right_rect, bottom_left_rect, bottom_right_rect = find_rectangles(pts)

    # Sort points within each rectangle
    top_left_sorted = sort_rectangle_points(top_left_rect)
    top_right_sorted = sort_rectangle_points(top_right_rect)
    bottom_left_sorted = sort_rectangle_points(bottom_left_rect)
    bottom_right_sorted = sort_rectangle_points(bottom_right_rect)

    top_left = top_left_sorted[1]  # New top-left (top_left_rect top-right corner)
    top_right = top_right_sorted[0]  # New top-right (top_right_rect top-left corner)
    bottom_left = bottom_left_sorted[3]  # New bottom-left (bottom_left_rect bottom-right corner)
    bottom_right = bottom_right_sorted[2]  # New bottom-right (bottom_right_rect bottom-left corner)

    # Initial sorting of points based on their x-coordinates
    rect = np.zeros((4, 2), dtype="float32")

    rect[0] = [top_right[0] - 10, top_right[1]]  # New top-left
    rect[1] = [top_left[0] + 10, top_left[1]]  # New top-right
    rect[2] = [bottom_left[0] + 10, bottom_left[1]]  # New bottom-left
    rect[3] = [bottom_right[0] - 3, bottom_right[1]]  # New bottom-right

    return rect

# Process the image
def process_image(image, model):
    bbox, label, conf = detect_objects(image, model)
    mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)
    image = annotate_squares(image, mapped_squares, bbox, label, conf, model.names)
    return image

def detect_aruco_markers(image):
    # Define the dictionary and parameters for ArUco marker detection
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    aruco_params = cv2.aruco.DetectorParameters()

    # Detect markers in the image
    corners, ids, rejected = cv2.aruco.detectMarkers(image, aruco_dict, parameters=aruco_params)
    
    if ids is not None and len(ids) == 4:
        # Draw detected markers
        #cv2.aruco.drawDetectedMarkers(image, corners, ids)

        #print(corners)
        
        # Collect all corner points
        all_points = []
        for corner in corners:
            corner = corner.reshape((4, 2))
            for point in corner:
                all_points.append(point)

        # Order the points in a consistent way (top-left, top-right, bottom-right, bottom-left)
        all_points = np.array(all_points)
        rect = order_points(all_points, image)

        return rect

    return 

def crop_image(image, rect):
    (tl, tr, bl, br) = rect
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

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    return warped


# Map bounding boxes to chessboard squares
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

    # bboxes
    for (box, lbl, cf) in zip(bbox, label, conf):
        if cf > 0.5:
            x, y, w, h = box
            label_text = f"{labels[lbl]}: {cf:.2f}"
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    return image


# Object detection using YOLO
def detect_objects(image, model):
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

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py path_to_model")
        sys.exit(1)
    model = YOLO(sys.argv[1])
    camera = setup_camera()

    prev_points = None

    while camera.IsGrabbing():
        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
        if grab_result.GrabSucceeded():
            image = grab_result.Array
            grab_result.Release()

            image = preprocess_image(image)
            rect = detect_aruco_markers(image)
        
            if rect is not None:
                prev_points = rect

            if prev_points is not None:
                #cv2.polylines(image, [np.int32(rect)], isClosed=True, color=(0, 255, 0), thickness=2)
                image = crop_image(image, prev_points)
                image = process_image(image, model)
            else:
                print('Waiting for board points...')

        cv2.namedWindow('Processed Image', cv2.WINDOW_NORMAL)
        cv2.imshow('Processed Image', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.StopGrabbing()
    camera.Close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
