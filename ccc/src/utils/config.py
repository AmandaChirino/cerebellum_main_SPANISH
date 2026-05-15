"""
Centralized configuration constants and runtime state.
"""


# ---------- Default ----------
# MODE = "demo"       # quick testing
MODE = "full"     # real participant runs


# ---------- Pygame UI ----------

RED_RGB = (255, 72, 72)
BLUE_RGB = (72, 197, 255)
WHITE_RGB = (236, 236, 236)
COCO_RGB = (192, 192, 192)
BLACK_RGB = (0, 0, 0)
GRAY_RGB = (128, 128, 128)
YELLOW_RGB = (255, 255, 0)

SCREEN_W = 1280
SCREEN_H = 720

FONT_SMALL = 48
FONT_LARGE = 72
FONT_TOO_LATE = 60


# ---------- Instructions ----------

MIN_READING_TIME = 100 if MODE == "demo" else 1000

INSTRUCTION_TASK_ORDER = (
    "phonetic_task_practice",
    "phonetic_task_experimental",
    "orthographic_task_practice",
    "orthographic_task_experimental",
    "multi_task_practice",
    "multi_task_experimental_block_1",
    "multi_task_experimental_block_2",
)

# Mapping table used across the app:
# 1: phonetic -> orthographic, left=vowel/lower,           List 1 -> List 2
# 2: phonetic -> orthographic, left=consonant/upper,       List 1 -> List 2
# 3: orthographic -> phonetic, left=vowel/lower,           List 1 -> List 2
# 4: orthographic -> phonetic, left=consonant/upper,       List 1 -> List 2
# 5: phonetic -> orthographic, left=vowel/lower,           List 2 -> List 1
# 6: phonetic -> orthographic, left=consonant/upper,       List 2 -> List 1
# 7: orthographic -> phonetic, left=vowel/lower,           List 2 -> List 1
# 8: orthographic -> phonetic, left=consonant/upper,       List 2 -> List 1
#
# In the multi-task phases, List 1 and List 2 correspond directly to
# multi_task_experimental_block_1 and multi_task_experimental_block_2.

MAPPINGS_PHONETIC_FIRST = {1, 2, 5, 6}
MAPPINGS_ORTHOGRAPHIC_FIRST = {3, 4, 7, 8}
MAPPINGS_LEFT_VOWEL_LOWER = {1, 3, 5, 7}
MAPPINGS_LEFT_CONSONANT_UPPER = {2, 4, 6, 8}
MAPPINGS_LIST1_THEN_LIST2 = {1, 2, 3, 4}
MAPPINGS_LIST2_THEN_LIST1 = {5, 6, 7, 8}


def mapping_is_phonetic_first(mapping: int) -> bool:
    return mapping in MAPPINGS_PHONETIC_FIRST


def mapping_left_is_vowel_lower(mapping: int) -> bool:
    return mapping in MAPPINGS_LEFT_VOWEL_LOWER


def mapping_uses_list2_first(mapping: int) -> bool:
    return mapping in MAPPINGS_LIST2_THEN_LIST1


# "start task right after X.png"
# Mappings 5-8 use the same instruction pages as 1-4 because the instruction
# images do not encode the List 1/List 2 order; that order is applied in
# experiment_flow.py when the multi-task blocks are scheduled.
INSTRUCTION_TASK_AFTER_PNG_BY_MAPPING = {
    1: (8, 11, 20, 23, 34, 37, 40),
    2: (8, 11, 20, 23, 34, 37, 40),
    3: (20, 23, 8, 11, 34, 37, 40),
    4: (20, 23, 8, 11, 34, 37, 40),
    5: (8, 11, 20, 23, 34, 37, 40),  # phonetic first, blocks reversed
    6: (8, 11, 20, 23, 34, 37, 40),  # phonetic first, blocks reversed
    7: (20, 23, 8, 11, 34, 37, 40),  # orthographic first, blocks reversed
    8: (20, 23, 8, 11, 34, 37, 40),  # orthographic first, blocks reversed
}

# Block labels for the CSV output.
# multi_task_experimental_block_1 = List 1
# multi_task_experimental_block_2 = List 2
# b3 = first multi-task experimental block presented, b4 = second.
# For mappings 5-8, List 2 is presented before List 1 in experiment_flow.py.
_MAPPING_PHONETIC_FIRST = {
    "phonetic_task_practice":           "p1",
    "phonetic_task_experimental":        "b1",
    "orthographic_task_practice":        "p2",
    "orthographic_task_experimental":    "b2",
    "multi_task_practice":               "p3",
    "multi_task_experimental_block_1":   "b3",
    "multi_task_experimental_block_2":   "b4",
}
_MAPPING_ORTHOGRAPHIC_FIRST = {
    "orthographic_task_practice":        "p1",
    "orthographic_task_experimental":    "b1",
    "phonetic_task_practice":            "p2",
    "phonetic_task_experimental":        "b2",
    "multi_task_practice":               "p3",
    "multi_task_experimental_block_1":   "b3",
    "multi_task_experimental_block_2":   "b4",
}
BLOCK_LABEL_BY_MAPPING = {
    1: _MAPPING_PHONETIC_FIRST,
    2: _MAPPING_PHONETIC_FIRST,
    3: _MAPPING_ORTHOGRAPHIC_FIRST,
    4: _MAPPING_ORTHOGRAPHIC_FIRST,
    5: _MAPPING_PHONETIC_FIRST,
    6: _MAPPING_PHONETIC_FIRST,
    7: _MAPPING_ORTHOGRAPHIC_FIRST,
    8: _MAPPING_ORTHOGRAPHIC_FIRST,
}


# ---------- Stimuli ----------

# Scale factor for stimulus images (1.0 = native size, 0.5 = half size).
# Change STIM_SCALE here to make stimuli larger or smaller.
STIM_SCALE = 0.75

if MODE == "demo":
    MAX_RESPONSE_TIME_SINGLE = 1000
    MAX_RESPONSE_TIME_MULTI  = 1000
    FIXATION_CROSS_TIME = 1000
    ISI_TIME = 500
else:
    MAX_RESPONSE_TIME_SINGLE = 4000
    MAX_RESPONSE_TIME_MULTI  = 4000
    FIXATION_CROSS_TIME = 1000
    ISI_TIME = 500


# ---------- Feedback ----------

FB_W = 100
FB_H = 100
FB_DURATION = 1000


# ---------- Joystick ----------

DZ_X = 0.5
DZ_Y = 0.5
JOY_MODE = 2


# ---------- Runtime State ----------

PID: str | None = None
LANGUAGE: str | None = None            # language (spanish / english)
GROUP: str | None = None               # group (pilot / control / cd / stroke / tumor / other)
SESSION: str | None = None             # session (s1-s9)
MAPPING: int | None = None              # 1 .. 8
DH: str | None = None
UH: str | None = None

START_TIME: str | None = None
GLOBAL_END_TIME: str | None = None

_is_fullscreen: bool = True
_input_source: str | None = None        # key / joy
_start_time: str | None = None
_end_time: str | None = None
key_response: str | None = None
joy_response: str | None = None
