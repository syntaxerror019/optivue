<div align="center">

# OptiVue

**A self-hosted, all-in-one CCTV system built for simplicity and low-power hardware.**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Platform](https://img.shields.io/badge/Tested%20on-Raspberry%20Pi%203B%2B-C51A4A?logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com)
[![Status](https://img.shields.io/badge/Status-In%20Development-orange)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

</div>

---

OptiVue is a lightweight, browser-based NVR (Network Video Recorder) built with Python and Flask. Connect your IP cameras, open a browser, and you have a fully functional CCTV system with live viewing, recording, motion detection, and snapshot capture -- no cloud, no subscriptions, no bloat.

Designed to run on modest hardware. Tested and working on a Raspberry Pi 3B+.

---

## Features

| Feature | Details |
|---|---|
| Live View | Multi-camera browser-based stream viewer |
| Recording | Adjustable and 24/7 continuous clip recording |
| Motion Detection | Trigger-based recording on detected movement |
| Photo Detection | Automatic snapshot capture on activity |
| Recordings Browser | Review and filter clips and snapshots by date and time |
| Web Config | Camera and system settings managed through the UI |
| Lightweight | Minimal dependencies, runs on low-power hardware |

---

## Quick Start

```bash
git clone https://github.com/yourusername/optivue.git
cd optivue
pip install -r requirements.txt
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your camera RTSP URLs, then:

```bash
python main.py
```

Open `http://localhost:5000` in your browser.

See the [Quick Start](../../wiki/Quick-Start) wiki page for the full setup guide including Raspberry Pi instructions and running as a background service.

---

## Requirements

- Python 3.9+
- FFmpeg (on system PATH)
- RTSP-capable IP cameras

---

## Documentation

Full documentation is in the [Wiki](../../wiki).

| Page | Description |
|---|---|
| [Quick Start](../../wiki/Quick-Start) | Install, configure, and get running |
| [Configuration](../../wiki/Configuration) | All `config.yaml` options explained |
| [API Reference](../../wiki/API-Reference) | REST endpoints |
| [Camera Compatibility](../../wiki/Camera-Compatibility) | Tested cameras and RTSP URL formats |
| [Troubleshooting](../../wiki/Troubleshooting) | Common issues and fixes |

---

## Project Structure

```
optivue/
├── main.py
├── config.yaml                  # Your config (gitignored)
├── config.example.yaml
├── requirements.txt
├── templates/
│   ├── components/
│   │   ├── styles.html
│   │   ├── header.html
│   │   ├── status_bar.html
│   │   └── control_bar.html
│   ├── index.html               # Live view
│   └── recordings.html          # Recordings browser
└── storage/                     # Clips and snapshots (gitignored)
```

---

## Roadmap

- [x] Live multi-camera view
- [x] Continuous and scheduled recording
- [x] Motion detection
- [x] Snapshot capture
- [x] Recordings browser with date/time filtering
- [ ] Push alerts (email / webhook)
- [ ] Mobile-optimised UI
- [ ] User authentication

---

## Contributing

Issues and pull requests are welcome. If you find a bug or have a feature request, please [open an issue](../../issues) first.

## License

MIT