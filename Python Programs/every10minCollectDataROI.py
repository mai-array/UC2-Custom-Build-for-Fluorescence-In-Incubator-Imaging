import RPi.GPIO as GPIO
import time
from picamzero import Camera
import os
import threading
from datetime import datetime
from picamera2 import Picamera2
# -------------------- Camera Setup --------------------
home_dir = os.environ['HOME']
save_dir = os.path.join(home_dir, "Desktop")

picam2 = Picamera2()

# Sensor + ROI parameters (Camera Module v2 / IMX219)
SENSOR_WIDTH = 3280
SENSOR_HEIGHT = 2464

ROI_SIZE = 2500  # true sensor ROI, full resolution

ROI_X = (SENSOR_WIDTH - ROI_SIZE) // 2
ROI_Y = (SENSOR_HEIGHT - ROI_SIZE) // 2

# Configure the camera with full-res ROI
picam2.configure(
    picam2.create_still_configuration(
        main={"size": (ROI_SIZE, ROI_SIZE)}
    )
)

picam2.start()

# Lock camera settings (important for fluorescence & timelapse)
picam2.set_controls({
    "ScalerCrop": (ROI_X, ROI_Y, ROI_SIZE, ROI_SIZE),
    "ExposureTime": 10000,   # µs
    "AnalogueGain": 1.0,
    "AwbEnable": False
})

print("Camera initialized with true sensor ROI")
# -------------------- GPIO Setup --------------------
GPIO.setmode(GPIO.BCM)


laser_pin = 18
GPIO.setup(laser_pin, GPIO.OUT, initial=GPIO.LOW)

# Stepper motor pins
IN1 = 2   
IN2 = 3   
IN3 = 4   
IN4 = 17  

control_pins = [IN1, IN2, IN3, IN4]
for pin in control_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

# -------------------- Stepper Motor Sequence --------------------
step_sequence = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

STEPS_PER_REV = 100
STEP_DELAY = 0.0015

# -------------------- Stepper Motor Function --------------------
def move_motor(steps, direction=1):
    sequence_len = len(step_sequence)
    for step in range(steps):
        for pin in range(4):
            index = step % sequence_len
            if direction == -1:
                index = (-step) % sequence_len
            GPIO.output(control_pins[pin], step_sequence[index][pin])
        time.sleep(STEP_DELAY)

# -------------------- Automatic Photo Function --------------------
def take_scheduled_photo():
    while True:
        print("\n Starting scheduled photo capture...")
        
        # Turn laser ON for 3 seconds
        GPIO.output(laser_pin, GPIO.HIGH)
        print("Laser ON (3s pre-photo)")
        time.sleep(3)

        # Capture photo with timestamp
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"auto_{timestamp}.jpg"
        filepath = os.path.join(save_dir, filename)
        picam2.capture_file(filepath)
        print(f"Captured: {filename}")

        # Keep laser ON for 2 more seconds
        print("Laser stays ON for 2s post-photo")
        time.sleep(2)

        # Turn laser OFF
        GPIO.output(laser_pin, GPIO.LOW)
        print("Laser OFF. Waiting 3 minutes...")

        time.sleep(180)  # 3 minutes = 180 seconds


auto_thread = threading.Thread(target=take_scheduled_photo, daemon=True)
auto_thread.start()

# -------------------- Main Loop --------------------
img_count = 1

print("Manual Commands:")
print(" - on / off     => Laser control")
print(" - pic            => Take photo")
print(" - cw / ccw     => Rotate motor clockwise / counterclockwise")
print(" - exit           => Exit program")

try:
    while True:
        cmd = input("Enter command: ").strip().lower()

        if cmd == "on":
            GPIO.output(laser_pin, GPIO.HIGH)
            print("LASER ON")

        elif cmd == "off":
            GPIO.output(laser_pin, GPIO.LOW)
            print("LASER OFF")

        elif cmd == "pic":
          now = datetime.now()
           timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"MANUAL_{timestamp}.jpg"
            filepath = os.path.join(save_dir, filename)
            picam2.capture_file(filepath)
            print(f"Captured: {filename}")

        elif cmd == "cw":
            print("Rotating clockwise...")
            move_motor(STEPS_PER_REV, direction=1)

        elif cmd == "ccw":
            print("Rotating counterclockwise...")
            move_motor(STEPS_PER_REV, direction=-1)

        elif cmd == "exit":
            print("Exiting program...")
            break

        else:
            print("Invalid command. Use 'on', 'off', 'pic', 'cw', 'ccw', or 'exit'.")

except KeyboardInterrupt:
    print("\nInterrupted by user.")

finally:
    GPIO.cleanup()
    print("GPIO cleaned up. Program ended.")
