
import cv2
import numpy as np
import matplotlib.pyplot as plt
import argparse

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
    
    if ids is not None:
        # Draw detected markers
        cv2.aruco.drawDetectedMarkers(image, corners, ids)
        
        # Display the image with markers
        plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.title('Detected ArUco Markers')
        plt.show()
    else:
        print("No ArUco markers detected.")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Detect ArUco markers in an image.")
    parser.add_argument("image_path", help="Path to the input image.")
    args = parser.parse_args()

    # Detect ArUco markers
    detect_aruco_markers(args.image_path)

if __name__ == "__main__":
    main()
