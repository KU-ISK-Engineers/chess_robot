# Import libraries
import cv2
import numpy as np
import imutils
import requests
from cvlib.object_detection import YOLO
  
# Replace the below URL with your own IP provided by the IP WEBCAM APP.
# Make sure to add "/shot.jpg" at last.
url = "http://192.168.0.205:8080/shot.jpg"
  
# While loop to continuously fetching data from the Url

weights="yolov4-tiny-custom_best.weights"
config="yolov4-tiny-custom.cfg"
labels="obj.names"
yolo = YOLO(weights, config,labels)

count=0

while True:
    img_resp = requests.get(url)
    img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
    img = cv2.imdecode(img_arr, -1)
    img = imutils.resize(img, width=1920, height=1080)

    count += 1
    if count % 10 != 0:
        continue

    # Press Esc key to exit
    if cv2.waitKey(1) == 27:
        break
    
    bbox, label, conf = yolo.detect_objects(img)
    img1=yolo.draw_bbox(img, bbox, label, conf)
    cv2.imshow("img1",img)
  

cv2.destroyAllWindows()
# import cv2
#
# cap=cv2.VideoCapture('http://192.168.0.205:8080/shot.jpg')
# while True:
#     ret,img=cap.read()
#     if not ret:
#         print('Error?')
#         continue
#     img=cv2.resize(img,(680,460))
#     cv2.imshow('frame', img)

    # count += 1
    # if count % 10 != 0:
    #     continue
    # 
    # if cv2.waitKey(1)&0xFF==27:
    #     break


#cap=cv2.VideoCapture('http://192.168.0.205:8080')

