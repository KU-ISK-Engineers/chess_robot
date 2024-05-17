import cv2
import numpy as np
import matplotlib.pyplot as plt
import argparse

def order_points(pts):
    # Initial sorting of points based on their x-coordinates
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    
    rect[0] = pts[np.argmin(s)]  # Top-left point
    rect[2] = pts[np.argmax(s)]  # Bottom-right point
    rect[1] = pts[np.argmin(diff)]  # Top-right point
    rect[3] = pts[np.argmax(diff)]  # Bottom-left point
    
    return rect

def detect_aruco_markers(image_path):
    # Load the image
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        return
    
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Define the dictionary and parameters for ArUco marker detection
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    aruco_params = cv2.aruco.DetectorParameters()

    # Detect markers in the image
    corners, ids, rejected = cv2.aruco.detectMarkers(gray_image, aruco_dict, parameters=aruco_params)
    
    if ids is not None and len(ids) == 4:
        # Draw detected markers
        cv2.aruco.drawDetectedMarkers(image, corners, ids)
        
        # Collect all corner points
        all_points = []
        for corner in corners:
            corner = corner.reshape((4, 2))
            for point in corner:
                all_points.append(point)

        # Order the points in a consistent way (top-left, top-right, bottom-right, bottom-left)
        all_points = np.array(all_points)
        ordered_points = order_points(all_points)

        # Draw the polygon inside the markers
        cv2.polylines(image, [np.int32(ordered_points)], isClosed=True, color=(0, 255, 0), thickness=2)
        
        # Optionally, fill the polygon
        # cv2.fillPoly(image, [np.int32(ordered_points)], color=(0, 255, 0, 50))  # RGBA for transparency

        # Display the image with markers
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.title('Detected ArUco Markers')
        plt.show()
    else:
        print("No ArUco markers detected or fewer/more than 4 markers detected.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Detect ArUco markers in an image.")
    parser.add_argument("image_path", help="Path to the input image.")
    args = parser.parse_args()

    # Detect ArUco markers
    detect_aruco_markers(args.image_path)

if __name__ == "__main__":
    main()
