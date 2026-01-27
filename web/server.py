import os
from flask import Flask, Response, render_template
from web.auth import require_basic_auth

class StreamingServer:
    def __init__(self, pipe_dir="/tmp/cam_pipes", host="0.0.0.0", port=5000):
        self.pipe_dir = pipe_dir
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.routes_created = []

        # Index route
        self.app.route("/")(self.index)

    def _generate_mjpeg(self, pipe_path):
        """Yield MJPEG frames from pipe, handle broken pipes gracefully."""
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
        """Dynamically create a route per camera pipe."""
        for pipe_file in os.listdir(self.pipe_dir):
            if pipe_file.endswith(".mjpeg"):
                pipe_path = os.path.join(self.pipe_dir, pipe_file)
                route_name = "/stream/" + pipe_file
                self.app.add_url_rule(route_name, route_name, self.make_mjpeg_route(pipe_path))
                self.routes_created.append(route_name)
                print(f"Streaming route created: {route_name}")
    @require_basic_auth
    def index(self):
        """Render a simple HTML page listing all cameras."""
        cameras = self.routes_created
        return render_template('index.html', 
                         cameras=cameras,
                         page='live',
                         page_title='Live View',
                         camera_name='Camera 1',
                         camera_ip='192.168.1.100',
                         resolution='640x480',
                         framerate='30',
                         compression='H.264',
                         status_text='Connected',
                         status_class='')

    def start(self):
        self.add_routes()
        print(f"Starting server on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, threaded=True)