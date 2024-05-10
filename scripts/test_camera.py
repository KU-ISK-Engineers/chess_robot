from pypylon import pylon
import cv2

def main():
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()

    # Set auto exposure mode to continuous
    camera.ExposureAuto.SetValue('Continuous')
    
    # Set camera parameters
    camera.AcquisitionMode.SetValue("Continuous")
        
        
    # Set pixel format to RGB
    camera.PixelFormat.SetValue("RGB8")
        
    camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    while (True):

        grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grab_result.GrabSucceeded():
            # Convert the grabbed frame to OpenCV format
            image1 = grab_result.Array
                
            # Convert the RGB image to BGR
            image1 = cv2.cvtColor(image1, cv2.COLOR_RGB2BGR)
                
            cv2.imshow("image", image1)
            
        

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        grab_result.Release()
main()