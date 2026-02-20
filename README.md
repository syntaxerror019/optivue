<div align="center">

# OptiVue

**Self-hosted, all-in-one CCTV system. Runs on anything.**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20RPi-brightgreen)]()
[![Status](https://img.shields.io/badge/Status-In%20Development-orange)]()
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)

</div>

---

OptiVue is a lightweight, self-hosted camera management system built with Python and Flask. It handles live viewing, continuous recording, motion detection, and snapshot capture through a clean browser-based interface -- no cloud, no subscriptions, no bloat.

Designed to run on low-powered hardware. Tested on a Raspberry Pi 3B+.

---

## Features

| Feature | Description |
|---|---|
| Live view | Multi-camera grid, accessible from any browser on your network |
| Recording | Continuous or scheduled recording, configurable per camera |
| Motion detection | Trigger clips and snapshots on movement |
| Photo capture | Periodic or event-driven snapshots with timestamps |
| Recordings browser | Review clips and snapshots, filterable by date and time |
| Lightweight | Minimal dependencies, runs comfortably on older hardware |
| Web config | Camera and system settings managed through the UI |

---

## Quick Start

```bash
git clone https://github.com/syntaxerror019name/optivue.git
cd optivue
pip install -r requirements.txt
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your camera details, then:

```bash
python main.py
```

Open `http://localhost:5000` in your browser.

See the [Quick Start wiki page](../../wiki/Quick-Start) for the full setup guide, including how to run OptiVue as a background service.

---

## Requirements

- Python 3.9+
- OpenCV ([Learn to install quickly on RPi](https://www.mileshilliard.com/posts/rpi-cv2/))
- USB camera(s) connected physically

---

## Documentation

Full documentation is in the [Wiki](../../wiki):

- [Home](../../wiki/Home)
- [Quick Start](../../wiki/Quick-Start)
- [Configuration](../../wiki/Configuration)
- [Troubleshooting](../../wiki/Troubleshooting)

---

## Hardware

OptiVue is built to be hardware-agnostic.

| Hardware | Status |
|---|---|
| Raspberry Pi 3B+ | Tested, working |
| Raspberry Pi 4 | Expected to work |
| Any Linux x86_64 machine | Tested, working |

---

## Roadmap

- [x] Live multi-camera view
- [x] Continuous recording
- [x] Motion detection
- [x] Snapshot capture
- [x] Recordings browser with date/time filtering
- [ ] Push alerts (email / webhook)
- [ ] Per-camera motion sensitivity controls
- [ ] Mobile-optimised UI

---

## Contributing

Issues and pull requests are welcome. If you find a bug or want to request a feature, open an issue and describe what you're seeing or what you need.

---

## License

[MIT](LICENSE)