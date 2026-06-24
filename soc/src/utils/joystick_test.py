import pygame # type: ignore[import]
import time
import math

pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Joystick detected: {joystick.get_name()}")

while True:
    pygame.event.pump()

    x = joystick.get_axis(0)
    y = joystick.get_axis(1)

    # Avoid shake
    if abs(x) < 0.5 and abs(y) < 0.5:
        time.sleep(0.1)
        continue

    angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

    if 225 <= angle < 315:
        direction = "left"
    elif 45 <= angle < 135:
        direction = "right"
    elif angle >= 315 or angle < 45:
        direction = "up"
    elif 135 <= angle < 225:
        direction = "down"
    else:
        direction = "undefined"

    print(f"Angle: {angle:.1f}°, Direction: {direction}")

    time.sleep(0.1)  # 100 ms