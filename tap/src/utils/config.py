# Mode
#MODE = "TEST" # For developing purposes
#MODE = "ACTUAL" # For actual tasks

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


# font size
FONT_SIZE = 48
FONT_SMALL = 48

TASK: str = "TAP"
USE_JOYSTICK: bool = False

INSTRUCTIONS_COUNT = 17


# ---------- MODE Settings ----------

def initialize_mode_settings():
    """Initialize settings that depend on MODE."""
    global MIN_READING_TIME, FB_DURATION, NUM_SYNCHRONIZED, NUM_SELF_PACE, FIXATION_CROSS
    
    if MODE == "demo":  
        MIN_READING_TIME = 1000
        FB_DURATION = 500
        FIXATION_CROSS = 250
        NUM_SYNCHRONIZED = 5 # Number of synchronized tappings
        NUM_SELF_PACE = 5 # Number of self pace tappings
    else:
        MIN_READING_TIME = 1000
        #FB_DURATION = 1000
        FB_DURATION = 2000
        FIXATION_CROSS = 500
        NUM_SYNCHRONIZED = 12 # Number of synchronized tappings
        NUM_SELF_PACE = 31 # Number of self pace tappings

# ---------- Instructions Settings ----------

PRACTICE_1 = 3 # practice 1 begins after page ~ [2 trial / left hand]
PRACTICE_2 = 5 # practice 2 begins after page ~ [2 trial / left hand]
BLOCK_1 = 8 # block 1 begins after page ~ [3 trial / left hand]
BLOCK_2 = 9 # block 2 begins after page ~ [3 trial / left hand]

# ---------- Trial Settings ----------

SYNCHRONIZED_INTERVAL = 550 # Interval between two stimuli (ms)
MIN_SELF_PACED_INTERVAL = 275 # Minimum interval between two self paced tappings to be considered "correct" (ms)
MAX_SELF_PACED_INTERVAL = 825 # Maximum interval between two self paced tappings to be considered "correct" (ms)
TREMOR_INTERVAL = 20 # Consequtive presses within this interval will be percieved as one (accidenal press due to tremor) (ms)
SELF_PACED_TIMEOUT = 30000 # Maximum time for self-paced phase (ms)

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
