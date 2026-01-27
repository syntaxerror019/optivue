import cv2
from datetime import datetime

def add_overlay(frame, cam_index, motion_detected=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # milliseconds
    status_text = "MOTION" if motion_detected else "OK."

    text = f"CAM {cam_index} {timestamp} {status_text}"
    org = (10, 35)
    font = cv2.FONT_HERSHEY_SIMPLEX

    scale = 0.8                 # bigger text
    outline_thickness = 8       # thick black border
    text_thickness = 2          # thick white text

    # Black outline
    cv2.putText(
        frame, text, org, font, scale,
        (0, 0, 0), outline_thickness, cv2.LINE_AA
    )

    # White text
    cv2.putText(
        frame, text, org, font, scale,
        (255, 255, 255), text_thickness, cv2.LINE_AA
    )

    return frame
