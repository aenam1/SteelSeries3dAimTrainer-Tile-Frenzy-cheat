import cv2
import mss
import numpy as np
import time
from pynput.keyboard import Listener
from win32api import mouse_event
import win32con

# Configurable Area (Top, Left, Width, Height)
# Centered 600x600 box for 1080p
MONITOR = {
    "top": 240,    # (1080 - 600) / 2
    "left": 660,   # (1920 - 600) / 2
    "width": 600,
    "height": 600
}

# Target Color Range (HSV) - Adjusted for Tile Frenzy
LOWER_COLOR = np.array([6, 187, 96])
UPPER_COLOR = np.array([18, 255, 255])

# Performance Scalers
SX, SY = 1.0, 1.0
R_VALUE = 500

running = True

def on_press(key):
    global running
    try:
        if key.char == 'q': running = False
    except AttributeError: pass

# Background keyboard listener
keyboard_listener = Listener(on_press=on_press)
keyboard_listener.start()

def perform_click(dx, dy):
    """Calculates arc-length for 3D projection and clicks."""
    # Using the more accurate calculation from your main.py
    target_x = int(R_VALUE * np.arctan(dx / R_VALUE) // SX)
    target_y = int(R_VALUE * np.arctan(dy / R_VALUE) // SY)

    # Relative Move + Click
    mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_LEFTDOWN | win32con.MOUSEEVENTF_LEFTUP, target_x, target_y, 0, 0)
    time.sleep(0.1)
    # Return to center
    mouse_event(win32con.MOUSEEVENTF_MOVE, -target_x, -target_y, 0, 0)

print("Starting in 3 seconds...")
time.sleep(3)

with mss.mss() as sct:
    # Calculate center of the capture box
    cx, cy = MONITOR["width"] // 2, MONITOR["height"] // 2

    while running:
        # Fast grab using MSS
        sct_img = sct.grab(MONITOR)
        frame = np.array(sct_img)
        
        # Convert to HSV (OpenCV 4.10+ optimized)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
        
        mask = cv2.inRange(hsv, LOWER_COLOR, UPPER_COLOR)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort by size and take the top targets
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        for contour in contours[:3]: # Fire at top 3 targets
            M = cv2.moments(contour)
            if M["m00"] > 0:
                tx = int(M["m10"] / M["m00"])
                ty = int(M["m01"] / M["m00"])
                
                perform_click(tx - cx, ty - cy)
                
        time.sleep(0.05) # Prevent CPU overload

print("Script stopped.")