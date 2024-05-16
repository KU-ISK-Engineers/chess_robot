import cv2
import numpy as np
import imutils
import sys
from cvlib.object_detection import YOLO
import os

def detect_image(image_path, yolo):
    # Load the image from the file path
    original_img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if original_img is None:
        print("Error: Image could not be read. Check the file path.")
        return
    
    original_img = cv2.merge([original_img, original_img, original_img])

    # Resize image for consistent detection performance
    resized_img = imutils.resize(original_img, width=800)
    scale_width = resized_img.shape[1] / original_img.shape[1]
    scale_height = resized_img.shape[0] / original_img.shape[0]

    # Detect objects in the resized image
    bbox, label, conf = yolo.detect_objects(resized_img)

    print(bbox, label, conf)

    # Adjust bounding boxes to match the original image dimensions and add labels
    for box, lbl, cf in zip(bbox, label, conf):
        x, y, w, h = box
        x = int(x / scale_width)
        y = int(y / scale_height)
        w = int(w / scale_width)
        h = int(h / scale_height)
        
        # Draw rectangle for bounding box
        cv2.rectangle(original_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Prepare text with label and confidence level
        text = f"{lbl}: {cf*100:.2f}%"
        
        # Calculate text width & height to background rectangle
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        
        # Set rectangle background for text
        cv2.rectangle(original_img, (x, y - 20), (x + text_width, y), (0, 255, 0), -1)
        
        # Put text above rectangle
        cv2.putText(original_img, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

    # Display the resulting image
    cv2.imshow("Detected Objects", original_img)
    cv2.waitKey(0)  # Wait for a key press to exit
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Initialize YOLO object detector
    weights = "chess2-weights/yolov4-tiny-custom_best.weights"
    config = "yolov4-tiny-custom.cfg"
    labels = "obj.names"
    yolo = YOLO(weights, config, labels)

    if len(sys.argv) < 2:
        print("Usage: python script.py <image_directory>")
        sys.exit(1)

    for filename in os.listdir(sys.argv[1]):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')):
            image_path = os.path.join(sys.argv[1], filename)
            print(image_path)
            detect_image(image_path, yolo)

