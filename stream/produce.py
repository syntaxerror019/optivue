from utils.motion import MotionDetector
from utils.overlays import add_overlay
import cv2, os, time, threading

class CameraProducer:
    def __init__(self, cam_index, pipe_dir="/tmp/cam_pipes", width=640, height=480, fps=15, motion_area=500):
        self.cam_index = cam_index
        self.pipe_dir = pipe_dir
        self.pipe_path = os.path.join(pipe_dir, f"cam{cam_index}.mjpeg")
        self.width = width
        self.height = height
        self.fps = fps
        self.running = False
        
        if not os.path.exists(self.pipe_dir):
            os.makedirs(self.pipe_dir)

        os.makedirs(pipe_dir, exist_ok=True)
        if not os.path.exists(self.pipe_path):
            os.mkfifo(self.pipe_path)

        self.motion_detector = MotionDetector(contour_area=motion_area)
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _run(self):
        cap = cv2.VideoCapture(self.cam_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)

        with open(self.pipe_path, 'wb') as f:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    continue

                motion_detected, frame = self.motion_detector.detect(frame)
                frame = add_overlay(frame, self.cam_index, motion_detected)

                ret, jpeg = cv2.imencode('.jpg', frame)
                if jpeg is not None:
                    try:
                        f.write(b'--frame\r\n')
                        f.write(b'Content-Type: image/jpeg\r\n\r\n')
                        f.write(jpeg.tobytes())
                        f.write(b'\r\n')
                        f.flush()
                    except BrokenPipeError:
                        pass
