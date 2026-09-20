"""
Hand-Gesture Controlled Light & Fan
====================================

Uses your webcam (laptop/desktop, or a phone camera streamed as a webcam)
to detect hand gestures with MediaPipe and turn a "Light" and a "Fan"
ON/OFF based on how many fingers you hold up.

GESTURE MAP (right hand, palm facing camera)
    1 finger   -> Light ON
    2 fingers  -> Light OFF
    3 fingers  -> Fan ON
    4 fingers  -> Fan OFF
    Open palm (5) -> Everything ON
    Fist (0)   -> Everything OFF

INSTALL
    pip install opencv-python mediapipe

RUN
    python gesture_light_fan_control.py

MOBILE NOTE
    MediaPipe + OpenCV run best on a desktop/laptop with a normal webcam.
    To use your phone as the camera source instead of a built-in webcam:
      - Install an "IP Webcam" app (Android) or "EpocCam"/"iVCam" (iOS),
        which turns your phone into a network camera.
      - Replace the `cv2.VideoCapture(0)` line below with the stream URL,
        e.g. cv2.VideoCapture("http://192.168.1.5:8080/video")
    Running MediaPipe directly ON a phone would require Pydroid3 (Android)
    or a dedicated mobile ML pipeline (MediaPipe Tasks for Android/iOS) -
    those use a different (Java/Kotlin/Swift) API, not this script.

HARDWARE NOTE
    This script prints/logs "Light ON", "Fan OFF", etc. and calls the
    functions `set_light()` / `set_fan()`. Wire those functions to your
    actual hardware:
      - Raspberry Pi + relay module -> use RPi.GPIO (example included, commented out)
      - Arduino + relay module      -> send a command over serial (example included, commented out)
      - Smart plug / Wi-Fi relay    -> call its HTTP API instead
"""

import time
import cv2
import mediapipe as mp

# ----------------------------------------------------------------------
# OPTIONAL: real hardware control. Uncomment and configure ONE of these
# blocks depending on what you're actually driving.
# ----------------------------------------------------------------------

# --- Raspberry Pi GPIO relay example ---
# import RPi.GPIO as GPIO
# LIGHT_PIN, FAN_PIN = 17, 27
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(LIGHT_PIN, GPIO.OUT)
# GPIO.setup(FAN_PIN, GPIO.OUT)

# --- Arduino over serial relay example ---
# import serial
# arduino = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)  # adjust port


def set_light(state: bool):
    """Turn the light ON (True) or OFF (False)."""
    print(f"[LIGHT] {'ON' if state else 'OFF'}")
    # GPIO.output(LIGHT_PIN, GPIO.HIGH if state else GPIO.LOW)
    # arduino.write(b'L1' if state else b'L0')


def set_fan(state: bool):
    """Turn the fan ON (True) or OFF (False)."""
    print(f"[FAN] {'ON' if state else 'OFF'}")
    # GPIO.output(FAN_PIN, GPIO.HIGH if state else GPIO.LOW)
    # arduino.write(b'F1' if state else b'F0')


# ----------------------------------------------------------------------
# Hand tracking setup
# ----------------------------------------------------------------------

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Landmark indices for fingertips and the joint below each (for the
# "is this finger extended" check)
FINGER_TIPS = [4, 8, 12, 16, 20]
FINGER_PIPS = [3, 6, 10, 14, 18]


def count_fingers(hand_landmarks, handedness_label: str) -> int:
    """Return how many fingers are extended (0-5) for one detected hand."""
    lm = hand_landmarks.landmark
    fingers_up = []

    # Thumb: compare x-coordinates (mirrors depending on left/right hand)
    if handedness_label == "Right":
        fingers_up.append(lm[FINGER_TIPS[0]].x < lm[FINGER_PIPS[0]].x)
    else:
        fingers_up.append(lm[FINGER_TIPS[0]].x > lm[FINGER_PIPS[0]].x)

    # Other 4 fingers: tip above (smaller y than) the pip joint = extended
    for tip, pip in zip(FINGER_TIPS[1:], FINGER_PIPS[1:]):
        fingers_up.append(lm[tip].y < lm[pip].y)

    return sum(fingers_up)


def apply_gesture(finger_count: int, light_state: bool, fan_state: bool):
    """Map a finger count to light/fan actions. Returns updated states."""
    if finger_count == 1:
        light_state = True
    elif finger_count == 2:
        light_state = False
    elif finger_count == 3:
        fan_state = True
    elif finger_count == 4:
        fan_state = False
    elif finger_count == 5:
        light_state, fan_state = True, True
    elif finger_count == 0:
        light_state, fan_state = False, False
    return light_state, fan_state


def main():
    # For mobile-camera streaming, swap 0 for your phone's stream URL, e.g.:
    # cap = cv2.VideoCapture("http://192.168.1.5:8080/video")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Could not open camera. Check the source (index or URL).")
        return

    light_state, fan_state = False, False
    last_action_time = 0
    action_cooldown = 1.0  # seconds, avoids rapid re-triggering on a held gesture

    with mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5,
    ) as hands:
        while True:
            success, frame = cap.read()
            if not success:
                print("Failed to read frame from camera.")
                break

            frame = cv2.flip(frame, 1)  # mirror for a natural "selfie" view
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            finger_count = -1

            if results.multi_hand_landmarks and results.multi_handedness:
                hand_landmarks = results.multi_hand_landmarks[0]
                handedness_label = results.multi_handedness[0].classification[0].label
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                finger_count = count_fingers(hand_landmarks, handedness_label)

                now = time.time()
                if now - last_action_time > action_cooldown:
                    new_light, new_fan = apply_gesture(finger_count, light_state, fan_state)
                    if new_light != light_state:
                        light_state = new_light
                        set_light(light_state)
                        last_action_time = now
                    if new_fan != fan_state:
                        fan_state = new_fan
                        set_fan(fan_state)
                        last_action_time = now

            # --- On-screen status overlay ---
            cv2.putText(frame, f"Fingers: {finger_count if finger_count >= 0 else '-'}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(frame, f"Light: {'ON' if light_state else 'OFF'}",
                        (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 0) if light_state else (0, 0, 255), 2)
            cv2.putText(frame, f"Fan: {'ON' if fan_state else 'OFF'}",
                        (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 0) if fan_state else (0, 0, 255), 2)
            cv2.putText(frame, "1=LightON 2=LightOFF 3=FanON 4=FanOFF 5=AllON Fist=AllOFF",
                        (10, frame.shape[0] - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 0), 1)

            cv2.imshow("Gesture Light & Fan Control", frame)

            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):  # 'q' or Esc to quit
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
