# PhotoSlideshow

A premium, containerized photo frame for Raspberry Pi 5 and Mac M1. Featuring smooth transitions, background music, metadata overlays, and a smartphone remote control.

## Features
- **Smooth Transitions**: Professional crossfade between images.
- **Smart Metadata**: Displays album name (from folder) and EXIF date. You can override these per-folder by editing the auto-generated `overlay.txt` file in each album directory.
- **Background Music**: Dynamic audio playback with auto-next and volume control.
- **Smartphone Remote**: Mobile-friendly web UI to control the frame from your phone.
- **Dockerized**: Easy deployment via Docker Compose.

## 🚀 Quick Start (Mac M1)

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Locally**:
   ```bash
   python3 main.py slideshow_photos slideshow_music
   ```
   *The remote will be available at `http://localhost:5001`.*

## 🍓 Raspberry Pi 5 Deployment

1. **Prepare Media**: Place your photos and music in the `slideshow_photos` and `slideshow_music` folders (or update `docker-compose.yml`).

2. **Launch with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Performance Tuning**:
   The `docker-compose.yml` includes commented-out sections for `/dev/dri` and `/dev/snd`. Uncomment these on your Pi for hardware-accelerated rendering and HDMI audio.

## 📱 Web Remote Control
Once running, find your device's IP (e.g., `192.168.1.10`) and navigate to `http://<device-ip>:5001` on your smartphone browser.

- **⏯ Pause/Play**: Stop the timer.
- **⏭ Next/Prev**: Skip through your collection.
- **🔊 Volume**: Adjust the background music.

## Project Structure
- `main.py`: Entry point and application loop.
- `code/`: Core logic (Scanner, Renderer, Music Player, Controller, Web Remote).
- `slideshow_photos/`: Place your images here.
- `slideshow_music/`: Place your audio tracks here.
- `Dockerfile`: Multi-arch container definition.

---
Built with ❤️ for Raspberry Pi enthusiasts.
