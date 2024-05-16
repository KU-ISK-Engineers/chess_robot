import os
import sys
import cv2
import concurrent.futures

def load_labels(labels_path):
    """Load the labels from a file."""
    with open(labels_path, 'r') as file:
        labels = file.read().strip().split('\n')
    return labels

def process_image(filename, input_dir, output_dir, labels):
    image_path = os.path.join(input_dir, filename)
    annotation_path = os.path.join(input_dir, os.path.splitext(filename)[0] + '.txt')
    
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image {image_path}")
        return
    
    height, width = image.shape[:2]

    # Check if the annotation file exists
    if not os.path.exists(annotation_path):
        print(f"Annotation file for {filename} not found.")
        return

    # Read the annotation file
    with open(annotation_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 5:
                class_id, x_center, y_center, bbox_width, bbox_height = map(float, parts)
                x_center *= width
                y_center *= height
                bbox_width *= width
                bbox_height *= height

                x_min = int(x_center - bbox_width / 2)
                y_min = int(y_center - bbox_height / 2)
                x_max = int(x_center + bbox_width / 2)
                y_max = int(y_center + bbox_height / 2)

                # Draw the bounding box
                cv2.rectangle(image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                label = labels[int(class_id)] if int(class_id) < len(labels) else f"Class {int(class_id)}"
                cv2.putText(image, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Save the annotated image to the output directory
    output_image_path = os.path.join(output_dir, filename)
    cv2.imwrite(output_image_path, image)
    print(f"Annotated image saved to {output_image_path}")

def draw_bounding_boxes(input_dir, output_dir, labels_path):
    # Load the labels
    labels = load_labels(labels_path)
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Collect all image filenames
    image_filenames = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'))]

    # Use concurrent processing to handle multiple images simultaneously
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_image, filename, input_dir, output_dir, labels) for filename in image_filenames]
        for future in concurrent.futures.as_completed(futures):
            future.result()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python draw_bounding_boxes.py <input_directory> <output_directory> <labels_file>")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    labels_file = sys.argv[3]

    if not os.path.isdir(input_directory):
        print(f"Error: Input directory {input_directory} does not exist.")
        sys.exit(1)

    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    if not os.path.isfile(labels_file):
        print(f"Error: Labels file {labels_file} does not exist.")
        sys.exit(1)

    draw_bounding_boxes(input_directory, output_directory, labels_file)
