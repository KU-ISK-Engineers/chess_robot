import cv2
import numpy as np
from sklearn.cluster import KMeans
import sys

def analyze_image(image_path):
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Image could not be loaded. Please check the file path.")
        return
    
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Resize image to decrease processing time
    # img = cv2.resize(img, (400, 400), interpolation=cv2.INTER_AREA)

    # Reshape the image to be a list of pixels
    img_pixels = img.reshape(-1, 3)

    # Quantize the colors (reduce to 10 colors for example)
    num_colors = 10
    kmeans = KMeans(n_clusters=num_colors)
    labels = kmeans.fit_predict(img_pixels)
    centers = kmeans.cluster_centers_

    # Count labels to find most popular
    label_counts = np.bincount(labels)
    total_pixels = len(labels)

    # Display colors that occupy more than 20%
    for i, count in enumerate(label_counts):
        percentage = (count / total_pixels) * 100
        if percentage > 20:
            color = centers[i].astype(int)
            print(f"Color: {color}, Percentage: {percentage:.2f}%")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <image_path>")
    else:
        analyze_image(sys.argv[1])
