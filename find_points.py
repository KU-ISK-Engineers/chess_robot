import cv2
import argparse
import sys

OUT_F_POINTS = "points.txt"
OUT_F_IMAGE = "cropped.png"

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

def main(args):
    if args.device is not None:
        cap = cv2.VideoCapture(args.device)
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture from the specified device.", file=sys.stderr)
            return
    elif args.image is not None:
        frame = cv2.imread(args.image)
    else:
        print("Please specify either --device or --image.")
        return

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

                # Crop the image
                cropped_image = clone[y_min:y_max, x_min:x_max]
                cv2.imshow('Cropped Image', cropped_image)
                cv2.waitKey(0)
                break
            else:
                print("No region selected.")

    # Save data
    cv2.imwrite(OUT_F_IMAGE, cropped_image)
    with open(OUT_F_POINTS, 'w') as f:
        print(y_min, y_max, x_min, x_max, file=f)
        print(y_min, y_max, x_min, x_max)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crop an image interactively.')
    parser.add_argument('--device', type=str, help='Device index to capture from (e.g., 0 for webcam)')
    parser.add_argument('--image', type=str, help='Path to an image file')
    args = parser.parse_args()
    main(args)

