# ./src/utils/config.py
"""
Application configuration module.

This module defines and centralizes all meta-parameters
used to control application behavior.
"""


# ---------- Default ----------
# MODE = "demo"
MODE = "full"

if MODE not in ("demo", "full"):
    raise ValueError(f"Invalid MODE '{MODE}'. Expected 'demo' or 'full'.")


# ---------- Pygame UI ----------

# color
RED_RGB = (255, 72, 72)     # FF4848
BLUE_RGB = (72, 197, 255)   # 48C5FF
WHITE_RGB = (236, 236, 236) # ECECEC
BLACK_RGB = (0,0,0)         # 000000
GRAY_RGB = (128,128,128)    # 808080
YELLOW_RGB = (255,255,0)    # FFFF00
SILVER_RGB = (192,192,192)  # C0C0C0

# screen size
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

# font size
FONT_SIZE = 48


# ---------- Instructions ----------

INSTRUCTIONS_COUNT = 7

if MODE == "demo":
    MIN_READING_TIME = 100  # participants must spend at least ~ms on each instruction page before they can proceed to the next
else:   # MODE = "full"
    MIN_READING_TIME = 1000


# ---------- Stimuli ----------

STIM_W = 122
STIM_H = 122

# Fixation cross size (independent from stimulus size)
CROSS_SIZE = 40

STIMULI_COUNT = 10
TARGETS_PER_BLOCK = 6
NON_TARGETS_BASE = 14
MAX_CONSECUTIVE_REPEATS = 3

if MODE == "demo":
    STIM_DISPLAY_TIME = 500
    ISI = 1000
    ISI_BEFORE_FIRST_TRIAL = 500
    PRACTICE1_COUNT, PRACTICE2_COUNT, PRACTICE3_COUNT = (10, 10, 10)
    BLOCK1_COUNT, BLOCK2_COUNT = (21, 21)
    BLOCK3_COUNT, BLOCK4_COUNT = (22, 22)
    BLOCK5_COUNT, BLOCK6_COUNT = (23, 23)
else:   # MODE = "full"
    STIM_DISPLAY_TIME = 500
    ISI = 2500
    ISI_BEFORE_FIRST_TRIAL = 500
    PRACTICE1_COUNT, PRACTICE2_COUNT, PRACTICE3_COUNT = (20, 20, 20)
    BLOCK1_COUNT, BLOCK2_COUNT = (21, 21)
    BLOCK3_COUNT, BLOCK4_COUNT = (22, 22)
    BLOCK5_COUNT, BLOCK6_COUNT = (23, 23)


# ---------- Feedback ----------

FB_W = 70  # feedback image width
FB_H = 70  # feedback image height

if MODE == "demo":
    FB_DURATION = 500
else:   # MODE == "full"
    FB_DURATION = 500


# ---------- Joystick Control ----------

dz_x = 0.5  # deadzone for x-axis
dz_y = 0.5  # deadzon for y-axis

js_mode = 2 # how many options can the joystick maps to
# js_mode = 4


# ---------- Other ----------
run_limit = 10000   # randomly draw the sequence at most ~ times (for 1/2/3-back stimuli sequence generation)


# ---------- Runtime Condition Assignment ----------
PID = None          # participant ID
LANGUAGE = None     # language (spanish / english)
GROUP = None        # group (pilot / control / cd / stroke / tumor / other)
SESSION = None      # session (s1-s9)
START_TIME = None   # global start time
GLOBAL_END_TIME = None  # global end time
MAPPING = 1         # mapping id

_is_fullscreen: bool = True             # fullscreen / window mode flag
dominant_hand = None        # "left" or "right"
hand_used = None   # "left" or "right"

# Block counters for CSV tracking
practice_block_count: int = 0           # Counter for practice blocks (p1, p2, p3...)
test_block_count: int = 0               # Counter for test blocks (b1, b2, b3...)
current_block_label: str | None = None  # Current block label (p1, b1, etc.)
