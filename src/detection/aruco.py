from typing import Optional, Tuple
import numpy as np
import cv2

def centroid(rectangle: np.ndarray) -> Tuple[float, float]:
    """Calculates the centroid of a rectangle from four corner points.

    Args:
        rectangle (np.ndarray): A (4, 2) array representing the (x, y) coordinates of the rectangle's corners.

    Returns:
        Tuple[float, float]: The (x, y) coordinates of the centroid.
    """
    return tuple(np.mean(rectangle, axis=0))


def find_rectangles(pts: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Groups and sorts points into four rectangles in the order: top-left, top-right, bottom-left, bottom-right.

    This function assumes the points represent four rectangles' corners. It groups points into four sets of four,
    calculates centroids for each rectangle, and sorts them based on position to assign each rectangle a consistent
    location.

    Args:
        pts (np.ndarray): A flat (16, 2) array representing corners of four rectangles (four points per rectangle).

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]: The four rectangles' points, in order:
        top-left, top-right, bottom-left, bottom-right, with each rectangle represented by a (4, 2) array.

    Raises:
        ValueError: If fewer than 16 points are provided.
    """
    if len(pts) < 16:
        raise ValueError("Insufficient points to form four rectangles.")
    
    # Group points into four sets of four (assumes points are ordered correctly)
    grouped_rectangles = [pts[i:i + 4] for i in range(0, len(pts), 4)]
    centroids = [centroid(rect) for rect in grouped_rectangles]
    centroids_rectangles = list(zip(centroids, grouped_rectangles))

    # Sort rectangles into top and bottom pairs based on y-coordinate, then sort each pair by x-coordinate
    sorted_by_y = sorted(centroids_rectangles, key=lambda x: x[0][1])
    top_two, bottom_two = sorted_by_y[:2], sorted_by_y[2:]
    top_left, top_right = sorted(top_two, key=lambda x: x[0][0])
    bottom_left, bottom_right = sorted(bottom_two, key=lambda x: x[0][0])

    return top_left[1], top_right[1], bottom_left[1], bottom_right[1]


def sort_rectangle_points(points: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Sorts four points of a rectangle into a consistent order: top-left, top-right, bottom-right, bottom-left.

    This function calculates the angle of each point relative to the centroid, then sorts points
    by angle to achieve a consistent clockwise order starting from the top-left.

    Args:
        points (np.ndarray): A (4, 2) array representing the rectangle's corners.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]: The points ordered as (top-left, top-right, bottom-right, bottom-left).
    """
    centroid = np.mean(points, axis=0)
    angles = np.arctan2(points[:, 1] - centroid[1], points[:, 0] - centroid[0])
    sorted_points = points[np.argsort(angles)]
    return tuple(sorted_points)


def order_points(pts: np.ndarray) -> np.ndarray:
    """Orders points consistently for perspective transformation as: top-left, top-right, bottom-left, bottom-right.

    This function groups points into four rectangles, then sorts and arranges the points to form an ordered 
    list that defines a consistent area for perspective transformation.

    Args:
        pts (np.ndarray): A flat (16, 2) array representing corners of multiple rectangles.

    Returns:
        np.ndarray: A (4, 2) array of points ordered as top-left, top-right, bottom-left, bottom-right.
    """
    top_left_rect, top_right_rect, bottom_left_rect, bottom_right_rect = find_rectangles(pts)

    # Sort points within each rectangle to maintain a consistent order
    top_left_sorted = sort_rectangle_points(top_left_rect)
    top_right_sorted = sort_rectangle_points(top_right_rect)
    bottom_left_sorted = sort_rectangle_points(bottom_left_rect)
    bottom_right_sorted = sort_rectangle_points(bottom_right_rect)

    # Create an array of ordered points for the transformation
    rect = np.zeros((4, 2), dtype="float32")

    rect[0] = top_left_sorted[2]  # Bottom-right corner
    rect[1] = top_right_sorted[3]  # Bottom-left corner
    rect[2] = bottom_right_sorted[0]  # Top-left corner
    rect[3] = bottom_left_sorted[1]  # Top-right corner

    return rect


def detect_aruco_area(image: np.ndarray) -> Optional[np.ndarray]:
    """Detects an area within an image using ArUco markers, returning four ordered points for perspective transformation.

    This function uses the ArUco dictionary and detector parameters to locate markers within an image. If four
    markers are found, it collects their corners, groups them, and arranges them into a consistent order.

    Args:
        image (np.ndarray): The input image in which to detect ArUco markers, typically a grayscale or color image.

    Returns:
        Optional[np.ndarray]: A (4, 2) array of four ordered points (top-left, top-right, bottom-left, bottom-right) representing
        the detected area, or None if fewer than four markers are detected.
    """
    # Initialize the dictionary and parameters for ArUco marker detection
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    aruco_params = cv2.aruco.DetectorParameters()

    # Detect markers within the image
    corners, ids, _ = cv2.aruco.detectMarkers(image, aruco_dict, parameters=aruco_params)
    
    # Ensure that exactly four markers are detected
    if ids is None or len(ids) != 4:
        return None

    # Collect all corner points of the detected markers
    all_points = np.concatenate(corners).reshape(-1, 2)
    # Order points to define the area
    return order_points(all_points)
