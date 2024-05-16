import cv2
import numpy as np
from pypylon import pylon
import imutils
from cvlib.object_detection import YOLO

def resize_with_aspectratio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]
    
    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    # Resize the image
    resized = cv2.resize(image, dim, interpolation=inter)
    return resized


def main():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    #camera.AcquisitionFrameRateEnable.SetValue(True)
    #camera.AcquisitionFrameRate.SetValue(5)
    camera.ExposureAuto.SetValue('Continuous')
    camera.AcquisitionMode.SetValue("Continuous")
    camera.PixelFormat.SetValue("RGB8")
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
    cv2.namedWindow("Camera View", cv2.WINDOW_NORMAL)

    weights = "chess2-weights/yolov4-tiny-custom_best.weights"
    config = "yolov4-tiny-custom.cfg"
    labels = "obj.names"
    yolo = YOLO(weights, config, labels)

    try:
        while camera.IsGrabbing():
            grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
            if grab_result.GrabSucceeded():
                image = grab_result.Array
                if image is not None and image.size != 0:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                    # Convert the grayscale image to a 3-channel grayscale image
                    image_3_channel = cv2.merge([image, image, image])

                    # Keep a copy of the original for drawing
                    original = image_3_channel.copy()

                    #image = resize_with_aspectratio(image, width=416)  # Resize maintaining aspect ratio
                    #original = image.copy()  # Keep a copy of the original for drawing

                    bbox, label, conf = yolo.detect_objects(image_3_channel)

                    print(bbox, label, conf)

                    # Manual bounding box drawing for debugging
                    for box, lbl, cf in zip(bbox, label, conf):
                        if cf > 0.5:  # Filter out low confidence detections
                            x, y, w, h = box
                            cv2.rectangle(original, (x, y), (x+w, y+h), (0, 255, 0), 2)
                            cv2.putText(original, f"{lbl} {cf:.2f}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                    # original = yolo.draw_bbox(original, bbox, label, conf)  # Draw on original size

                    cv2.imshow('Camera View', original)
                else:
                    print("No image captured or image is empty.")
                
                if cv2.waitKey(1) == 27:
                    break
            else:
                print("Grab failed.")
            grab_result.Release()
    finally:
        camera.StopGrabbing()
        camera.Close()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
