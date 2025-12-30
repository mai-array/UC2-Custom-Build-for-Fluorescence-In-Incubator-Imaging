import RPi.GPIO as GPIO
import time
import os
from picamera2 import Picamera2

# -------------------- Camera Setup --------------------
home_dir = os.environ['HOME']
save_dir = os.path.join(home_dir, "Desktop")

picam2 = Picamera2()

# Sensor + ROI parameters (Camera Module v3)
SENSOR_WIDTH = 4056
SENSOR_HEIGHT = 3040

ROI_SIZE = 1000        # sensor pixels
OUTPUT_SIZE = 500      # saved image size

ROI_X = (SENSOR_WIDTH - ROI_SIZE) // 2   # 1528
ROI_Y = (SENSOR_HEIGHT - ROI_SIZE) // 2  # 1020

picam2.configure(
    picam2.create_still_configuration(
        main={"size": (OUTPUT_SIZE, OUTPUT_SIZE)}
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

print("Camera initialized with true sensor ROI.")

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

# -------------------- Main Loop --------------------
img_count = 1

print("\nCommands:")
print(" - on / off   => Laser control")
print(" - pic        => Take photo (true ROI, high-res)")
print(" - cw / ccw   => Rotate motor")
print(" - exit       => Exit program")

try:
    while True:
        cmd = input("\nEnter command: ").strip().lower()

        if cmd == "on":
            GPIO.output(laser_pin, GPIO.HIGH)
            print("LASER ON")

        elif cmd == "off":
            GPIO.output(laser_pin, GPIO.LOW)
            print("LASER OFF")

        elif cmd == "pic":
            filename = f"ECZIncubatorTestsmalla{img_count}.jpg"
            filepath = os.path.join(save_dir, filename)

            picam2.capture_file(filepath)

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
            print("Invalid command. Use 'on', 'off', 'pic', 'cw', 'ccw', or 'exit'.")

except KeyboardInterrupt:
    print("\nInterrupted by user.")

finally:
    GPIO.cleanup()
    picam2.stop()
    print("GPIO cleaned up. Program ended.")
