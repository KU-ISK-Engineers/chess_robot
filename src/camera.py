import cv2
from typing import List, Tuple
from pypylon import pylon
import chess
from cvlib.object_detection import YOLO
from .detection import image_to_board

class CameraDetection:
    def __init__(self, camera: pylon.InstantCamera, crop_points: List[int], yolo: YOLO, timeout: int = 5000) -> None:
        self.camera = camera
        self.points = crop_points
        self.timeout = timeout
        self.yolo = yolo

    def capture_image(self) -> cv2.Mat:
        if not self.camera.IsGrabbing():
            raise RuntimeError("Camera is not grabbing images.")
        
        grab_result = self.camera.RetrieveResult(self.timeout, pylon.TimeoutHandling_ThrowException)
        if not grab_result.GrabSucceeded():
            raise RuntimeError("Failed to grab image from camera.")

        image = grab_result.Array
        image = _preprocess_image(image)
        image = _crop_image(image, self.points)

        self.image = image
        return self.image
    
    def capture_board(self) -> chess.Board:
       return image_to_board(self.capture_image(), self.yolo)


def _preprocess_image(image: cv2.Mat) -> cv2.Mat:
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    height, width = image.shape[:2]
    new_width = 800
    new_height = int((new_width / width) * height)
    image = cv2.resize(image, (new_width, new_height))

    return image

def _crop_image(image: cv2.Mat, points: List[int]) -> cv2.Mat:
    y_min, y_max, x_min, x_max = points
    cropped_image = image[y_min:y_max, x_min:x_max]
    return cropped_image 