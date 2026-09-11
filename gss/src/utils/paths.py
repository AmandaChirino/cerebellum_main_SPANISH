# ./src/utils/paths.py
"""
Centralized filesystem path definitions for experiment resources and outputs.
"""


from pathlib import Path

import utils.config as cfg


# ---------- Directories ----------

# project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# resources
RESOURCES_DIR = PROJECT_ROOT / "resources"

# results
RESULTS_DIR = PROJECT_ROOT / "results"

# logs
LOGS_DIR = PROJECT_ROOT / "logs"



# ---------- Load Instructions ----------

def _get_instruction_dir() -> Path:
    """Return the instruction directory for the active mapping."""
    assert cfg.MAPPING in [1, 2]
    return RESOURCES_DIR / ("instructions_v1" if cfg.MAPPING == 1 else "instructions_v2")


def load_instructions() -> tuple[list[Path], Path, Path, Path]:
    """
    Return instruction asset paths for the active mapping.

    Assets:
    - 1.png ~ 50.png
    - Accuracy_Block.png
    - Speed_Block.png
    - Varying_Block.png
    """
    instructions_dir = _get_instruction_dir()
    instructions = [instructions_dir / f"{i}.png" for i in range(1, 51)]
    accuracy_block = instructions_dir / "Accuracy_Block.png"
    speed_block = instructions_dir / "Speed_Block.png"
    varying_block = instructions_dir / "Varying_Block.png"
    return instructions, accuracy_block, speed_block, varying_block


def bind_instructions() -> None:
    """Bind current instruction assets to module globals."""
    instructions, accuracy_block, speed_block, varying_block = load_instructions()
    globals()["INSTRUCTIONS"] = instructions
    globals()["Accuracy_Block"] = accuracy_block
    globals()["Speed_Block"] = speed_block
    globals()["Varying_Block"] = varying_block
    for idx, path in enumerate(instructions, start=1):
        globals()[str(idx)] = path


# ---------- Load Feedback ----------

FEEDBACK_DIR = RESOURCES_DIR / "feedback"

FB_CORRECT = FEEDBACK_DIR / "correct.png"
FB_INCORRECT = FEEDBACK_DIR / "incorrect.png"

BEEP = FEEDBACK_DIR / "beep.wav"


# ---------- Load Admin (dynamic) ----------

# Read and bind all .png files under ADMINH_DIR; variable names
# match filenames (without extension). Example: Admin.png -> Admin
# This supports runtime composition rules (e.g., adding _Next, _1-6, _L/R).

ADMIN_DIR = RESOURCES_DIR / "admin"

def _bind_adminh_images():
    images = {}
    if ADMIN_DIR.exists():
        for path in ADMIN_DIR.glob('*.png'):
            var_name = path.stem  # filename without extension
            globals()[var_name] = path
            images[var_name] = path
    return images

ADMIN_IMAGES = _bind_adminh_images()


# ---------- Load Stimuli (letter-coded set) ----------

# Convention in ./resources/stimuli:
# - Word-color: "B/G/R/Y_B/G/R/Y.png" (e.g., B_G.png means BLUE written in GREEN)
# - X-color:    "X_B/G/R/Y.png" (e.g., X_G.png means X written in GREEN)
# - Ignore subfolder: ./resources/stimuli/goal
#
# Auto-generate module-level variables like:
#   BLUE_in_GREEN = PROJECT_ROOT / 'resources/stimuli/B_G.png'
#   X_in_BLUE     = PROJECT_ROOT / 'resources/stimuli/X_B.png'
# Also expose dictionaries for programmatic access:
#   WORD_COLOR_STIMULI[("BLUE", "GREEN")] -> Path(.../B_G.png)
#   X_COLOR_STIMULI["BLUE"]               -> Path(.../X_B.png)

STIMULI_DIR = RESOURCES_DIR / "stimuli"

_COLOR_LETTER_TO_NAME = {
    'B': 'BLUE',
    'G': 'GREEN',
    'R': 'RED',
    'Y': 'YELLOW',
}

def _build_letter_stimuli_maps():
    """Scan current stimuli folder and bind variables/dicts accordingly."""
    word_color = {}
    x_color = {}

    # Word-color pairs
    for path in STIMULI_DIR.glob('[BGRY]_[BGRY].png'):
        stem = path.stem  # e.g., 'B_G'
        try:
            word_letter, color_letter = stem.split('_', 1)
        except ValueError:
            continue
        word_name = _COLOR_LETTER_TO_NAME.get(word_letter)
        color_name = _COLOR_LETTER_TO_NAME.get(color_letter)
        if not word_name or not color_name:
            continue
        var_name = f"{word_name}_in_{color_name}"
        globals()[var_name] = path
        word_color[(word_name, color_name)] = path

    # X-color
    for path in STIMULI_DIR.glob('X_[BGRY].png'):
        stem = path.stem  # e.g., 'X_G'
        parts = stem.split('_', 1)
        if len(parts) != 2:
            continue
        _, color_letter = parts
        color_name = _COLOR_LETTER_TO_NAME.get(color_letter)
        if not color_name:
            continue
        var_name = f"X_in_{color_name}"
        globals()[var_name] = path
        x_color[color_name] = path

    return word_color, x_color

# Build on import
WORD_COLOR_STIMULI, X_COLOR_STIMULI = _build_letter_stimuli_maps()


# ---------- Goal Stimuli ----------

GOAL_DIR = STIMULI_DIR / "goal"

def _bind_goal_stimuli():
    goal = {}
    if GOAL_DIR.exists():
        for pattern in ('*.png', '*.jpg', '*.jpeg'):
            for path in GOAL_DIR.glob(pattern):
                var_name = path.stem
                globals()[var_name] = path
                goal[var_name] = path
    return goal

GOAL_STIMULI = _bind_goal_stimuli()
