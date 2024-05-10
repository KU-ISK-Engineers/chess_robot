from pypylon import pylon
import cv2
import argparse
import sys

OUT_F_POINTS = "points.txt"
OUT_F_CROPPED = "cropped.png"
OUT_F_ANNOTATED = "annotated.png"

# Global variables to store selected points
point1 = None
point2 = None
cropping = False

def click_and_crop(event, x, y, flags, param):
    global point1, point2, cropping

    if event == cv2.EVENT_LBUTTONDOWN:
        point1 = (x, y)
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        point2 = (x, y)
        cropping = False

        # Draw a rectangle around the selected region
        cv2.rectangle(image, point1, point2, (0, 255, 0), 2)
        cv2.imshow("image", image)

import cv2

def annotate_squares(image):
    # Define the number of rows and columns in the chessboard
    rows = 8
    cols = 8

    # Calculate the width and height of each square
    square_width = image.shape[1] // cols
    square_height = image.shape[0] // rows

    # Draw the annotations and squares on the image
    for row in range(rows):
        for col in range(cols):
            # Calculate the top-left and bottom-right corners of the current square
            top_left = (col * square_width, row * square_height)
            bottom_right = ((col + 1) * square_width, (row + 1) * square_height)

            # Draw the square using a rectangle
            cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)  # Green color, 2 px thickness

            # Calculate the center for placing text
            center_x = col * square_width + square_width // 2
            center_y = row * square_height + square_height // 2

            # Draw the coordinate annotation on the image
            cv2.putText(image, f"({row},{col})", (center_x - 20, center_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  # Red color

    return image

def main(args):
    if args.device is not None:
        camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        camera.Open()

        # Set auto exposure mode to continuous
        camera.ExposureAuto.SetValue('Continuous')
        
        # Set camera parameters
        camera.AcquisitionMode.SetValue("Continuous")
        
        # Set frame rate to 15 fps
        camera.AcquisitionFrameRateEnable.SetValue(True)
        
        # Set pixel format to RGB
        camera.PixelFormat.SetValue("RGB8")
        
        camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            # Convert the grabbed frame to OpenCV format
            image1 = grab_result.Array
            
            # Convert the RGB image to BGR
            image1 = cv2.cvtColor(image1, cv2.COLOR_RGB2BGR)
            
        
        
        grab_result.Release()
        frame = image1
        # if not ret:
        #     print("Failed to capture from the specified device.", file=sys.stderr)
        #     return
    elif args.image is not None:
        frame = cv2.imread(args.image)
    else:
        print("Please specify either --device or --image.")
        return

    # Readjust size
    height, width = frame.shape[:2]
    new_width = 800
    new_height = int((new_width / width) * height)
    frame = cv2.resize(frame, (new_width, new_height))

    global image, point1, point2
    image = frame
    clone = image.copy()

    cv2.namedWindow("image")
    cv2.setMouseCallback("image", click_and_crop)

    while True:
        cv2.imshow("image", image)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("r"):
            image = clone.copy()
            point1 = None
            point2 = None
        elif key == ord("c"):
            if point1 and point2:
                # Calculate top-left and bottom-right points of the bounding box
                x_min = min(point1[0], point2[0])
                y_min = min(point1[1], point2[1])
                x_max = max(point1[0], point2[0])
                y_max = max(point1[1], point2[1])
                break
            else:
                print("No region selected.")

    # Crop the image
    cropped_image = clone[y_min:y_max, x_min:x_max]
    cv2.imwrite(OUT_F_CROPPED, cropped_image)

    # Save data
    with open(OUT_F_POINTS, 'w') as f:
        print(y_min, y_max, x_min, x_max, file=f)
        print(y_min, y_max, x_min, x_max)

    annotated_image = annotate_squares(cropped_image)
    cv2.imwrite(OUT_F_ANNOTATED, annotated_image)

    while True:
        cv2.imshow('Annotated Image', annotated_image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break


    cv2.waitKey(0)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crop an image interactively.')
    parser.add_argument('--device', type=str, help='Device index to capture from (e.g., 0 for webcam)')
    parser.add_argument('--image', type=str, help='Path to an image file')
    args = parser.parse_args()
    main(args)