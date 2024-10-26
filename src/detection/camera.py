from typing import Optional
import logging
import time

import cv2
from pypylon import pylon
import chess
from ultralytics import YOLO
import numpy as np

from src.core.board import PhysicalBoard, BoardDetection, boards_are_equal
from src.detection.aruco import detect_aruco_area
from src.detection.model import greyscale_to_board

logger = logging.getLogger(__name__)

def default_camera_setup() -> pylon.InstantCamera:
    """Configures and initializes a camera with default settings for capturing images.

    This setup includes setting the frame rate, exposure mode, acquisition mode, and pixel format
    for the camera.

    Returns:
        pylon.InstantCamera: The initialized and configured camera instance.
    """
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate.SetValue(5)
    camera.ExposureAuto.SetValue("Continuous")
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("RGB8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    return camera


def crop_image_by_area(image: np.ndarray, area) -> np.ndarray:
    """Crops an image based on specified area coordinates, such as those detected by ArUco markers.

    This function calculates the optimal width and height for cropping, then performs
    a perspective transform to isolate the specified area.

    Args:
        image (np.ndarray): The image to be cropped.
        area: A set of four coordinates defining the top-left, top-right, bottom-left,
              and bottom-right corners of the area to crop.

    Returns:
        np.ndarray: The cropped image focused on the specified area.
    """
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

    m = cv2.getPerspectiveTransform(area, dst)
    warped = cv2.warpPerspective(image, m, (max_width, max_height))
    return warped


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Converts an image to grayscale, preparing it for detection and processing.

    Args:
        image (np.ndarray): The input color image in BGR format.

    Returns:
        np.ndarray: The grayscale version of the image.
    """
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


class CameraBoardDetection(BoardDetection):
    """Detects and captures the chessboard's state from camera images, using a YOLO model for detection.

    This class utilizes the YOLO model to detect elements on a chessboard. The camera can be either
    provided or initialized with default settings.

    Attributes:
        model (YOLO): The YOLO model used for detecting board elements.
        camera (pylon.InstantCamera): The camera used for capturing board images.
        timeout (int): The timeout duration (in milliseconds) for image retrieval from the camera.
    """

    def __init__(
        self,
        model: YOLO,
        camera: Optional[pylon.InstantCamera] = None,
        timeout: int = 5000,
    ) -> None:
        """Initializes CameraBoardDetection with a YOLO model, optional camera, and timeout setting.

        Args:
            model (YOLO): The YOLO model for detecting elements on the chessboard.
            camera (Optional[pylon.InstantCamera]): Optional camera instance; if None, defaults are set up.
            timeout (int): Timeout in milliseconds for image capture. Defaults to 5000 ms.
        """
        self.camera = camera or default_camera_setup()
        self.timeout = timeout
        self.model = model
        self.area = None
        self.board = None

    def capture_image(self) -> Optional[np.ndarray]:
        """Captures an image from the camera and crops it to the board area if detected.

        This function repeatedly attempts to capture an image until successful. Once an image is captured,
        it is converted to grayscale and then cropped to focus on the chessboard.

        Returns:
            Optional[np.ndarray]: The cropped grayscale image, or None if capturing failed.
        """
        if not self.camera.IsGrabbing():
            logger.warning("Camera is not grabbing images")
            return None

        cropped_image = None
        while cropped_image is None:
            grab_result = self.camera.RetrieveResult(
                self.timeout, pylon.TimeoutHandling_Return
            )
            if not grab_result.GrabSucceeded():
                logger.warning("Failed to grab image from camera.")
                continue

            image = grab_result.Array
            image = preprocess_image(image)
            cropped_image = self._crop_image(image)

            if cropped_image is None:
                logger.info("Waiting for image to be cropped")
                time.sleep(1)

        return cropped_image

    def capture_board(
        self, perspective: chess.Color = chess.WHITE
    ) -> Optional[PhysicalBoard]:
        """Captures and verifies the state of the chessboard, ensuring consistent results.

        This function captures two consecutive images and converts them to board states using the YOLO model.
        If both states are consistent, the board perspective is set and returned.

        Args:
            perspective (chess.Color): The color perspective (chess.WHITE or chess.BLACK) used to adjust the board orientation.

        Returns:
            Optional[PhysicalBoard]: The detected and verified chessboard state, or None if detection failed.
        """
        image1 = self.capture_image()
        if not image1:
            return None

        time.sleep(0.3)
        image2 = self.capture_image()
        if not image2:
            return None

        board1 = greyscale_to_board(image1, self.model, flip=perspective == chess.WHITE)
        board2 = greyscale_to_board(image2, self.model, flip=perspective == chess.WHITE)

        if boards_are_equal(board1.chess_board, board2.chess_board):
            board2.perspective = perspective
            return board2

    def _crop_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Crops the image to the detected board area based on ArUco markers.

        This function detects an area within the image using ArUco markers and performs a perspective transform to
        crop the image around the board. The area is cached for use in future captures if found.

        Args:
            image (np.ndarray): The grayscale image to be cropped.

        Returns:
            Optional[np.ndarray]: The cropped board image, or None if no area was detected.
        """
        area = detect_aruco_area(image)

        if area is not None:
            self.area = area

        if self.area is None:
            return None

        image = crop_image_by_area(image, self.area)
        return image
