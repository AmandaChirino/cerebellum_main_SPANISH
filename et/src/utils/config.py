# ./src/utils/config.py
"""
Application configuration module.

This module defines and centralizes all meta-parameters
used to control application behavior.
"""

# ---------- Pygame UI ----------

# color
RED_RGB = (255, 72, 72)     # FF4848
BLUE_RGB = (72, 197, 255)   # 48C5FF
WHITE_RGB = (236, 236, 236) # ECECEC
BLACK_RGB = (0,0,0)         # 000000
COCO_RGB = '#C0C0C0'           # 808080
YELLOW_RGB = (255,255,0)    # FFFF00

# screen size
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900

# display where the window opens (0 = main display)
DISPLAY_INDEX = 0

# real window size in pixels, filled when the window is created
REAL_SCREEN_W: int | None = None
REAL_SCREEN_H: int | None = None

# font size
FONT_SIZE = 48
FONT_SMALL = 48

# slider: half of the bar length as a fraction of the screen HEIGHT (also sets the mouse travel)
SLIDER_HALF_LENGTH = 0.4

TASK: str = "ET"

INSTRUCTIONS_COUNT = 5

# ---------- Feedback ----------

FB_W = 200  # feedback image width
FB_H = 200  # feedback image height


# ---------- Joystick Control ----------

dz_x = 0.5  # deadzone for x-axis
dz_y = 0.5  # deadzon for y-axis

js_mode = 2 # how many options can the joystick maps to

# ---------- MODE Settings ----------

def initialize_mode_settings():
    """Initialize settings that depend on MODE."""
    global MIN_READING_TIME, FB_DURATION, STIMULI_COUNT_PRAC, STIMULI_COUNT_EXPERIMENTAL, FIXATION_CROSS
    
    if MODE == "demo":  
        MIN_READING_TIME = 10
        FB_DURATION = 500
        STIMULI_COUNT_PRAC = 1
        STIMULI_COUNT_EXPERIMENTAL = 1
        FB_DURATION = 500
        FIXATION_CROSS = 250
    else:
        MIN_READING_TIME = 1000
        FB_DURATION = 1000
        STIMULI_COUNT_PRAC = 9
        STIMULI_COUNT_EXPERIMENTAL = 45 # 15 for each condition
        FB_DURATION = 2000
        FIXATION_CROSS = 500

# ---------- Runtime Condition Assignment ----------
PID: str | None = None          # participant ID
LANGUAGE: str | None = None     # language (spanish / english)
GROUP: str | None = None        # group (pilot / control / cd / stroke / tumor / other)
SESSION: str | None = None      # session (s1-s9)
START_TIME: str | None = None   # global start time
MAPPING: int | None = None       # A or B
TYPE: str | None = None          # practice or experimental
MODE: str | None = None          # actual or demo
START_TIME: str | None = None    # global start time
END_TIME: str | None = None      # global end time
RESULTS_FILE: str | None = None  # participant file results 
DH: str | None = None                   # participant's dominant hand (left / right)
UH: str | None = None                   # hand used during task (left / right)

_is_fullscreen: bool = True             # fullscreen / window mode flag
dominant_hand: str | None = None        # "left" or "right"
less_affected_hand: str | None = None   # "left" or "right"
stimulus_set: str | None = None         # "A" or "B"
