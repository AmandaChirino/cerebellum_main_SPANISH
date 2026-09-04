# ./src/utils/config.py
"""
Centralized configuration constants for experiment parameters and runtime state.
"""

# ---------- Default ----------
MODE = "demo"       # quick testing
#MODE = "full"     # real participant runs


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

if MODE == "demo":
    MIN_READING_TIME = 100  # minimum time per instruction page before allowing next (ms)
else:   # MODE = "full"
    MIN_READING_TIME = 1000


# ---------- Stimuli ----------
if MODE == "demo":
    MAX_RESPONSE_TIME = 1000            # maximum response time (ms)
    ISI_DURATION = 500                  # inter-stimulus interval duration (ms)
    ITI_COUNTDOWN = 3                   # status report after each trial display duration (s)
    DISPLAY_GOAL_DURATION = 1000        # goal display duration (ms)

    COLOR_PRACTICE_COUNT = 5            # color practice number of trials
    STROOP_PRACTICE_COUNT = 5           # stroop practice number of trials

    INTERVAL_MIN = 3000                 # minimum time for an interval (ms)
    INTERVAL_MAX = 5000                 # maximum time for an interval (ms)
    INTERVAL_PRACTICE_COUNT = 2         # interval practice number of intervals
    
    SPEED_PRACTICE_COUNT = 1            # speed practice number of intervals
    ACCURACY_PRACTICE_COUNT = 1         # accuracy practice number of intervals
    VARYING_PRACTICE_SPEED_COUNT = 1    # varying practice (speed) number of intervals
    VARYING_PRACTICE_ACCURACY_COUNT = 1 # varying practice (accuracy) number of intervals

    SPEED_TEST_COUNT = 1                # speed test number of intervals
    ACCURACY_TEST_COUNT = 1             # accuracy test number of intervals
    VARYING_TEST_SPEED_COUNT = 1        # varying test (speed) number of intervals
    VARYING_TEST_ACCURACY_COUNT = 1     # varying test (accuracy) number of intervals

else:   # MODE = "full"
    MAX_RESPONSE_TIME = 3000
    ISI_DURATION = 500
    ITI_COUNTDOWN = 5
    DISPLAY_GOAL_DURATION = 2000

    COLOR_PRACTICE_COUNT = 60
    STROOP_PRACTICE_COUNT = 30

    INTERVAL_MIN = 8000
    INTERVAL_MAX = 12000
    INTERVAL_PRACTICE_COUNT = 4

    SPEED_PRACTICE_COUNT = 3
    ACCURACY_PRACTICE_COUNT = 3
    VARYING_PRACTICE_SPEED_COUNT = 2
    VARYING_PRACTICE_ACCURACY_COUNT = 2


# ---------- Full-Mode Test Intervals ----------
# Fixed test blocks (full mode): 3 intervals per duration (8–12 s), independently shuffled
# for Speed and Accuracy blocks, with no duration repeated more than twice consecutively.
import random

# Named durations for clarity
INTERVAL_8 = 8000
INTERVAL_9 = 9000
INTERVAL_10 = 10000
INTERVAL_11 = 11000
INTERVAL_12 = 12000

_deftries = 10000

def _is_valid_no_more_than_two_consecutive(seq: list[int]) -> bool:
    if not seq:
        return True
    run_val = seq[0]
    run_len = 1
    for v in seq[1:]:
        if v == run_val:
            run_len += 1
            if run_len > 2:
                return False
        else:
            run_val = v
            run_len = 1
    return True


def _shuffled_with_constraint(base: list[int], max_tries: int = _deftries) -> list[int]:
    arr = list(base)
    for _ in range(max_tries):
        random.shuffle(arr)
        if _is_valid_no_more_than_two_consecutive(arr):
            return list(arr)
    # Fallback: deterministic greedy construction to avoid deadlock
    counts = {}
    for v in base:
        counts[v] = counts.get(v, 0) + 1
    result: list[int] = []
    last1 = last2 = None
    while sum(counts.values()) > 0:
        # pick a value with remaining count that doesn't create 3-in-a-row
        candidates = [v for v, c in counts.items() if c > 0 and not (last1 == last2 == v)]
        if not candidates:
            # if impossible, just append any available to finish (will violate rule, but prevents hang)
            candidates = [v for v, c in counts.items() if c > 0]
        # choose the one with highest remaining count first to spread values
        candidates.sort(key=lambda v: (-counts[v], v))
        v = candidates[0]
        result.append(v)
        counts[v] -= 1
        last2, last1 = last1, v
    return result

