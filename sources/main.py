import cv2 as cv
from windowcapture import WindowCapture
from vision import Vision
from fishing_bot import FishermanBot
import numpy as np
import threading

def debug():
    wincap = WindowCapture('Albion Online Client')
    vision = Vision('./bobber_2.png')
    from time import time
    loop_time = time()
    while True:
        screenshot = wincap.get_screenshot(region=(690, 440, 215, 55))
        screenshot = cv.cvtColor(screenshot, cv.COLOR_RGB2BGR)
        screenshot = screenshot.astype(np.uint8)
        rectangles = vision.find(screenshot, 0.7)
        vision.draw_rectangles(screenshot, rectangles)
        cv.imshow("Test", screenshot)
        print('FPS: {}'.format(1 / (time() - loop_time)))
        loop_time = time()
        if cv.waitKey(1) == ord(']'):
            cv.destroyAllWindows()
            break

if __name__ == "__main__":
    bot = FishermanBot('./bobber_2.png', './empty_bar_2.png', (690, 440, 215, 55))
    # threading.Thread(target=debug).start()
    bot.init_gui()
    
    