import cv2
import sys
import os

def read_points(file_path):
    with open(file_path, 'r') as file:
        points = list(map(int, file.readline().strip().split()))
    if len(points) != 4:
        raise ValueError("Expected four integers in the file.")
    return points

def crop_image(image_path, points, output_dir):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Image not found at the specified path: {image_path}")

    y_min, y_max, x_min, x_max = points
    cropped_image = image[y_min:y_max, x_min:x_max]
    
    # Construct output path
    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, image_name)
    
    cv2.imwrite(output_path, cropped_image)
    print(f"Cropped image saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python crop_images.py path_to_input_folder path_to_points_file path_to_output_folder")
        sys.exit(1)

    input_folder = sys.argv[1]
    points_file = sys.argv[2]
    output_folder = sys.argv[3]

    # Read points from file
    points = read_points(points_file)

    # Create output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Process each image in the input folder
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(input_folder, filename)
            crop_image(image_path, points, output_folder)
