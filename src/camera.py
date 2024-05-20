import cv2
from typing import List, Tuple
from pypylon import pylon
import chess
from ultralytics import YOLO
from .detection import image_to_board
import numpy as np

class CameraDetection:
    def __init__(self, camera: pylon.InstantCamera, model: YOLO, timeout: int = 5000) -> None:
        self.camera = camera
        self.timeout = timeout
        self.model = model
        self.prev_points = None

    def capture_image(self) -> cv2.Mat:
        if not self.camera.IsGrabbing():
            raise RuntimeError("Camera is not grabbing images.")
        
        grab_result = self.camera.RetrieveResult(self.timeout, pylon.TimeoutHandling_ThrowException)
        if not grab_result.GrabSucceeded():
            raise RuntimeError("Failed to grab image from camera.")

        image = grab_result.Array
        image = self._preprocess_image(image)
        image = crop_image(image, self.points)

        self.image = image
        return self.image
    
    def capture_board(self) -> chess.Board:
       return image_to_board(self.capture_image(), self.model)
    
    def _preprocess_image(self, image: cv2.Mat) -> cv2.Mat:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        rect = detect_aruco_markers(image)

        if self.points is not None:
            prev_points = rect

        if prev_points is not None:
            #cv2.polylines(image, [np.int32(rect)], isClosed=True, color=(0, 255, 0), thickness=2)
            image = crop_image(image, prev_points)
            image = process_image(image, model)
        else:
            print('Waiting for board points...')

        return image
            


def preprocess_image(image: cv2.Mat, prev_points = None) -> cv2.Mat:

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

# --- TESTING ---
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

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py path_to_model")
        sys.exit(1)

    model = YOLO(sys.argv[1])
    camera = setup_camera()

    detection = CameraDetection(camera, model)
    pass

if __name__ == "__main__":
    main()
