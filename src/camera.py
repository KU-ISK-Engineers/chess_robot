import cv2
from typing import Optional
from pypylon import pylon
import chess
from ultralytics import YOLO
import numpy as np
import time
from .aruco import detect_aruco_area
from .board import PhysicalBoard, BoardDetection, boards_are_equal
from .image import crop_image_by_area, greyscale_to_board
import logging

logger = logging.getLogger(__name__)


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


def _preprocess_image(image: np.ndarray) -> np.ndarray:
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


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

    def capture_image(self) -> Optional[np.ndarray]:
        if not self.camera.IsGrabbing():
            logger.warning("Camera is not grabbing images")
            return 
        
        cropped_image = None
        
        while cropped_image is None:
            grab_result = self.camera.RetrieveResult(self.timeout, pylon.TimeoutHandling_Return)
            if not grab_result.GrabSucceeded():
                logger.warning("Failed to grab image from camera.")
                continue

            image = grab_result.Array
            image = _preprocess_image(image)
            cropped_image = self._crop_image(image)

            if cropped_image is None:
                logger.info('Waiting for image to be cropped')
                time.sleep(1)

        return cropped_image

    def capture_board(self, perspective: chess.Color = chess.WHITE) -> Optional[PhysicalBoard]:
        image1 = self.capture_image()
        if not image1:
            return

        time.sleep(0.3)
        image2 = self.capture_image()
        if not image2:
            return

        board1 = greyscale_to_board(image1, self.model, flip=perspective == chess.WHITE)
        board2 = greyscale_to_board(image2, self.model, flip=perspective == chess.WHITE)

        if boards_are_equal(board1.chess_board, board2.chess_board):
            board2.perspective = perspective
            return board2

    def _crop_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        area = detect_aruco_area(image)

        if area is not None:
            self.area = area

        if self.area is None:
            return None
        
        image = crop_image_by_area(image, self.area)
        return image

