import os
import math
import sys
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed

def rotate_save(image_path, annotations, output_folder, angle):
    print(f"Rotating {image_path}: {angle} deg")

    try:
        # Load the image
        image = Image.open(image_path).convert("L")
        image_width, image_height = image.size

        # Create a new image that is the same size as the original
        overlaid_image = image.copy()

        for annotation in annotations:
            # Get annotation coordinates
            label, center_x_norm, center_y_norm, width_norm, height_norm = annotation

            # Convert normalized coordinates to pixel values
            center_x = int(float(center_x_norm) * image_width)
            center_y = int(float(center_y_norm) * image_height)
            width = int(float(width_norm) * image_width)
            height = int(float(height_norm) * image_height)

            # Calculate the edge of the square that will contain the annotation box
            square_edge = int(math.sqrt(width**2 + height**2))

            # Calculate bounding box coordinates for the twice square_edge size square
            x1 = max(center_x - square_edge, 0)
            y1 = max(center_y - square_edge, 0)
            x2 = min(center_x + square_edge, image_width)
            y2 = min(center_y + square_edge, image_height)

            # Crop the image to the twice square_edge size square
            large_cropped_image = image.crop((x1, y1, x2, y2))
            rotated_image = large_cropped_image.rotate(angle, expand=True)

            # Calculate the mean of annotation width and height
            mean_edge = int((width + height) / 2)

            # Calculate the bounding box coordinates for the final mean_edge size square
            new_center_x, new_center_y = rotated_image.size[0] // 2, rotated_image.size[1] // 2
            final_x1 = new_center_x - mean_edge // 2
            final_y1 = new_center_y - mean_edge // 2
            final_x2 = new_center_x + mean_edge // 2
            final_y2 = new_center_y + mean_edge // 2

            # Crop the rotated image to the final mean_edge size square
            final_cropped_image = rotated_image.crop((final_x1, final_y1, final_x2, final_y2))

            # Create a mask for transparency
            mask = Image.new("L", final_cropped_image.size, 255)

            # Calculate position to paste the final cropped image so its center matches the annotation center
            paste_x = center_x - mean_edge // 2
            paste_y = center_y - mean_edge // 2

            # Ensure the paste coordinates are within bounds
            paste_x = max(0, min(paste_x, image_width - final_cropped_image.size[0]))
            paste_y = max(0, min(paste_y, image_height - final_cropped_image.size[1]))

            # Paste the final cropped image on the original image using the mask
            overlaid_image.paste(final_cropped_image, (paste_x, paste_y), mask)

        # Save the overlaid image
        rotated_image_path = os.path.join(output_folder, os.path.splitext(os.path.basename(image_path))[0] + f'_overlaid_{angle}.png')
        overlaid_image.save(rotated_image_path)

        # Write updated annotation to a text file for the overlaid image
        rotated_annotation_txt_path = os.path.splitext(rotated_image_path)[0] + '.txt'
        with open(rotated_annotation_txt_path, 'w') as f:
            for annotation in annotations:
                label, center_x_norm, center_y_norm, width_norm, height_norm = annotation
                center_x_new = float(center_x_norm)
                center_y_new = float(center_y_norm)
                width_new = mean_edge / image_width
                height_new = width_new
                f.write(f"{label} {center_x_new:.6f} {center_y_new:.6f} {width_new:.6f} {height_new:.6f}\n")

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def process_file(executor, input_folder, output_folder, angle_step, filename):
    image_path = os.path.join(input_folder, filename)
    annotation_path = os.path.join(input_folder, os.path.splitext(filename)[0] + '.txt')
    futures = []

    if os.path.exists(annotation_path):
        with open(annotation_path, 'r') as f:
            annotations = [tuple(line.strip().split()) for line in f]

        for angle in range(0, 360, angle_step):
            future = executor.submit(rotate_save, image_path, annotations, output_folder, angle)
            futures.append(future)
    else:
        print(f"Annotation file not found for {filename}")

    return futures

def process_folder(input_folder, output_folder, angle_step):
    os.makedirs(output_folder, exist_ok=True)

    files_to_process = [filename for filename in os.listdir(input_folder) if filename.lower().endswith(('.png', '.jpg', '.jpeg'))]

    with ThreadPoolExecutor(max_workers=os.cpu_count() * 2) as executor:
        all_futures = []

        for filename in files_to_process:
            futures = process_file(executor, input_folder, output_folder, angle_step, filename)
            all_futures.extend(futures)

        for future in as_completed(all_futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error processing file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python rotations_large.py <input_directory> <output_directory> <angle>")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    angle_step = int(sys.argv[3])

    process_folder(input_directory, output_directory, angle_step)
