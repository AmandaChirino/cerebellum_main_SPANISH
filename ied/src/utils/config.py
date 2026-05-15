# ./src/utils/config.py
"""
Application configuration module.

This module defines and centralizes all meta-parameters
used to control application behavior.
"""

from pathlib import Path


# ---------- Default ----------
# Select "demo" mode for testing purposes, "full" mode for deployment
#MODE = "demo"
MODE = "full"

if MODE not in ("demo", "full"):
    raise ValueError(f"Invalid MODE '{MODE}'. Expected 'demo' or 'full'.")


# ---------- Runtime condition assignment ----------
_is_fullscreen: bool = True         # full screen / window mode marker
PID: str | None = None              # participant id
LANGUAGE: str | None = None        # language (spanish / english)
GROUP: str | None = None           # group (pilot / control / cd / stroke / tumor / other)
SESSION: str | None = None         # session (s1-s9)
MAPPING: int | None = 1             # single mapping only (no MAPPING grouping)
START_TIME: str | None = None       # global start time
GLOBAL_END_TIME: str | None = None  # global end time
RESULTS_DATE: str | None = None     # yyyy_mm_dd for results filename
RESULTS_FILENAME: str | None = None # actual results filename (with suffix if needed)

PHASE_START_TIME: str | None = None # current phase start time
PHASE_END_TIME: str | None = None   # current phase end time

dominant_hand: str | None = None    # "left" or "right"
hand_used: str | None = None        # "left" or "right"

correct_ind: int | None = None      # correct answer for the current trial
correct_count: int | None = None    # temporary count of continuous correct answers
trial_count: int | None = None      # number of trials made for the current phase
force_quit: bool = False            # if true -> end the task


# ---------- Directories ----------

# project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# resources
RESOURCES_DIR = BASE_DIR / "resources"

# results
RESULTS_DIR = BASE_DIR / "results"

# logs
LOGS_DIR = BASE_DIR / "logs"


# ---------- Pygame UI settings ----------

# color
RED_RGB = (255, 72, 72)     # FF4848
BLUE_RGB = (72, 197, 255)   # 48C5FF
WHITE_RGB = (236, 236, 236) # ECECEC
BLACK_RGB = (0, 0, 0)       # 000000
GRAY_RGB = (128, 128, 128)  # 808080
YELLOW_RGB = (255, 255, 0)  # FFFF00
COCO_RGB = (192, 192, 192)  # C0C0C0

# screen size
SCREEN_WIDTH = 1516
SCREEN_HEIGHT = 852

# font size
FONT_SIZE = 48
LARGE_FONT_SIZE = 72

# admin page transition
ADMIN_PREPLAY_BLACKOUT_MS = 500

# block size (for 4 blocks containing stimuli)
RECT_W = 300
RECT_H = 200
BORDER_PX = 2


# ---------- Instructions settings ----------
INSTRUCTION_COUNT = 26
PRACTICE1 = 10
PRACTICE2 = 18
PHASES = 25

if MODE == "demo":
    MIN_READING_TIME = 100      # Minimum reading time to spend on each instruction page
    FINAL_INSTRUCTION_TIMEOUT_MS = 1000
else:
    MIN_READING_TIME = 1000
    FINAL_INSTRUCTION_TIMEOUT_MS = 10000


# ---------- Stimulus settings ----------
PHASE_COUNT = 9     # total number of phases

if MODE == "demo":
    ISI_MS = 500                    # inter-stimulus interval (ms)
    PRACTICE_TRIAL_REQUIREMENT = 5  # ~ trials for each practice phase
    CORRECT_REQUIREMENT = 3         # ~ correct answers in a row to proceed
    FORCE_QUIT_LIMIT = 10           # auto end after ~ trials
else:
    ISI_MS = 1000
    PRACTICE_TRIAL_REQUIREMENT = 20
    CORRECT_REQUIREMENT = 6
    FORCE_QUIT_LIMIT = 50


# ---------- Feedback settings ----------
if MODE == "demo":
    FB_DURATION = 500      # feedback duration
    FE_FB_DURATION = 1000   # first-error feedback duration
else:
    FB_DURATION = 1000
    FE_FB_DURATION = 3000


# ---------- Joystick Control ----------
DZ_X = 0.6  # deadzone for x-axis
DZ_Y = 0.6  # deadzone for y-axis

JS_MODE = 4  # joystick supports up/down/left/right (dual input source)
