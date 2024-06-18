import cv2
from typing import Tuple, Optional
from pypylon import pylon
import chess
from ultralytics import YOLO
import numpy as np
import time
from .aruco import detect_aruco_area
from .detection import image_to_board, visualise_chessboard
from .board import BoardWithOffsets

class CameraDetection:
    def __init__(self, camera: pylon.InstantCamera, model: YOLO, timeout: int = 5000) -> None:
        self.camera = camera
        self.timeout = timeout
        self.model = model
        self.area = None
        self.board = None

    def capture_image(self) -> cv2.Mat:
        if not self.camera.IsGrabbing():
            raise RuntimeError("Camera is not grabbing images.")
        
        cropped_image = None
        
        while cropped_image is None:
            grab_result = self.camera.RetrieveResult(self.timeout, pylon.TimeoutHandling_ThrowException)
            if not grab_result.GrabSucceeded():
                raise RuntimeError("Failed to grab image from camera.")

            image = grab_result.Array
            image = self._preprocess_image(image)
            cropped_image = self._crop_image(image)

            if cropped_image is None:
                print('Waiting for image to be cropped')
                time.sleep(1)

        self.image = cropped_image
        return self.image
    
    def capture_board(self, perspective: chess.Color = chess.WHITE) -> BoardWithOffsets:
        image = self.capture_image()
        board = image_to_board(image, self.model, perspective)
        return board
    
    def _preprocess_image(self, image: cv2.Mat) -> cv2.Mat:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def _crop_image(self, image: cv2.Mat) -> Tuple[Optional[cv2.Mat]]:
        rect = detect_aruco_area(image)

        if rect is not None:
            self.area = rect

        if self.area is None:
            return None
        
        image = crop_image_by_area(image, self.area)
        return image

            
def crop_image_by_area(image: cv2.Mat, area) -> cv2.Mat:
    (tl, tr, bl, br) = area
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

    M = cv2.getPerspectiveTransform(area, dst)
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

    while True:
        #image = detection.capture_image()
        board = detection.capture_board(perspective=chess.BLACK)
        visualise_chessboard(board)

        # cv2.namedWindow('image', cv2.WINDOW_NORMAL)
        # cv2.imshow('image', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == "__main__":
    main()
