from typing import Optional
import logging
import time

import cv2
from pypylon import pylon
import chess
from ultralytics import YOLO
import numpy as np
from enum import Enum

from src.core.board import PhysicalBoard, BoardCapture, are_boards_equal
from src.detection.aruco import detect_aruco_area
from src.detection.model import grayscale_to_board

logger = logging.getLogger(__name__)


class Orientation(Enum):
    HUMAN_BOTTOM = 0
    ROBOT_BOTTOM = 1


def default_camera_setup() -> Optional[pylon.InstantCamera]:
    """
    Configures and initializes a camera with default settings for capturing images.

    The setup configures frame rate, exposure mode, acquisition mode, and pixel format.
    If initialization fails, logs an error and returns None.

    Returns:
        Optional[pylon.InstantCamera]: The initialized camera instance, or None if setup fails.
    """
    try:
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()
        camera.AcquisitionFrameRateEnable.SetValue(True)
        camera.AcquisitionFrameRate.SetValue(5)
        camera.ExposureAuto.SetValue("Continuous")
        camera.AcquisitionMode.SetValue("Continuous")
        camera.PixelFormat.SetValue("RGB8")
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        logger.info("Camera successfully initialized and started grabbing.")
        return camera
    except Exception:
        logger.exception("Failed to initialize camera!")
        return None


