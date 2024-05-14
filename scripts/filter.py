import cv2
import numpy as np
import sys

def filter_color(image_path):
    # Load the image in BGR color space
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Image could not be loaded. Please check the file path.")
        return
    
    # Define the target color range
    target_color = np.array([220, 220, 220])
    tolerance = np.array([30, 30, 30])

    # Calculate lower and upper bounds for the color range
    lower_bound = target_color - tolerance
    upper_bound = target_color + tolerance

    # Convert lower and upper bounds to correct order for BGR
    lower_bound = np.clip(lower_bound, 0, 255)
    upper_bound = np.clip(upper_bound, 0, 255)

    # Create a mask that identifies pixels within the specified range
    mask = cv2.inRange(img, lower_bound, upper_bound)

    # Create an output image that displays only the colors in the range, setting others to black
    output_img = cv2.bitwise_and(img, img, mask=mask)

    # Display the original and the filtered image

    cv2.imshow('Original Image', cv2.resize(img, (800,800), interpolation=cv2.INTER_LINEAR))
    cv2.imshow('Filtered Image', cv2.resize(output_img, (800,800), interpolation=cv2.INTER_LINEAR))
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if len(sys.argv) != 2:
    print("Usage: python filter.py path_to_image")
    sys.exit(1)

image_path = sys.argv[1]
filter_color(image_path)

# To run the function, you need to pass the path to your image file.
# Example: filter_color('path_to_your_image.jpg')
