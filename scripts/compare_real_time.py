from pypylon import pylon
import cv2
import numpy as np
import time
import sys

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

def compare_squares(squares1, squares2, threshold=255*200):
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

def visualize_changes(image, changes, square_height, square_width, margin=2):
    for change_type, positions in changes.items():
        if change_type == 'taken':
            color = (0, 0, 255)  # Red color for removed pieces
        elif change_type == 'put':
            color = (0, 255, 0)  # Green color for added pieces
        else:
            color = (128, 128, 128)  # Gray color for unchanged pieces

        for row, col in positions:
            top_left = (col * square_width + margin, row * square_height + margin)
            bottom_right = ((col + 1) * square_width - margin, (row + 1) * square_height - margin)
            cv2.rectangle(image, top_left, bottom_right, color, 2)

    return image


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

def main():
    if len(sys.argv) != 2:
        print("Usage: python compare_real_time.py path_to_points_file")
        sys.exit(1)

    points_file = sys.argv[1]

    points = read_points(points_file)
    # crop_image(image_path, points)

    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()
    camera.ExposureAuto.SetValue('Continuous')
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("Mono8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    last_image = None
    prev_result = None

    try:
        while True:
            if cv2.waitKey(1) != 13 and prev_result is not None:
                cv2.imshow('Real-Time Comparison', prev_result)
                continue

            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                # Process current image
                image = grab_result.Array
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                image = resize_image(image)
                image = crop_image(image, points)
                gray_image = preprocess_image(image)

                if last_image is not None:
                    # Process comparison
                    squares_current = slice_into_squares(gray_image)
                    squares_last = slice_into_squares(last_image)
                    changes = compare_squares(squares_last, squares_current)
                    result_image = visualize_changes(image.copy(), changes, gray_image.shape[0] // 8, gray_image.shape[1] // 8)
                    cv2.imshow('Real-Time Comparison', result_image)
                    prev_result = result_image
                last_image = gray_image

                grab_result.Release()

            else:
                print("Failed to grab frame.")
    finally:
        camera.StopGrabbing()
        camera.Close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
