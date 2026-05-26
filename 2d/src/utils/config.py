# ./src/utils/config.py
"""
Centralized configuration constants for experiment parameters and runtime state.
"""


# ---------- Default ----------
#MODE = "demo"       # quick testing
MODE = "full"         # real participant runs


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

TOTAL_INSTRUCTION_PAGES = 28
DEMO_MIN_READING_TIME = 100
FULL_MIN_READING_TIME = 1000
MIN_READING_TIME = DEMO_MIN_READING_TIME if MODE.lower() == "demo" else FULL_MIN_READING_TIME



# ---------- Stimuli ----------

if MODE == "demo":
    MAX_RESPONSE_TIME = 3000    # maximum response time (ms)
else:   # MODE = "full"
    MAX_RESPONSE_TIME = 5000

FIXATION_CROSS = 1000           # fixation cross duration (ms)
ISI_TIME = 500                  # blank interval between trials (ms)



# ---------- Feedback ----------

FB_W = 80  # feedback image width (px)
FB_H = 80  # feedback image height (px)

if MODE == "demo":
    FB_DURATION = 500   # feedback duration (ms)
else:   # MODE == "full"
    FB_DURATION = 1000



# ---------- Joystick Control ----------

DZ_X = 0.5      # deadzone for x-axis ([0,1])
DZ_Y = 0.5      # deadzone for y-axis ([0,1])

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


def key_for_option(option: int) -> str:
    """
    Map abstract response option to keyboard key according to mapping.

    mapping 1: option_1 -> d, option_2 -> k
    mapping 2: option_1 -> k, option_2 -> d
    """
    mapping = MAPPING if MAPPING in (1, 2) else 1
    if option not in (1, 2):
        raise ValueError(f"Unsupported option: {option}")

    if mapping == 1:
        return "d" if option == 1 else "k"
    return "k" if option == 1 else "d"


def option_for_key(key_name: str) -> int:
    """
    Map keyboard key name to abstract response option according to mapping.
    """
    mapping = MAPPING if MAPPING in (1, 2) else 1
    if key_name not in ("d", "k"):
        raise ValueError(f"Unsupported key: {key_name}")

    if mapping == 1:
        return 1 if key_name == "d" else 2
    return 2 if key_name == "d" else 1


def joy_for_key(key_name: str) -> str:
    """
    Joystick direction corresponding to keyboard key.
    d -> left, k -> right
    """
    if key_name == "d":
        return "left"
    if key_name == "k":
        return "right"
    raise ValueError(f"Unsupported key: {key_name}")
