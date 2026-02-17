import os
from flask import Flask, Response, render_template, request
from web.auth import require_basic_auth
from utils.config import ConfigSaver
from werkzeug.serving import make_server
import threading

class StreamingServer:
    def __init__(self, pipe_dir="/tmp/cam_pipes", host="0.0.0.0", port=5000, config=None):
        self.pipe_dir = pipe_dir
        self.config = config
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.routes_created = []
        
        self.config_saver = ConfigSaver()
        self._server = None
        self._thread = None
        self._stop_event = threading.Event()

        # Index route
        self.app.route("/")(self.index)
        self.app.route("/settings", methods=["GET", "POST"])(self.settings)

    def _generate_mjpeg(self, pipe_path):
        while True:
            try:
                with open(pipe_path, 'rb') as f:
                    while True:
                        line = f.readline()
                        if not line:
                            continue
                        if line.startswith(b'--frame'):
                            # Skip headers
                            while True:
                                header = f.readline()
                                if header == b'\r\n':
                                    break
                            data = b''
                            while True:
                                chunk = f.readline()
                                if chunk.startswith(b'--frame') or not chunk:
                                    break
                                data += chunk
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')
            except (BrokenPipeError, FileNotFoundError):
                print(f"[WARN] Pipe {pipe_path} broken, retrying in 0.5s")
                import time
                time.sleep(0.5)
                continue

    def make_mjpeg_route(self, pipe_path):
        def route_func():
            return Response(
                self._generate_mjpeg(pipe_path),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        return route_func

    def add_routes(self):
        for pipe_file in os.listdir(self.pipe_dir):
            if pipe_file.endswith(".mjpeg"):
                pipe_path = os.path.join(self.pipe_dir, pipe_file)
                route_name = "/stream/" + pipe_file
                self.app.add_url_rule(route_name, route_name, self.make_mjpeg_route(pipe_path))
                
                entry = {
                    "name": pipe_file,
                    "url": route_name,
                    "resolution": f"{self.config.camera_height}x{self.config.camera_width}",
                    "framerate": self.config.camera_fps,
                    "show_info" : True
                }
                
                self.routes_created.append(entry)
                print(f"Streaming route created: {route_name}")
                
    #@require_basic_auth
    def index(self):
        cameras = self.routes_created
        return render_template('index.html', 
                         cameras=cameras,
                         page='live',
                         page_title='Live View',
                         status_text='Connected'
                         )

    def settings(self):
        if request.method == 'GET':
            return render_template('settings.html', 
                             page='settings',
                             page_title='Settings',
                             status_text='Connected',
                             config=self.config
                             )
        elif request.method == 'POST':
            data = request.get_json()
            
            self.config_saver.save(
                **{
                    'camera.width': int(data['resolution'].split('x')[0]),
                    'camera.height': int(data['resolution'].split('x')[1]),
                    'camera.fps': int(data['frameRate']),
                    'camera.motion_detection': data['motionDetection'],
                    'camera.motion_contour_area': int(data['sensitivity']),
                    'record.enabled': bool(data['record']),
                    'record.recording_length': int(data['recordingLength']),
                    'record.storage_path': data['storagePath'],
                    'record.video_retention': int(data['videoRetention'])
                }
            )
            
            return 'ok',200

    def start(self):
            self.add_routes()
            print(f"Starting server on http://{self.host}:{self.port}")

            def run_app():
                self.app.run(host=self.host, port=self.port, threaded=True, use_reloader=False)

            self._thread = threading.Thread(target=run_app, daemon=True)
            self._thread.start()
        
    def stop(self):
        if self._server:
            print("Stopping Flask server...")
            self._stop_event.set()
            self._thread.join()