import cv2

class MotionDetector:
    def __init__(self, contour_area=500):
        self.prev_gray = None
        self.contour_area = contour_area

    def preprocess_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.GaussianBlur(gray, (21, 21), 0)

    def detect(self, frame):
        gray = self.preprocess_frame(frame)

        if self.prev_gray is None:
            self.prev_gray = gray
            return False, frame

        # Compute difference and threshold
        delta = cv2.absdiff(self.prev_gray, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_detected = False
        big_box = None  # Will hold the merged bounding box

        for c in contours:
            if cv2.contourArea(c) > self.contour_area:
                motion_detected = True
                x, y, w, h = cv2.boundingRect(c)
                if big_box is None:
                    big_box = [x, y, x + w, y + h]
                else:
                    # Merge current contour with existing big_box
                    big_box[0] = min(big_box[0], x)
                    big_box[1] = min(big_box[1], y)
                    big_box[2] = max(big_box[2], x + w)
                    big_box[3] = max(big_box[3], y + h)

        # Draw single merged rectangle
        if big_box is not None:
            x1, y1, x2, y2 = big_box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        self.prev_gray = gray
        return motion_detected, frame
