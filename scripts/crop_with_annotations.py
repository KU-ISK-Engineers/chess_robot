import cv2
import os
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

def crop_image(image, points):
    y_min, y_max, x_min, x_max = points
    cropped_image = image[y_min:y_max, x_min:x_max]
    return cropped_image

def read_annotations(annotation_path):
    with open(annotation_path, 'r') as file:
        annotations = [line.strip().split() for line in file]
    return annotations

def update_annotations(annotations, points, original_size, cropped_size):
    y_min, y_max, x_min, x_max = points
    original_height, original_width = original_size
    cropped_height, cropped_width = cropped_size

    updated_annotations = []
    for annotation in annotations:
        class_id, x_center, y_center, width, height = map(float, annotation)
        x_center = x_center * original_width
        y_center = y_center * original_height
        width = width * original_width
        height = height * original_height

        # Adjust for cropping
        x_center -= x_min
        y_center -= y_min

        # Normalize to new image size
        x_center /= cropped_width
        y_center /= cropped_height
        width /= cropped_width
        height /= cropped_height

        updated_annotations.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    
    return updated_annotations

def save_annotations(annotation_path, updated_annotations):
    with open(annotation_path, 'w') as file:
        for annotation in updated_annotations:
            file.write(annotation + '\n')
    print("Updated annotations saved to", annotation_path)

def process_directory(image_directory, points_file, output_directory):
    points = read_points(points_file)

    # Ensure the output directory exists
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    for filename in os.listdir(image_directory):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')):
            image_path = os.path.join(image_directory, filename)
            annotation_path = os.path.join(image_directory, os.path.splitext(filename)[0] + '.txt')

            print(f"Processing {image_path} with annotations {annotation_path}")

            image = cv2.imread(image_path, cv2.IMREAD_COLOR)
            if image is None:
                print(f"Error: Image not found at {image_path}. Skipping.")
                continue

            original_size = image.shape[:2]
            image = resize_image(image)
            cropped_image = crop_image(image, points)
            cropped_size = cropped_image.shape[:2]

            if os.path.exists(annotation_path):
                annotations = read_annotations(annotation_path)
                updated_annotations = update_annotations(annotations, points, original_size, cropped_size)
                output_annotations_path = os.path.join(output_directory, os.path.splitext(filename)[0] + '_cropped.txt')
                save_annotations(output_annotations_path, updated_annotations)

            output_image_path = os.path.join(output_directory, os.path.splitext(filename)[0] + '_cropped.png')
            cv2.imwrite(output_image_path, cropped_image)
            print(f"Cropped image saved to {output_image_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python crop.py path_to_image_directory path_to_points_file path_to_output_directory")
        sys.exit(1)

    image_directory = sys.argv[1]
    points_file = sys.argv[2]
    output_directory = sys.argv[3]
    process_directory(image_directory, points_file, output_directory)
