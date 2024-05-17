import cv2
import numpy as np
import svgwrite
import os

# Create a directory to store the markers
output_dir = 'aruco_markers'
os.makedirs(output_dir, exist_ok=True)

# Define the dictionary and parameters
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
marker_size = 200  # Size of the marker in pixels

def generate_aruco_marker(marker_id, marker_size, output_dir):
    marker_image = np.zeros((marker_size, marker_size), dtype=np.uint8)
    marker_image = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size)
    #marker_image = cv2.aruco.drawMarker(aruco_dict, marker_id, marker_size)

    # Convert to SVG format
    dwg = svgwrite.Drawing(f"{output_dir}/aruco_{marker_id}.svg", profile='tiny', size=(marker_size, marker_size))
    dwg.add(dwg.rect(insert=(0, 0), size=(marker_size, marker_size), fill='white'))
    for i in range(marker_size):
        for j in range(marker_size):
            if marker_image[i, j] == 0:
                dwg.add(dwg.rect(insert=(j, i), size=(1, 1), fill='black'))
    dwg.save()

# Generate markers for a 6x6 grid chessboard
grid_size = 6
for marker_id in range(grid_size * grid_size):
    generate_aruco_marker(marker_id, marker_size, output_dir)

print(f"ArUco markers have been generated in the '{output_dir}' directory.")
