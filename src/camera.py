import cv2
from typing import List, Tuple
from pypylon import pylon
import chess
from ultralytics import YOLO
from .detection import image_to_board
from .aruco import 
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
            
def crop_image_by_points(image, rect):
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