# Build base list: 3 of each duration
_base_intervals = [
    INTERVAL_8, INTERVAL_8, INTERVAL_8,
    INTERVAL_9, INTERVAL_9, INTERVAL_9,
    INTERVAL_10, INTERVAL_10, INTERVAL_10,
    INTERVAL_11, INTERVAL_11, INTERVAL_11,
    INTERVAL_12, INTERVAL_12, INTERVAL_12,
]

# Independent randomized schedules for Speed and Accuracy tests (only in full mode)
if MODE == 'full':
    SPEED_TEST_INTERVALS = _shuffled_with_constraint(_base_intervals)
    ACCURACY_TEST_INTERVALS = _shuffled_with_constraint(_base_intervals)


# ---------- Full-Mode Varying Test Intervals ----------
# Two varying blocks together: 15 SPEED + 15 ACCURACY (3× each 8/9/10/11/12s).
# Each block has 15 mixed intervals. Distribution chosen uniformly among:
#   block1: 6S+9A / block2: 9S+6A
#   block1: 7S+8A / block2: 8S+7A
#   block1: 8S+7A / block2: 7S+8A
#   block1: 9S+6A / block2: 6S+9A
if MODE == "full":
    def _make_tokens(prefix: str) -> list[str]:
        return [
            f"{prefix}_INTERVAL_8", f"{prefix}_INTERVAL_8", f"{prefix}_INTERVAL_8",
            f"{prefix}_INTERVAL_9", f"{prefix}_INTERVAL_9", f"{prefix}_INTERVAL_9",
            f"{prefix}_INTERVAL_10", f"{prefix}_INTERVAL_10", f"{prefix}_INTERVAL_10",
            f"{prefix}_INTERVAL_11", f"{prefix}_INTERVAL_11", f"{prefix}_INTERVAL_11",
            f"{prefix}_INTERVAL_12", f"{prefix}_INTERVAL_12", f"{prefix}_INTERVAL_12",
        ]

    def _token_duration_ms(tok: str) -> int:
        try:
            return int(tok.split("_")[-1]) * 1000
        except Exception:
            return 0

    def _is_valid_varying(seq: list[str]) -> bool:
        # rule 1: no three consecutive same duration (ignore category)
        for i in range(len(seq) - 2):
            d1 = _token_duration_ms(seq[i])
            d2 = _token_duration_ms(seq[i+1])
            d3 = _token_duration_ms(seq[i+2])
            if d1 == d2 == d3:
                return False
        # rule 2: at most three consecutive same category
        run_cat = None
        run_len = 0
        for tok in seq:
            cat = 'SPEED' if tok.startswith('SPEED_') else ('ACCURACY' if tok.startswith('ACCURACY_') else '')
            if cat == run_cat:
                run_len += 1
                if run_len > 3:
                    return False
            else:
                run_cat = cat
                run_len = 1
        return True

    def _shuffle_varying_with_constraints(base: list[str], max_tries: int = _deftries) -> list[str]:
        arr = list(base)
        for _ in range(max_tries):
            random.shuffle(arr)
            if _is_valid_varying(arr):
                return list(arr)
        # Fallback: greedy construction
        counts: dict[str, int] = {}
        for t in base:
            counts[t] = counts.get(t, 0) + 1
        result: list[str] = []
        last1: str | None = None
        last2: str | None = None
        while sum(counts.values()) > 0:
            def ok(tok: str) -> bool:
                tmp = (result[-2:] if len(result) >= 2 else result[:]) + [tok]
                # duration rule
                if len(tmp) >= 3:
                    d1 = _token_duration_ms(tmp[-1])
                    d2 = _token_duration_ms(tmp[-2])
                    d3 = _token_duration_ms(tmp[-3])
                    if d1 == d2 == d3:
                        return False
                # category rule
                cat = 'SPEED' if tok.startswith('SPEED_') else 'ACCURACY'
                c1 = 'SPEED' if (last1 and last1.startswith('SPEED_')) else ('ACCURACY' if last1 else None)
                c2 = 'SPEED' if (last2 and last2.startswith('SPEED_')) else ('ACCURACY' if last2 else None)
                if cat == c1 == c2:
                    return False
                return True
            candidates = [t for t,c in counts.items() if c > 0 and ok(t)]
            if not candidates:
                candidates = [t for t,c in counts.items() if c > 0]
            candidates.sort(key=lambda t: (-counts[t], _token_duration_ms(t)))
            t = candidates[0]
            result.append(t)
            counts[t] -= 1
            last2, last1 = last1, t
        return result

    # Build pools
    _speed_pool = _make_tokens('SPEED')
    _acc_pool = _make_tokens('ACCURACY')

    # Choose allocation
    _alloc = random.choice([(6,9,9,6), (7,8,8,7), (8,7,7,8), (9,6,6,9)])
    _s1, _a1, _s2, _a2 = _alloc

    def _draw_from_pool(pool: list[str], k: int) -> list[str]:
        chosen: list[str] = []
        for _ in range(k):
            idx = random.randrange(len(pool))
            chosen.append(pool.pop(idx))
        return chosen

    _b1 = _draw_from_pool(_speed_pool, _s1) + _draw_from_pool(_acc_pool, _a1)
    _b2 = _draw_from_pool(_speed_pool, _s2) + _draw_from_pool(_acc_pool, _a2)

    VARYING1_TEST_INTERVALS: list[str] = _shuffle_varying_with_constraints(_b1)
    VARYING2_TEST_INTERVALS: list[str] = _shuffle_varying_with_constraints(_b2)


