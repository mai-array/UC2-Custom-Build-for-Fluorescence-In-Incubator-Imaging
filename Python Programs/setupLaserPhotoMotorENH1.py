import RPi.GPIO as GPIO
import time
import os
import cv2
from picamera2 import Picamera2

# -------------------- Camera Setup --------------------
home_dir = os.environ['HOME']
save_dir = os.path.join(home_dir, "Desktop")

picam2 = Picamera2()

# Full sensor resolution (Camera Module v3)
FULL_RES = (4056, 3040)
CROP_SIZE = 500

picam2.configure(
    picam2.create_still_configuration(
        main={"size": FULL_RES}
    )
)

picam2.start()

# Lock exposure (important for fluorescence / timelapse)
picam2.set_controls({
    "ExposureTime": 10000,
    "AnalogueGain": 1.0
})

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

STEPS_PER_REV = 2048
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

# -------------------- Image Capture (HIGH-RES CROP) --------------------
def take_cropped_photo(filepath):
    img = picam2.capture_array()

    h, w, _ = img.shape
    x0 = (w - CROP_SIZE) // 2
    y0 = (h - CROP_SIZE) // 2

    crop = img[y0:y0+CROP_SIZE, x0:x0+CROP_SIZE]
    cv2.imwrite(filepath, crop)

# -------------------- Main Loop --------------------
img_count = 1

print("Commands:")
print(" - on / off     => Laser control")
print(" - pic          => Take photo (high-res cropped)")
print(" - cw / ccw     => Rotate motor")
print(" - exit         => Exit program")

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
            filename = f"ECZIncubatorTestsmalla{img_count}.jpg"
            filepath = os.path.join(save_dir, filename)
            take_cropped_photo(filepath)
            print(f"Captured {filename}")
            img_count += 1

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
            print("Invalid command.")

except KeyboardInterrupt:
    print("\nInterrupted by user.")

finally:
    GPIO.cleanup()
    picam2.stop()
    print("GPIO cleaned up. Program ended.")
