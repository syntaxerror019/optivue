from utils.motion import MotionDetector
from utils.overlays import add_overlay
import cv2
import os
import time
import threading
import numpy as np

class CameraProducer:
    def __init__(self, cam_index, pipe_dir="/tmp/cam_pipes", width=320, height=240, 
                 fps=10, motion_area=500, config=None):
        self.cam_index = cam_index
        self.pipe_dir = pipe_dir
        self.pipe_path = os.path.join(pipe_dir, f"cam{cam_index}.mjpeg")
        self.width = width
        self.height = height
        self.fps = fps
        self.config = config
        self.frame_interval = 1.0 / fps
        
        # Create pipe directory and file
        os.makedirs(pipe_dir, exist_ok=True)
        if not os.path.exists(self.pipe_path):
            os.mkfifo(self.pipe_path)
        
        if self.config.motion_detection:
            self.motion_detector = MotionDetector(contour_area=motion_area)
        
        self._stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        
        # Cache for reducing motion detection frequency
        self.motion_check_interval = 3  # Check motion every N frames
        self.last_motion_state = False
        
    def start(self):
        self._stop_event.clear()
        self.thread.start()
    
    def stop(self):
        self._stop_event.set()
        self.thread.join(timeout=2.0)
    
    def _run(self):
        # Optimized capture settings
        cap = cv2.VideoCapture(self.cam_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.cam_index)
        
        # Set format to MJPEG if camera supports it (reduces USB bandwidth)
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Aggressive JPEG compression for Pi
        encode_param = [
            int(cv2.IMWRITE_JPEG_QUALITY), 60,  # Lower quality
            int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,
            int(cv2.IMWRITE_JPEG_PROGRESSIVE), 0
        ]
        
        frame_count = 0
        next_frame_time = time.time()
        
        # Pre-allocate buffer for JPEG encoding (reuse memory)
        jpeg_buffer = bytearray(self.width * self.height)
        
        try:
            with open(self.pipe_path, 'wb', buffering=8192) as f:  # Larger buffer
                while not self._stop_event.is_set():
                    current_time = time.time()
                    
                    # Precise frame timing
                    if current_time < next_frame_time:
                        time.sleep(max(0.001, next_frame_time - current_time))
                        continue
                    
                    next_frame_time = current_time + self.frame_interval
                    
                    ret, frame = cap.read()
                    if not ret:
                        time.sleep(0.01)
                        continue
                    
                    # Motion detection optimization: only check every Nth frame
                    motion_detected = self.last_motion_state  # Use cached state
                    if self.config.motion_detection and frame_count % self.motion_check_interval == 0:
                        motion_detected, frame = self.motion_detector.detect(frame)
                        self.last_motion_state = motion_detected
                    
                    # Add overlay (minimize this if possible)
                    frame = add_overlay(frame, self.cam_index, motion_detected)
                    
                    # Encode to JPEG
                    ret, jpeg = cv2.imencode('.jpg', frame, encode_param)
                    if ret:
                        try:
                            # More efficient writing
                            jpeg_bytes = jpeg.tobytes()
                            f.write(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n')
                            f.write(jpeg_bytes)
                            f.write(b'\r\n')
                            f.flush()
                        except (BrokenPipeError, OSError):
                            time.sleep(0.1)
                    
                    frame_count += 1
                    
        finally:
            cap.release()