# ---------- Feedback ----------

FB_W = 100  # feedback image width (px)
FB_H = 100  # feedback image height (px)

if MODE == "demo":
    FB_DURATION = 1000          # feedback duration (ms)
    FB_SCREEN_DURATION = 2000   # feedback screen display duration (ms) (for intervals)
else:   # MODE == "full"
    FB_DURATION = 1000
    FB_SCREEN_DURATION = 5000


# ---------- Joystick Control ----------

DZ_X = 0.6      # deadzone for x-axis ([0,1])
DZ_Y = 0.6      # deadzone for y-axis ([0,1])

# JOY_MODE = 2    # number of discrete joystick directions
JOY_MODE = 4


# ---------- Runtime State ----------

PID: str | None = None                  # participant ID
MAPPING: int | None = None              # task mapping (1 / 2)
START_TIME: str | None = None           # task start time (ISO format)

global_start_time: str | None = None    # whole-task start time (ISO)
global_end_time: str | None = None      # whole-task end time (ISO)

# Admin
GROUP: int | None = None                # participant's group
SESSION: int | None = None              # participant's session
DH: str | None = None                   # participant's dominant hand (left / right)
UH: str | None = None                   # hand used during task (left / right)

_is_fullscreen: bool = True             # current fullscreen state
_input_source: str | None = None        # response input source (key = keyboard / joy = joystick)
_start_time: str | None = None          # block start time (ISO format)
_end_time: str | None = None            # block end time (ISO format)
key_response: str | None = None         # actual keyboard key pressed
joy_response: str | None = None         # actual joystick direction
version: int | None = None              # PID-derived version (0-15)

# ---------- Start From Mapping ----------
# Map task names to the last instruction page before that task begins
# Names follow the doc order: color_practice → … → varying_practice → run_test
START_FROM_PAGES = {
    'color_practice': 10,
    'stroop_practice': 18,
    'interval_practice': 22,
    'speed_practice': 28,
    'accuracy_practice': 32,
    'varying_practice': 36,
    'run_test': 40,
    'end': 50,
}

# Use string name to choose where to start; None means from the beginning
start_from = None
# start_from = "color_practice"
# start_from = "stroop_practice"
# start_from = "interval_practice"
# start_from = "speed_practice"
# start_from = "accuracy_practice"
# start_from = "varying_practice"
# start_from = "run_test"


# ---------- Task Sequences ----------
# Each item is a 4-step goal sequence using codes:
#   S = Speed, A = Accuracy, V = Varying
TASK_SEQUENCES: list[tuple[str, str, str, str]] = [
    ("S","A","V","V"),
    ("S","V","A","V"),
    ("S","V","V","A"),
    ("A","S","V","V"),
    ("A","V","S","V"),
    ("A","V","V","S"),
    ("V","S","A","V"),
    ("V","S","V","A"),
    ("V","A","S","V"),
    ("V","A","V","S"),
    ("V","V","S","A"),
    ("V","V","A","S"),
]

# Selected sequence for current run (set after version is derived)
task_sequence: tuple[str, str, str, str] | None = None

# ---------- Color-to-Direction Mapping (JOY_MODE==4) ----------
# Base mapping is mapping 1; MAPPING==2 flips left↔right and up↔down.
COLOR_TO_DIR = {
    "BLUE": "left",
    "GREEN": "down",
    "RED": "right",
    "YELLOW": "up",
}

def expected_dir_for_color(color: str) -> str:
    d = COLOR_TO_DIR.get(color)
    if d is None:
        return "NA"
    if MAPPING == 2:
        flip = {"left": "right", "right": "left", "up": "down", "down": "up"}
        return flip.get(d, d)
    return d
