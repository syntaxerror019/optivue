import cv2
import time

def add_overlay(frame, cam_index, motion_detected=False):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    status_text = "MOTION" if motion_detected else "No Motion"
    color = (0, 0, 255) if motion_detected else (0, 255, 0)
    cv2.putText(frame,
                f"CAM {cam_index} {timestamp} {status_text}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2)
    return frame
