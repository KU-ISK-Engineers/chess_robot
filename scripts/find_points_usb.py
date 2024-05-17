from pypylon import pylon
import cv2

OUT_F_POINTS = "points.txt"
OUT_F_CROPPED = "cropped.png"
OUT_F_ANNOTATED = "annotated.png"

# Global variables to store selected points
cropping = False
point1 = None
point2 = None

def click_and_crop(image, points, event, x, y, flags, param):
    global cropping, point1, point2

    if event == cv2.EVENT_LBUTTONDOWN:
        point1 = (x, y)
        cropping = True

    elif event == cv2.EVENT_LBUTTONUP:
        point2 = (x, y)
        cropping = False

        # Draw a rectangle around the selected region
        cv2.rectangle(image, point1, point2, (0, 255, 0), 2)
        cv2.imshow("image", image)

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

def setup_camera():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    camera.AcquisitionFrameRateEnable.SetValue(True)
    camera.AcquisitionFrameRate.SetValue(5)
    camera.ExposureAuto.SetValue('Continuous')
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("RGB8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    return camera

def preprocess_image(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image

def main():
    camera = setup_camera()

    while True:
        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if not grab_result.GrabSucceeded():
            continue

        # Convert the grabbed frame to OpenCV format
        image = grab_result.Array
        image = preprocess_image(image)
        grab_result.Release()

        clone = image.copy()

        global point1, point2

        def crop(event, x, y, flags, param):
            return click_and_crop(image, (point1, point2), event, x, y, flags, param)

        cv2.namedWindow("image", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("image", crop)

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

        if point1 and point2:
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
                cv2.namedWindow('Annotated Image', cv2.WINDOW_NORMAL)
                cv2.imshow('Annotated Image', annotated_image)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break

        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
