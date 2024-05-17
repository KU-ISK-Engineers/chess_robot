import cv2
import numpy as np

def preprocess_image(image_path):
    # Load image
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    return image

def find_black_gray_squares(gray):
    # Define grayscale ranges for black and gray
    lower_black = 0
    upper_black = 50

    lower_gray = 50
    upper_gray = 500

    # Create mask for black in the grayscale image
    mask_black = cv2.inRange(gray, lower_black, upper_black)
    
    # Create mask for gray in the grayscale image
    mask_gray = cv2.inRange(gray, lower_gray, upper_gray)

    # Combine masks
    combined_mask = cv2.bitwise_or(mask_black, mask_gray)

    # Find contours
    contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def filter_and_draw_squares(image, contours):
    squares = []
    for contour in contours:
        # Get the bounding box for each contour
        x, y, w, h = cv2.boundingRect(contour)
        
        # Filter out too small or too large boxes
        if 200 < w < 400 and 200 < h < 400:  # Adjust size range based on your image resolution
            squares.append((x, y, w, h))
            # Draw rectangle around detected square
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Display the image with detected squares
    cv2.imshow('Detected Squares', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return squares

if __name__ == "__main__":
    image_path = 'training/cropped_grayscale.png'  # Replace with your image path

    # Preprocess the image
    gray = preprocess_image(image_path)

    # Find black and gray squares
    contours = find_black_gray_squares(gray)

    # Filter and draw detected squares
    detected_squares = filter_and_draw_squares(gray, contours)

    # Output detected squares
    for i, (x, y, w, h) in enumerate(detected_squares):
        print(f"Square {i + 1}: x={x}, y={y}, width={w}, height={h}")
