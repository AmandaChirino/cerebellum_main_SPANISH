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



# # ---------- Load Instructions (single mapping) ----------

# INSTRUCTIONS_DIR = RESOURCES_DIR / "instructions"
# INSTRUCTIONS = []
# for i in range(cfg.INSTRUCTIONS_COUNT):
#     INSTRUCTIONS.append(INSTRUCTIONS_DIR / f"{i+1}.png")

# PRACTICE_INSTRUCTION = INSTRUCTIONS_DIR / "practice.png"
# TEST_INSTRUCTION = INSTRUCTIONS_DIR / "test.png"


# ---------- Load Instructions (multiple mappings) ----------

def load_instructions() -> list[Path]:
    """
    Return instruction asset paths based on the configured mapping.
    """
    assert cfg.MAPPING in [1, 2]    # ensure cfg.MAPPING is set to 1 or 2

    # Select instruction directory based on cfg.MAPPING
    if cfg.MAPPING == 1:
        INSTRUCTIONS_DIR = RESOURCES_DIR / "instructions_v1"
    else:   # cfg.MAPPING == 2
        INSTRUCTIONS_DIR = RESOURCES_DIR / "instructions_v2"
    
    INSTRUCTIONS = []
    for i in range(cfg.INSTRUCTIONS_COUNT):
        jpg_path = INSTRUCTIONS_DIR / f"{i+1}.jpg"
        png_path = INSTRUCTIONS_DIR / f"{i+1}.png"
        INSTRUCTIONS.append(jpg_path if jpg_path.exists() or not png_path.exists() else png_path)

    return INSTRUCTIONS



# ---------- Load Stimuli (single mapping) ----------

STIMULI_DIR = RESOURCES_DIR / "stimuli"
MAPPING_STIMULI_DIR = STIMULI_DIR / "mapping"
FIXATION_CROSS_IMAGE = RESOURCES_DIR / "Fixation_Cross.png"

STIMULI = []
for i in range(cfg.STIMULI_COUNT):
    STIMULI.append(STIMULI_DIR / f"{i+1}.png")


def mapping_image_path() -> Path:
    """
    Return the full-screen response mapping image for the current mapping.
    """
    mapping = cfg.MAPPING if cfg.MAPPING in (1, 2) else 1
    return MAPPING_STIMULI_DIR / f"mapping {mapping}.jpg"


# ---------- Load Stimuli (multiple mappings) ----------

# def load_stimuli() -> tuple[list[Path], ...]:
#     """Return stimulus asset paths based on the configured mapping."""
#     assert cfg.MAPPING in [1, 2]    # ensure cfg.MAPPING is set to 1 or 2

#     # Select stimulus directory based on cfg.MAPPING
#     if cfg.MAPPING == 1:
#         STIMULI_DIR = RESOURCES_DIR / "stimuli_v1"
#     else:   # cfg.MAPPING == 2
#         STIMULI_DIR = RESOURCES_DIR / "stimuli_v2"

#     STIMULI = []
#     for i in range(cfg.STIMULI_COUNT):
#         STIMULI.append(STIMULI_DIR / f"{i+1}.png")


#     return STIMULI



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
