from picamera import PiCamera
import cv2

def capture(img_pth):
    camera = PiCamera()
    camera.capture(img_pth)
    camera.close()
    print("Done capturing!")

def preprocess_img(img_pth):
    img = cv2.imread(img_pth)
    resized_img = cv2.resize(img, (800,800))
    cv2.imwrite(img_pth, resized_img)


