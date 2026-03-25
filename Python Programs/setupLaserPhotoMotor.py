import RPi.GPIO as GPIO
import time
from picamzero import Camera
import os

# -------------------- Camera Setup --------------------
home_dir = os.environ['HOME']
save_dir = os.path.join(home_dir, "Desktop")

cam = Camera()
cam.start_preview()
cam.still_size = (500, 500)
cam.exposure = 10000

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
STEPS_PER_SMALL_REV = 500
STEPS_PER_HYPER_REV = 100
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

print("Commands:")
print(" - on / off     => Laser control")
print(" - pic            => Take photo")
print(" - cw / ccw     => Rotate motor clockwise / counterclockwise 2048 steps")
print(" - cws / ccws     => Rotate motor clockwise / counterclockwise 500 steps")
print(" - cwsh / ccwsh     => Rotate motor clockwise / counterclockwise 100 steps")
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
            filename = f"ECZIncubatorTestsmalla{img_count}.jpg"
            filepath = os.path.join(save_dir, filename)
            cam.take_photo(filepath)
            print(f"Captured {filename}")
            img_count += 1

        elif cmd == "cw":
            print("Rotating clockwise 2048 steps...")
            move_motor(STEPS_PER_REV, direction=1)

        elif cmd == "cws":
            print("Rotating clockwise 500 steps...")
            move_motor(STEPS_PER_SMALL_REV, direction=1)

        elif cmd == "cwsh":
            print("Rotating clockwise 100 steps...")
            move_motor(STEPS_PER_HYPER_REV, direction=1)

        elif cmd == "ccw":
            print("Rotating counterclockwise 2048 steps...")
            move_motor(STEPS_PER_REV, direction=-1)

        elif cmd == "ccws":
            print("Rotating counterclockwise 500 steps...")
            move_motor(STEPS_PER_SMALL_REV, direction=-1)

        elif cmd == "ccwsh":
            print("Rotating counterclockwise 100 steps...")
            move_motor(STEPS_PER_HYPER_REV, direction=-1)

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

