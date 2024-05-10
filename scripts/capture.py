from pypylon import pylon
import cv2
import argparse
import os
import time

def main(output_dir):
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    # Set auto exposure mode to continuous
    camera.ExposureAuto.SetValue('Continuous')
    
    # Set camera parameters
    camera.AcquisitionMode.SetValue("Continuous")
    
    # Set pixel format to RGB
    camera.PixelFormat.SetValue("RGB8")
    
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    cv2.namedWindow("Camera View", cv2.WINDOW_NORMAL)  # Create a window for display

    try:
        while True:
            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grab_result.GrabSucceeded():
                # Convert the grabbed frame to OpenCV format
                image = grab_result.Array
                
                # Convert the RGB image to BGR
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                # Display the resulting frame
                cv2.imshow('Camera View', image)
                
                grab_result.Release()

            key = cv2.waitKey(1)  # Wait for key press for 1 ms

            if key == 13:  # 13 is the Enter Key
                # Generate filename with timestamp
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = os.path.join(output_dir, f"{timestamp}.png")

                # Save the image
                cv2.imwrite(filename, image)
                print(f"Saved: {filename}")

            elif key == ord('q'):  # Exit on pressing 'q'
                break

    finally:
        camera.StopGrabbing()
        camera.Close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Press Enter to capture images and display camera view.')
    parser.add_argument('output_dir', type=str, help='Directory to save images.')
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    main(args.output_dir)
