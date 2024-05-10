import cv2
import numpy as np
import sys

def load_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Image not found at {image_path}")
    return image

def preprocess_image(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def slice_into_squares(image, rows=8, cols=8):
    h, w = image.shape[0], image.shape[1]
    square_height = h // rows
    square_width = w // cols
    squares = []
    for row in range(rows):
        for col in range(cols):
            square = image[row * square_height:(row + 1) * square_height, col * square_width:(col + 1) * square_width]
            squares.append((square, (row, col)))
    return squares

def compare_squares(squares1, squares2, threshold=255*75):
    changes = {'taken': [], 'put': [], 'unchanged': []}
    for (sq1, pos1), (sq2, pos2) in zip(squares1, squares2):
        diff = cv2.absdiff(sq1, sq2)
        if np.sum(diff) > threshold:
            if np.mean(sq1) > np.mean(sq2):
                changes['taken'].append(pos1)
            else:
                changes['put'].append(pos1)
        else:
            changes['unchanged'].append(pos1)
    return changes

def visualize_changes(image, changes, square_height, square_width):
    for row, col in changes['taken']:
        top_left = (col * square_width, row * square_height)
        bottom_right = ((col + 1) * square_width, (row + 1) * square_height)
        cv2.rectangle(image, top_left, bottom_right, (0, 0, 255), 2)  # Red color for removed pieces
    for row, col in changes['put']:
        top_left = (col * square_width, row * square_height)
        bottom_right = ((col + 1) * square_width, (row + 1) * square_height)
        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)  # Green color for added pieces
    for row, col in changes['unchanged']:
        top_left = (col * square_width, row * square_height)
        bottom_right = ((col + 1) * square_width, (row + 1) * square_height)
        cv2.rectangle(image, top_left, bottom_right, (128, 128, 128), 2)  # Gray color for unchanged pieces
    return image

def concatenate_images(images, axis=1):
    return cv2.hconcat(images) if axis == 1 else cv2.vconcat(images)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare.py path_to_first_image.png path_to_second_image.png")
        sys.exit(1)

    image1 = load_image(sys.argv[1])
    image2 = load_image(sys.argv[2])
    gray_image1 = preprocess_image(image1)
    gray_image2 = preprocess_image(image2)

    # Calculate square size from the first image
    rows, cols = 8, 8
    square_height = gray_image1.shape[0] // rows
    square_width = gray_image1.shape[1] // cols

    squares1 = slice_into_squares(gray_image1)
    squares2 = slice_into_squares(gray_image2)

    changes = compare_squares(squares1, squares2)

    result_image = visualize_changes(image1.copy(), changes, square_height, square_width)

    combined_image = concatenate_images([image1, image2, result_image])
    cv2.imshow('Combined Visualization', combined_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imwrite('combined_result_image.png', combined_image)
