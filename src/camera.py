import cv2
from typing import Optional
from pypylon import pylon
import chess
from ultralytics import YOLO
import numpy as np
import time
from .aruco import detect_aruco_area
from .board import RealBoard, BoardDetection
from .image import crop_image_by_area, greyscale_to_board

def default_camera_setup():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate.SetValue(5)
    camera.ExposureAuto.SetValue('Continuous')
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("RGB8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    return camera

class CameraBoardDetection(BoardDetection):
    def __init__(self, model: YOLO, camera: Optional[pylon.InstantCamera] = None, timeout: int = 5000) -> None:
        if camera:
            self.camera = camera
        else:
            self.camera = default_camera_setup()

        self.timeout = timeout
        self.model = model
        self.area = None
        self.board = None

    def capture_image(self) -> np.ndarray:
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

        return cropped_image

    def capture_board(self, perspective: chess.Color = chess.WHITE) -> RealBoard:
        image = self.capture_image()
        board = greyscale_to_board(image, self.model, flip=perspective == chess.WHITE)
        board.perspective = perspective
        return board

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def _crop_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        area = detect_aruco_area(image)

        if area is not None:
            self.area = area

        if self.area is None:
            return None
        
        image = crop_image_by_area(image, self.area)
        return image

