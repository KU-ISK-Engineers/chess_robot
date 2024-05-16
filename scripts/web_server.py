from pypylon import pylon
import cv2
import time
from flask import Flask, Response
import threading

app = Flask(__name__)

camera = None
latest_frame = None
frame_lock = threading.Lock()

def initialize_camera():
    global camera
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    # Set auto exposure mode to continuous
    camera.ExposureAuto.SetValue('Continuous')
    
    # Set camera parameters
    camera.AcquisitionMode.SetValue("Continuous")
    
    # Set pixel format to RGB
    camera.PixelFormat.SetValue("RGB8")
    
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

def grab_frames():
    global camera, latest_frame
    while camera.IsGrabbing():
        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            # Convert the grabbed frame to OpenCV format
            image = grab_result.Array

            # Convert the RGB image to GRAY
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

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
    initialize_camera()
    frame_thread = threading.Thread(target=grab_frames)
    frame_thread.start()
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        camera.StopGrabbing()
        camera.Close()
        cv2.destroyAllWindows()
