import cv2
import numpy as np

class MotionDetector:
    def __init__(self, contour_area=500):
        self.prev_gray = None
        self.prev_gray_float = None 
        self.contour_area = contour_area
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        self.alpha = 0.1  # Lower = slower background adaptation
        
    def preprocess_frame(self, frame):
        # Resize if needed for faster processing
        height, width = frame.shape[:2]
        if width > 320:
            new_width = 320
            new_height = int(height * (320 / width))
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Convert grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Use smaller blur kernel
        return cv2.GaussianBlur(gray, (11, 11), 0)

    def detect(self, frame):
        gray = self.preprocess_frame(frame)

        if self.prev_gray is None:
            self.prev_gray = gray.copy()
            self.prev_gray_float = gray.astype(np.float32)
            return False, frame
        delta = cv2.absdiff(self.prev_gray, gray)
        _, thresh = cv2.threshold(delta, 30, 255, cv2.THRESH_BINARY)
   
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, self.kernel)
        thresh = cv2.dilate(thresh, None, iterations=1)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        motion_box = None
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.contour_area:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(contour)

                if motion_box is None:
                    motion_box = [x, y, x + w, y + h]
                else:
                    motion_box[0] = min(motion_box[0], x)
                    motion_box[1] = min(motion_box[1], y)
                    motion_box[2] = max(motion_box[2], x + w)
                    motion_box[3] = max(motion_box[3], y + h)
        
        # Draw bounding box if motion detected
        if motion_box:
            scale_x = frame.shape[1] / gray.shape[1]
            scale_y = frame.shape[0] / gray.shape[0]
            
            x1 = int(motion_box[0] * scale_x)
            y1 = int(motion_box[1] * scale_y)
            x2 = int(motion_box[2] * scale_x)
            y2 = int(motion_box[3] * scale_y)
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        # Update background with accumulateWeighted (fix the error)
        gray_float = gray.astype(np.float32)
        cv2.accumulateWeighted(gray_float, self.prev_gray_float, self.alpha)
        
        self.prev_gray = np.uint8(self.prev_gray_float)
        
        return motion_detected, frame