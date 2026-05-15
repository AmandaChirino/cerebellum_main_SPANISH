# ./src/utils/config.py
"""
Centralized configuration constants for experiment parameters and runtime state.
"""


# ---------- Default ----------
# MODE = "demo"       # quick testing
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

INSTRUCTIONS_COUNT = 5

if MODE == "demo":
    READ_TIME = 100  # minimum time spent on each instruction page (ms)
else:   # MODE = "full"
    READ_TIME = 1000

LAST_INSTRUCTION_AUTO_EXIT_DEMO_MS = 1000
LAST_INSTRUCTION_AUTO_EXIT_FULL_MS = 10000
if MODE == "demo":
    LAST_INSTRUCTION_AUTO_EXIT_MS = LAST_INSTRUCTION_AUTO_EXIT_DEMO_MS
else:
    LAST_INSTRUCTION_AUTO_EXIT_MS = LAST_INSTRUCTION_AUTO_EXIT_FULL_MS



# ---------- Stimuli ----------

STIMULI_COUNT = 5

if MODE == "demo":
    MAX_RESPONSE_TIME = 1000    # maximum response time (ms)
    FIXATION_CROSS = 500        # fixation cross duration (ms)
else:   # MODE = "full"
    MAX_RESPONSE_TIME = 3000
    FIXATION_CROSS = 500



# ---------- Feedback ----------

FB_W = 200  # feedback image width (px)
FB_H = 200  # feedback image height (px)
FB_MAX_DURATION = 2000  # max non-blocking feedback overlay duration (ms)

if MODE == "demo":
    FB_DURATION = 500   # feedback duration (ms)
else:   # MODE == "full"
    FB_DURATION = 1000


# ---------- Trial Settings [Motor] ----------

M_MIN_FIXATION_TIME = 800 # Minimum fixation time [Motor]
M_MAX_FIXATION_TIME = 1200 # Maximum fixation time [Motor]
M_AVG_FIXATION_TIME = (M_MIN_FIXATION_TIME + M_MAX_FIXATION_TIME) // 2 # Average fixation time [Motor]
if MODE == "demo":
    M_RESPONSE_TIME = 500 # Response time [Motor]
    M_ISI_TIME = 250 # ISI time [Motor]
else:
    M_RESPONSE_TIME = 2000 # Response time [Motor]
    M_ISI_TIME = 500 # ISI time [Motor]


# ---------- Trial Settings [Sensorimotor] ----------

SM_MIN_FIXATION_TIME = 800 # Minimum fixation time [Sensorimotor]
SM_MAX_FIXATION_TIME = 1200 # Maximum fixation time [Sensorimotor]
SM_AVG_FIXATION_TIME = (SM_MIN_FIXATION_TIME + SM_MAX_FIXATION_TIME) // 2 # Average fixation time [Sensorimotor]
if MODE == "demo":
    SM_RESPONSE_TIME = 500 # Response time [Sensorimotor]
    SM_ISI_TIME = 250 # ISI time [Sensorimotor]
else:
    SM_RESPONSE_TIME = 2000 # Response time [Sensorimotor]
    SM_ISI_TIME = 500 # ISI time [Sensorimotor]


# ---------- Trial Counts [Motor] ----------

if MODE == "demo":
    PRACTICE1_NUM_BLUE = 2
    PRACTICE1_NUM_NOGO = 2

    BLOCK1_NUM_BLUE = 3
    BLOCK1_NUM_NOGO = 1

    PRACTICE2_NUM_RED = 2
    PRACTICE2_NUM_NOGO = 2

    BLOCK2_NUM_RED = 3
    BLOCK2_NUM_NOGO = 1
    
else:
    PRACTICE1_NUM_BLUE = 10
    PRACTICE1_NUM_NOGO = 2

    BLOCK1_NUM_BLUE = 30
    BLOCK1_NUM_NOGO = 3

    PRACTICE2_NUM_RED = 10
    PRACTICE2_NUM_NOGO = 2

    BLOCK2_NUM_RED = 30
    BLOCK2_NUM_NOGO = 3


# ---------- Trial Counts [Sensorimotor] ----------

if MODE == "demo":
    PRACTICE3_NUM_RED = 2
    PRACTICE3_NUM_BLUE = 2
    PRACTICE3_NUM_NOGO = 2

    BLOCK3_NUM_RED = 2
    BLOCK3_NUM_BLUE = 2
    BLOCK3_NUM_NOGO = 1

    BLOCK4_NUM_RED = 2
    BLOCK4_NUM_BLUE = 2
    BLOCK4_NUM_NOGO = 1

else:
    PRACTICE3_NUM_RED = 10
    PRACTICE3_NUM_BLUE = 10
    PRACTICE3_NUM_NOGO = 4

    BLOCK3_NUM_RED = 15
    BLOCK3_NUM_BLUE = 15
    BLOCK3_NUM_NOGO = 3

    BLOCK4_NUM_RED = 15
    BLOCK4_NUM_BLUE = 15
    BLOCK4_NUM_NOGO = 3


# ---------- Instruction Pages ----------

# Motor
PRACTICE1_PAGE = 5 # Practice 1 begins after page ~
BLOCK1_PAGE = 8 # Block 1 begins after page ~
PRACTICE2_PAGE = 13 # Practice 2 begins after page ~
BLOCK2_PAGE = 16 # Block 2 begins after page ~

# Sensorimotor
PRACTICE3_PAGE = 22 # Practice 3 begins after page ~
BLOCK3_PAGE = 25 # Block 3 begins after page ~
BLOCK4_PAGE = 28 # Block 4 begins after page ~
END_PAGE = 29 # Task ends after page ~

# ---------- Joystick Control ----------

DZ_X = 0.60      # deadzone for x-axis ([0,1])
DZ_Y = 0.60      # deadzone for y-axis ([0,1])

JOY_MODE = 2    # number of discrete joystick directions
# JOY_MODE = 4


# ---------- Runtime State ----------
PID: str | None = None                  # participant ID
LANGUAGE: str | None = None            # language (spanish / english)
GROUP: str | None = None               # group (pilot / control / cd / stroke / tumor / other)
SESSION: str | None = None             # session (s1-s9)
MAPPING: int | None = None              # task mapping (1 / 2)
DH: str | None = None                   # participant's dominant hand (left / right)
UH: str | None = None                   # hand used during task (left / right)
START_TIME: str | None = None           # task start time (ISO format)

_is_fullscreen: bool = True         # current fullscreen state
_input_source: str | None = None    # response input source (key = keyboard / joy = joystick)
_start_time: str | None = None      # block start time (ISO format)
_end_time: str | None = None        # block end time (ISO format)
key_response: str | None = None     # actual keyboard key pressed
joy_response: str | None = None     # actual joystick direction
