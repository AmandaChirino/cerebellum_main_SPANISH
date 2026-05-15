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

# instructions
INSTRUCTIONS_DIR = RESOURCES_DIR / "instructions_v1"
INSTRUCTIONS_REVERSED_DIR = RESOURCES_DIR / "instructions_v2"

# stimuli
STIMULI_DIR = RESOURCES_DIR / "stimuli"



# # ---------- Load Instructions (single version) ----------

# INSTRUCTIONS_DIR = RESOURCES_DIR / "instructions"
# INSTRUCTIONS = []
# for i in range(cfg.INSTRUCTIONS_COUNT):
#     INSTRUCTIONS.append(INSTRUCTIONS_DIR / f"{i+1}.png")

# PRACTICE_INSTRUCTION = INSTRUCTIONS_DIR / "practice.png"
# TEST_INSTRUCTION = INSTRUCTIONS_DIR / "test.png"


# ---------- Load Instructions (multiple versions) ----------

def _instruction_root(mapping: int | None = None) -> Path:
    if mapping is None:
        mapping = cfg.MAPPING
    assert mapping in [1, 2]  # ensure mapping is set to 1 or 2
    return INSTRUCTIONS_DIR if mapping == 1 else INSTRUCTIONS_REVERSED_DIR


def load_instructions(count: int, mapping: int | None = None) -> list[Path]:
    """
    Return instruction asset paths from the unified instructions directory.
    """
    root = _instruction_root(mapping)
    return [root / f"{i}.png" for i in range(1, count + 1)]



def load_stimuli(mapping: int | None = None) -> dict[str, Path]:
    """
    Return stimulus asset paths for motor/sensorimotor tasks.
    Mapping image depends on task mapping version (1 or 2).
    """
    if mapping is None:
        mapping = getattr(cfg, "version", None) or cfg.MAPPING
    assert mapping in [1, 2]  # ensure mapping is set to 1 or 2

    return {
        "fixation": STIMULI_DIR / "CCS_Fixation.png",
        "blue": STIMULI_DIR / "CCS_Blue.png",
        "red": STIMULI_DIR / "CCS_Red.png",
        "white": STIMULI_DIR / "CCS_Fixation.png",
        "mapping": STIMULI_DIR / ("CCS_Mapping_1.png" if mapping == 1 else "CCS_Mapping_2.png"),
    }



# ---------- Load Feedback ----------

FEEDBACK_DIR = RESOURCES_DIR / "feedback"

FB_CORRECT = FEEDBACK_DIR / "feedback_correct.png"
FB_INCORRECT = FEEDBACK_DIR / "feedback_incorrect.png"

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
