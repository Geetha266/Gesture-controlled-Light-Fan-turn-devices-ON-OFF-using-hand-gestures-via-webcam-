# Gesture-Controlled Light & Fan 🖐️💡🌀

Control a light and a fan **with hand gestures** captured by your webcam — no touch, no remote. Built with **OpenCV** for video capture and **MediaPipe** for real-time hand tracking, in pure Python.

## Demo Overview

Hold up a number of fingers in front of your camera and the app toggles your light/fan accordingly. The current finger count and device states are overlaid live on the video feed.

## Gesture Map

| Gesture         | Action        |
|-----------------|---------------|
| ☝️ 1 finger      | Light **ON**  |
| ✌️ 2 fingers     | Light **OFF** |
| 🤟 3 fingers     | Fan **ON**    |
| 🖖 4 fingers     | Fan **OFF**   |
| 🖐️ Open palm (5) | Everything **ON**  |
| ✊ Fist (0)      | Everything **OFF** |

## Features

- Real-time hand tracking via MediaPipe (21 landmark points per hand)
- Finger-counting logic that works for either hand (left/right aware)
- 1-second action cooldown to prevent a held gesture from re-triggering every frame
- Live on-screen overlay: finger count, light/fan status, gesture legend
- Clean hook points (`set_light()`, `set_fan()`) to wire in real hardware

## Requirements

- Python 3.8+
- A webcam (built-in or USB), or a phone streamed as an IP camera

## Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pip install opencv-python mediapipe
```

## Usage

```bash
python gesture_light_fan_control.py
```

- Press **`q`** or **`Esc`** to quit.
- Make sure your hand is well-lit and fully visible in frame for best detection.

### Using your phone as the camera

Desktop is the recommended platform for running OpenCV + MediaPipe. To use your phone's camera instead of a laptop webcam:

1. Install an IP camera app on your phone (e.g. **IP Webcam** for Android, **EpocCam**/**iVCam** for iOS).
2. Connect your phone and computer to the same Wi-Fi network.
3. In `gesture_light_fan_control.py`, replace:
   ```python
   cap = cv2.VideoCapture(0)
   ```
   with your phone's stream URL:
   ```python
   cap = cv2.VideoCapture("http://192.168.1.5:8080/video")
   ```
   The script itself still runs on your computer — only the video source changes.

## Connecting Real Hardware

By default, `set_light()` and `set_fan()` just print to the console (`[LIGHT] ON`, `[FAN] OFF`, ...). Swap in one of the following depending on your setup:

### Raspberry Pi (GPIO + relay module)

```python
import RPi.GPIO as GPIO
LIGHT_PIN, FAN_PIN = 17, 27
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT_PIN, GPIO.OUT)
GPIO.setup(FAN_PIN, GPIO.OUT)

def set_light(state: bool):
    GPIO.output(LIGHT_PIN, GPIO.HIGH if state else GPIO.LOW)

def set_fan(state: bool):
    GPIO.output(FAN_PIN, GPIO.HIGH if state else GPIO.LOW)
```

### Arduino (serial + relay module)

```python
import serial
arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # adjust port

def set_light(state: bool):
    arduino.write(b'L1' if state else b'L0')

def set_fan(state: bool):
    arduino.write(b'F1' if state else b'F0')
```

### Smart plug / Wi-Fi relay

Call the device's HTTP/cloud API from inside `set_light()` / `set_fan()` instead (implementation depends on your specific smart plug brand).

## How It Works

1. **Capture** – `cv2.VideoCapture` grabs frames from the webcam.
2. **Detect** – Each frame is converted to RGB and passed to MediaPipe's Hands model, which returns 21 landmark points for any detected hand.
3. **Count fingers** – Each fingertip landmark is compared to the joint below it to determine if that finger is extended; the thumb is checked on the x-axis since it moves sideways.
4. **Map gesture → action** – The finger count (0–5) maps to a light/fan ON/OFF state.
5. **Debounce** – A cooldown timer prevents the same held gesture from re-triggering every single frame.
6. **Output** – `set_light()` / `set_fan()` fire when a state actually changes — this is the hook point for real hardware.
7. **Overlay** – The hand skeleton, finger count, and device states are drawn on the live video window.

## Project Structure

```
.
├── gesture_light_fan_control.py   # main app
└── README.md
```

## License

MIT — feel free to use, modify, and share.
