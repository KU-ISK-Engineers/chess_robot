from pypylon import pylon
import cv2
import time
from flask import Flask, Response
import threading
import sys

from identify_real_time import setup_camera, preprocess_image, crop_image, setup_points, setup_yolo, detect, map_bboxes_to_squares, annotate_squares

app = Flask(__name__)

latest_frame = None
frame_lock = threading.Lock()

def grab_frames():
    global camera, latest_frame
    while camera.IsGrabbing():
        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            # Convert the grabbed frame to OpenCV format
            image = grab_result.Array
            image = preprocess_image(image)
            image = crop_image(image, points)

            bbox, label, conf = detect(image, yolo)

            mapped_squares = map_bboxes_to_squares(image, bbox, label, conf)                
            #print(mapped_squares)
            image = annotate_squares(image, mapped_squares)

            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', image)
            frame = buffer.tobytes()

            with frame_lock:
                latest_frame = frame

            grab_result.Release()
        else:
            time.sleep(0.1)  # Sleep a bit if no frame is grabbed

def gen_frames():
    global latest_frame
    while True:
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return "Camera Video Stream"

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python web_server.py path_to_weights path_to_points")
        sys.exit(1)

    camera = setup_camera()
    yolo = setup_yolo(sys.argv[1])
    points = setup_points(sys.argv[2])

    frame_thread = threading.Thread(target=grab_frames)
    frame_thread.start()
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        camera.StopGrabbing()
        camera.Close()
        cv2.destroyAllWindows()
