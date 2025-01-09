from typing import Optional
import logging
import time

import cv2
from pypylon import pylon
import chess
from ultralytics import YOLO
import numpy as np

from src.core.board import PhysicalBoard, BoardCapture, are_boards_equal
from src.detection.aruco import detect_aruco_area
from src.detection.model import grayscale_to_board

logger = logging.getLogger(__name__)

HUMAN_PERSPECTIVE = 1
ROBOT_PERSPECTIVE = 0


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
    except Exception as e:
        logger.error(f"Failed to initialize camera: {e}")
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
    Capturing assumes a stable perspective, where the player or robot remains in the same position.

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
        internal_perspective (bool): `HUMAN_PERSPECTIVE` if top of captured image is the player's side, `ROBOT_PERSPECTIVE` for the robot's side.
    """

    def __init__(
        self,
        model: YOLO,
        camera: Optional[pylon.InstantCamera] = None,
        internal_perspective: int = ROBOT_PERSPECTIVE,
        timeout: int = 5000,
        capture_delay: float = 0.3,
        conf_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        max_piece_offset: float = 0.4,
    ) -> None:
        """
        Initializes CameraBoardDetection with model, camera, and settings.

        Args:
            model (YOLO): YOLO model for detecting chessboard elements.
            camera (Optional[pylon.InstantCamera]): Camera instance; defaults to None for automatic setup.
            internal_perspective (bool): `HUMAN_PERSPECTIVE` for player's side at the bottom, `ROBOT_PERSPECTIVE` for robot side at the bottom.
            timeout (int): Image capture timeout in milliseconds. Defaults to 5000.
            capture_delay (float): Delay between captures in seconds. Defaults to 0.3.
            conf_threshold (float): Confidence threshold for detection. Defaults to 0.5.
            iou_threshold (float): IoU threshold for non-maximum suppression. Defaults to 0.45.
            max_piece_offset (float): Maximum offset from square center for valid mapping. Defaults to 0.4.

        Raises:
            RuntimeError: If camera initialization fails.
        """
        self.camera = camera or default_camera_setup()
        if self.camera is None:
            raise RuntimeError("Camera initialization failed.")
        self.timeout = timeout
        self.capture_delay = capture_delay
        self.model = model
        self.area = None
        self.board = None
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.max_piece_offset = max_piece_offset
        self.internal_perspective = internal_perspective

    def capture_image(self) -> Optional[np.ndarray]:
        """
        Captures an image, converts it to grayscale, and crops to board area if detected.

        Retries capturing until successful. Logs an error if capturing fails.

        Returns:
            Optional[np.ndarray]: Cropped grayscale image, or None if capture fails.
        """
        if not self.camera.IsGrabbing():
            logger.error("Camera is not grabbing images.")
            return None

        while True:
            grab_result = self.camera.RetrieveResult(
                self.timeout, pylon.TimeoutHandling_Return
            )
            if not grab_result.GrabSucceeded():
                logger.warning("Failed to grab image from camera.")
                continue

            image = preprocess_image(grab_result.Array)
            cropped_image = self._crop_image(image)

            if cropped_image is not None:
                return cropped_image
            logger.warning("No board detected; retrying.")
            time.sleep(1)

    def capture_board(
        self, human_perspective: chess.Color = chess.WHITE
    ) -> Optional[PhysicalBoard]:
        """
        Captures and verifies the state of the chessboard to ensure consistency.

        Captures an image, converts it to a board state, and verifies consistency by capturing
        a second image after a delay if necessary.

        Args:
            human_perspective (chess.Color): Color perspective (chess.WHITE or chess.BLACK) for board orientation.

        Returns:
            Optional[PhysicalBoard]: Detected and verified chessboard state, or None if capture fails.
        """
        image = self.capture_image()
        if image is None:
            return None

        perspective = (
            human_perspective
            if self.internal_perspective == HUMAN_PERSPECTIVE
            else not human_perspective
        )

        board = grayscale_to_board(
            image,
            perspective,
            self.model,
            self.conf_threshold,
            self.iou_threshold,
            self.max_piece_offset,
        )

        # Verification by second capture
        time.sleep(self.capture_delay)
        second_image = self.capture_image()
        if second_image is not None:
            second_board = grayscale_to_board(
                second_image,
                perspective,
                self.model,
                self.conf_threshold,
                self.iou_threshold,
                self.max_piece_offset,
            )
            if are_boards_equal(board.chess_board, second_board.chess_board):
                return board

        logger.info("Inconsistent board states detected; capture failed.")
        return None

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
