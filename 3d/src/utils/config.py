# ./src/utils/config.py
"""
Centralized configuration constants for experiment parameters and runtime state.
"""


# ---------- Default ----------
#MODE = "demo"       # quick testing
MODE = "full"     # real participant runs


# ---------- Pygame UI ----------

# color
RED_RGB = (255, 72, 72)     # #FF4848
BLUE_RGB = (72, 197, 255)   # #48C5FF
WHITE_RGB = (236, 236, 236) # #ECECEC
COCO_RGB = (192, 192, 192)  # #C0C0C0
BLACK_RGB = (0, 0, 0)       # #000000
GRAY_RGB = (128, 128, 128)  # #808080
YELLOW_RGB = (255, 255, 0)  # #FFFF00

# screen size
SCREEN_W = 1280 # screen width (px)
SCREEN_H = 720  # screen height (px)

# font size
FONT_SMALL = 48 # body text (px)
FONT_LARGE = 72 # titles (px)


# ---------- Instructions ----------

INSTRUCTIONS_COUNT = 22

if MODE == "demo":
    MIN_READING_TIME = 100  # minimum time per instruction page before allowing next (ms)
else:   # MODE = "full"
    MIN_READING_TIME = 1000



# ---------- Stimuli ----------

STIMULI_COUNT = 5

if MODE == "demo":
    MAX_RESPONSE_TIME = 1000    # maximum response time (ms)
    FIXATION_CROSS = 500        # fixation cross duration (ms)
    ISI = 500                   # inter stimulus interval (ms)
else:   # MODE = "full"
    MAX_RESPONSE_TIME = 3000
    FIXATION_CROSS = 500
    ISI = 500



# ---------- Feedback ----------

FB_W = 80  # feedback image width (px)
FB_H = 80  # feedback image height (px)

if MODE == "demo":
    FB_DURATION = 500   # feedback duration (ms)
else:   # MODE == "full"
    FB_DURATION = 2000



# ---------- Joystick Control ----------

DZ_X = 0.6      # deadzone for x-axis ([0,1])
DZ_Y = 0.6      # deadzone for y-axis ([0,1])

JOY_MODE = 2    # number of discrete joystick directions
# JOY_MODE = 4


# ---------- Runtime State ----------
PID: str | None = None                  # participant ID
MAPPING: int | None = None              # task mapping (1 / 2)
COUNTERBALANCE_REMAINDER: int | None = None  # PID suffix mod 4 (0 / 1 / 2 / 3)
DH: str | None = None                   # participant's dominant hand (left / right)
UH: str | None = None                   # hand used during task (left / right)
GROUP: int | None = None                # group index (1..6)
SESSION: int | None = None              # session index (1..6)
START_TIME: str | None = None           # task start time (ISO format)

_is_fullscreen: bool = True         # current fullscreen state
_input_source: str | None = None    # response input source (key = keyboard / joy = joystick)
_start_time: str | None = None      # block start time (ISO format)
_end_time: str | None = None        # block end time (ISO format)
key_response: str | None = None     # actual keyboard key pressed
joy_response: str | None = None     # actual joystick direction