def crop_image_by_area(image: np.ndarray, area) -> np.ndarray:
    """
    Crops an image based on specified area coordinates detected by ArUco markers.

    Args:
        image (np.ndarray): The image to be cropped.
        area: Four corner points defining the region to crop.

    Returns:
        np.ndarray: The cropped image focused on the specified area.
    """

    def max_dimension(p1, p2, p3, p4):
        width = max(np.linalg.norm(p2 - p1), np.linalg.norm(p4 - p3))
        height = max(np.linalg.norm(p3 - p1), np.linalg.norm(p2 - p4))
        return int(width), int(height)

    max_width, max_height = max_dimension(*area)
    dst = np.array(
        [
            [0, 0],
            [max_width - 1, 0],
            [max_width - 1, max_height - 1],
            [0, max_height - 1],
        ],
        dtype="float32",
    )

    m = cv2.getPerspectiveTransform(area, dst)
    return cv2.warpPerspective(image, m, (max_width, max_height))


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Converts a color image to grayscale for processing and detection.

    Args:
        image (np.ndarray): The input color image in BGR format.

    Returns:
        np.ndarray: The grayscale version of the image.
    """
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


class CameraBoardCapture(BoardCapture):
    """
    Detects and captures the state of a chessboard from camera images using a YOLO model.

    Uses ArUco markers to detect the board area and YOLO to identify pieces.
    Capturing board assumes a constant physical orientation of the camera, where the player or robot remains on the same side.

    Attributes:
        model (YOLO): YOLO model for piece detection.
        camera (pylon.InstantCamera): Camera for capturing board images.
        timeout (int): Timeout for image retrieval (milliseconds).
        capture_delay (float): Delay between consecutive captures (seconds).
        area (Optional[np.ndarray]): Cached area for cropping based on ArUco markers.
        board (Optional[PhysicalBoard]): Current state of the chessboard.
        conf_threshold (float): Confidence threshold for detection.
        iou_threshold (float): IoU threshold for non-maximum suppression.
        max_piece_offset (float): Maximum offset distance from square center for valid piece mapping.
        physical_orientation (Orientation): `Orientation.HUMAN_BOTTOM` if bottom of the captured image is the player's side, `Orientation.ROBOT_BOTTOM` otherwise.
    """

    def __init__(
        self,
        model: YOLO,
        camera: pylon.InstantCamera,
        physical_orientation: Orientation = Orientation.HUMAN_BOTTOM,
        timeout: int = 5000,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        max_piece_offset: float = 0.9,
        visualize_board: bool = False,
    ) -> None:
        """
        Initializes CameraBoardDetection with model, camera, and settings.

        Args:
            model (YOLO): YOLO model for detecting chessboard elements.
            camera (Optional[pylon.InstantCamera]): Camera instance; defaults to None for automatic setup.
            physical_orientation (Orientation): `Orientation.HUMAN_BOTTOM` if bottom of the captured image is the player's side, `Orientation.ROBOT_BOTTOM` otherwise.
            timeout (int): Image capture timeout in milliseconds. Defaults to 5000.
            capture_delay (float): Delay between captures in seconds. Defaults to 0.3.
            conf_threshold (float): Confidence threshold for detection. Defaults to 0.5.
            iou_threshold (float): IoU threshold for non-maximum suppression. Defaults to 0.45.
            max_piece_offset (float): Maximum offset from square center for valid mapping. Defaults to 0.4.

        Raises:
            RuntimeError: If camera initialization fails.
        """
        self.camera = camera or default_camera_setup()
        self.timeout = timeout
        self.model = model
        self.area = None
        self.board = None
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.max_piece_offset = max_piece_offset
        self.physical_orientation = physical_orientation
        self.visualize_board = visualize_board

    def capture_image(self) -> Optional[np.ndarray]:
        """
        Captures an image, converts it to grayscale, and crops to board area if detected.

        Retries capturing until successful. Logs an error if capturing fails.

        Returns:
            Optional[np.ndarray]: Cropped grayscale image, or None if capture fails.
        """
        if not self.camera.IsGrabbing():
            logger.error("Camera is not grabbing images!")
            return None

        while True:
            grab_result = self.camera.RetrieveResult(
                self.timeout, pylon.TimeoutHandling_Return
            )
            if not grab_result.GrabSucceeded():
                logger.error("Failed to grab image from camera!")
                return None

            image = preprocess_image(grab_result.Array)
            cropped_image = self._crop_image(image)

            if cropped_image is not None:
                return cropped_image

            logger.warning("No board detected with aruco stickers; retrying.")
            time.sleep(1)

    def capture_board(self, human_color: chess.Color) -> Optional[PhysicalBoard]:
        """
        Captures and verifies the state of the chessboard to ensure consistency.

        Captures an image, converts it to a board state, and verifies consistency by capturing
        a second image after a delay if necessary.

        Args:
            human_perspective (chess.Color): Color perspective (chess.WHITE or chess.BLACK) for board orientation.

        Returns:
            Optional[PhysicalBoard]: Detected and verified chessboard state, or None if capture fails.
        """
        perspective = (
            human_color
            if self.physical_orientation == Orientation.HUMAN_BOTTOM
            else not human_color
        )

        while True:
            first_image = self.capture_image()
            if first_image is None:
                return None

            first_board = grayscale_to_board(
                first_image,
                perspective,
                self.model,
                self.conf_threshold,
                self.iou_threshold,
                self.max_piece_offset,
                visualize=self.visualize_board,
            )

            second_image = self.capture_image()
            if second_image is None:
                return None

            second_board = grayscale_to_board(
                second_image,
                perspective,
                self.model,
                self.conf_threshold,
                self.iou_threshold,
                self.max_piece_offset,
                visualize=self.visualize_board,
            )

            if are_boards_equal(first_board.chess_board, second_board.chess_board):
                return first_board

            logger.info("Inconsistent board states captured; retrying..")

    def _crop_image(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Crops the image to the board area using ArUco markers.

        Args:
            image (np.ndarray): Grayscale image to be cropped.

        Returns:
            Optional[np.ndarray]: Cropped board image, or None if no area is detected.
        """
        area = detect_aruco_area(image)
        if area is not None:
            self.area = area

        if self.area is None:
            logger.warning("No ArUco area detected.")
            return None
        return crop_image_by_area(image, self.area)

    def close(self):
        """Releases camera resources and stops image capture."""
        if self.camera and self.camera.IsGrabbing():
            self.camera.StopGrabbing()
            self.camera.Close()

    def __del__(self):
        """Ensures resources are released upon deletion."""
        self.close()
