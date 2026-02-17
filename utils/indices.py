import cv2
import os

def detect_cameras(max_index=10):
    cameras = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if not cap or not cap.isOpened():
            continue

        ret, frame = cap.read()
        if ret and frame is not None:
            cameras.append(i)

        cap.release()

    if not cameras:
        raise RuntimeError("No usable cameras found")

    return cameras

def create_pipe(pipe_path):
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
