# ./src/utils/config.py
"""
Application configuration module.

This module defines and centralizes all meta-parameters
used to control application behavior.
"""

# ---------- Runtime Condition Assignment ----------
PID: str | None = None           # participant ID
LANGUAGE: str | None = None     # language (spanish / english)
GROUP: str | None = None        # group (pilot / control / cd / stroke / tumor / other)
SESSION: str | None = None      # session (s1-s9)
MAPPING: int | None = None       # MAPPING
TYPE: str | None = None          # practice or experimental
MODE: str | None = None          # actual or demo
START_TIME: str | None = None    # global start time
END_TIME: str | None = None      # global end time
RESULTS_FILE: str | None = None  # participant file results 
JOY_LOG_FILE: str | None = None  # participant joystick log
DH: str | None = None                   # participant's dominant hand (left / right)
UH: str | None = None                   # hand used during task (left / right)
joy_response: str | None = None         # latest joystick response label (left / right)

_is_fullscreen: bool = True             # fullscreen / window mode flag


# ---------- Pygame UI ----------

# color
RED_RGB = (255, 72, 72)     # FF4848
BLUE_RGB = (72, 197, 255)   # 48C5FF
COCO_RGB = "#C0C0C0"      # Text
BLACK_RGB = (0,0,0)         # 000000
GRAY_RGB = (0,0,0)    # 000000
YELLOW_RGB = (255,255,0)    # FFFF00
# FONT moved to paths.py
# screen size
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# font size
FONT_SIZE = 48
FONT_SMALL = 48

TASK: str = "SOC"

# ---------- MODE Settings ----------

def initialize_mode_settings():
    """Initialize settings that depend on MODE."""
    global MIN_READING_TIME, FB_DURATION, STIMULI_COUNT_PRAC, STIMULI_COUNT_EXPERIMENTAL
    
    if MODE == "demo":  
        MIN_READING_TIME = 10
        FB_DURATION = 500
        STIMULI_COUNT_PRAC = 1
        STIMULI_COUNT_EXPERIMENTAL = 1
    else:
        MIN_READING_TIME = 1000
        FB_DURATION = 1000
        STIMULI_COUNT_PRAC = 9
        STIMULI_COUNT_EXPERIMENTAL = 45 # 15 for each condition

NUM_BLOCKS = 4
VIDEOS_PER_COMBO = 20
PRACTICE_PER_COMBO = 1
TRIALS_PER_BLOCK = 5
MAX_RETRIES = 20000

# ---------- Instructions ----------

INSTRUCTIONS_COUNT = 27

# ---------- Stimuli ----------

MAX_RESPOND_TIME = 3000 # max time to respond to a stimulus (3 seconds)
FIXATION_CROSS = 500  # fixation duration in ms
FIXATION_CROSS_SIZE = 800  # fixation cross size in px

MAX_CONSEC_PLAYER = 2
MAX_CONSEC_CONDITION = 3
MAX_CONSEC_DIFFICULTY = 3


# ---------- Feedback ----------

FB_W = 80  # feedback image width
FB_H = 80  # feedback image height
PRACTICE1_PG = 7 
BLOCK1_PG = 11
BLOCK2_PG = 16
BLOCK3_PG = 21
BLOCK4_PG = 26
LAST_PG = 27

# ---------- Joystick Control ----------

dz_x = 0.60  # deadzone for x-axis
dz_y = 0.60  # deadzone for y-axis
DZ_X = dz_x  # uppercase alias used by joystick filters
DZ_Y = dz_y  # uppercase alias used by joystick filters

js_mode = 2 # how many options can the joystick maps to
