import cv2
import os

def detect_cameras(max_index=5):
    cameras = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap is not None and cap.isOpened():
            cameras.append(i)
            cap.release()
    if len(cameras) == 0:
        raise Exception("No USB cameras found")
    return cameras

def create_pipe(pipe_path):
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
