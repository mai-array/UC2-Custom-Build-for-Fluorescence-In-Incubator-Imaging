from picamera2 import Picamera2
import time

# -------------------- Sensor parameters (IMX219) --------------------
SENSOR_WIDTH = 3280
SENSOR_HEIGHT = 2464

# Initial ROI guess 
ROI_SIZE = 1000
ROI_X = (SENSOR_WIDTH - ROI_SIZE) // 2
ROI_Y = (SENSOR_HEIGHT - ROI_SIZE) // 2

# Movement controls
STEP = 20
ROI_MIN = 400
ROI_MAX = 2000

# -------------------- Camera Setup --------------------
picam2 = Picamera2()

picam2.configure(
    picam2.create_preview_configuration(
        main={"size": (800, 800)}
    )
)

picam2.start()

picam2.set_controls({
    "ScalerCrop": (ROI_X, ROI_Y, ROI_SIZE, ROI_SIZE),
    "ExposureTime": 10000,
    "AnalogueGain": 1.0,
    "AwbEnable": False
})

print("\n=== ROI CALIBRATION MODE ===")
print("w/s : move up / down")
print("a/d : move left / right")
print("+/- : resize ROI")
print("p   : print ROI values")
print("q   : quit\n")

# -------------------- Calibration Loop --------------------
while True:
    cmd = input("calib> ").strip().lower()

    if cmd == "w":
        ROI_Y = max(0, ROI_Y - STEP)
    elif cmd == "s":
        ROI_Y = min(SENSOR_HEIGHT - ROI_SIZE, ROI_Y + STEP)
    elif cmd == "a":
        ROI_X = max(0, ROI_X - STEP)
    elif cmd == "d":
        ROI_X = min(SENSOR_WIDTH - ROI_SIZE, ROI_X + STEP)
    elif cmd == "+":
        ROI_SIZE = min(ROI_MAX, ROI_SIZE + STEP)
    elif cmd == "-":
        ROI_SIZE = max(ROI_MIN, ROI_SIZE - STEP)
    elif cmd == "p":
        print(f"\nFINAL ROI → ({ROI_X}, {ROI_Y}, {ROI_SIZE}, {ROI_SIZE})\n")
        continue
    elif cmd == "q":
        print("\nExiting calibration.")
        break
    else:
        continue

    picam2.set_controls({
        "ScalerCrop": (ROI_X, ROI_Y, ROI_SIZE, ROI_SIZE)
    })

    print(f"ROI updated → ({ROI_X}, {ROI_Y}, {ROI_SIZE}, {ROI_SIZE})")

picam2.stop()
