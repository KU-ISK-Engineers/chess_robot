import cv2
import sys

def read_points(file_path):
    with open(file_path, 'r') as file:
        points = list(map(int, file.readline().strip().split()))
    if len(points) != 4:
        raise ValueError("Expected four integers in the file.")
    return points

def resize_image(image, width=800):
    height, original_width = image.shape[:2]
    new_height = int((width / original_width) * height)
    resized_image = cv2.resize(image, (width, new_height))
    return resized_image

def crop_image(image_path, points):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError("Image not found at the specified path.")

    # Resize the image to match the interactive selection script
    image = resize_image(image)

    y_min, y_max, x_min, x_max = points
    cropped_image = image[y_min:y_max, x_min:x_max]
    output_path = 'cropped.png'
    cv2.imwrite(output_path, cropped_image)
    print("Cropped image saved to", output_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python crop.py path_to_image path_to_points_file")
        sys.exit(1)

    image_path = sys.argv[1]
    points_file = sys.argv[2]
    points = read_points(points_file)
    crop_image(image_path, points)
