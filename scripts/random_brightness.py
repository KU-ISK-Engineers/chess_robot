import cv2
import albumentations as A
import numpy as np
import glob
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_bboxes(file_path):
    bboxes = []
    class_labels = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            values = list(map(float, line.split()))
            class_labels.append(int(values[0]))
            bboxes.append(values[1:])
    return bboxes, class_labels

def save_bboxes(file_path, bboxes, class_labels):
    with open(file_path, 'w') as f:
        for cls, bbox in zip(class_labels, bboxes):
            f.write(f"{cls} " + " ".join(map(str, bbox)) + "\n")

def augment_image(image, bboxes, class_labels, transform):
    # Convert grayscale image to 3-channel image
    image_3ch = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    augmented = transform(image=image_3ch)
    # Convert back to grayscale
    augmented_image = cv2.cvtColor(augmented['image'], cv2.COLOR_BGR2GRAY)
    return augmented_image, bboxes  # Returning original bboxes as they are not modified

def process_image(img_path, output_directory, brightness_probability):
    base_name = os.path.splitext(os.path.basename(img_path))[0]
    bbox_path = os.path.join(os.path.dirname(img_path), f"{base_name}.txt")
    
    image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    
    if os.path.exists(bbox_path):
        bboxes, class_labels = load_bboxes(bbox_path)
    else:
        bboxes, class_labels = [], []

    # Precompile the transformation
    transform = A.Compose([
        A.RandomBrightnessContrast(brightness_limit=(-0.1, 0.2), contrast_limit=(-0.1, 0.2), p=brightness_probability)
    ])
    
    augmented_image, augmented_bboxes = augment_image(image, bboxes, class_labels, transform)
    
    output_img_path = os.path.join(output_directory, f"{base_name}_brightness.png")
    output_bbox_path = os.path.join(output_directory, f"{base_name}_brightness.txt")
    
    cv2.imwrite(output_img_path, augmented_image)
    save_bboxes(output_bbox_path, augmented_bboxes, class_labels)
    
    return img_path

def main(input_directory, output_directory, brightness_probability):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    image_paths = glob.glob(os.path.join(input_directory, '*.png'))
    
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_image, img_path, output_directory, brightness_probability) for img_path in image_paths]
        for future in as_completed(futures):
            img_path = future.result()
            print(f"Processed {img_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python script.py <input_directory> <output_directory> <brightness_probability>")
        sys.exit(1)
    
    input_directory = sys.argv[1]
    output_directory = sys.argv[2]
    brightness_probability = float(sys.argv[3])
    
    main(input_directory, output_directory, brightness_probability)
