# ./src/utils/paths.py
"""
Path management module.

This module defines and centralizes all filesystem paths used throughout the application.
"""


from pathlib import Path


# ---------- Directories ----------

# project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# resources
RESOURCES_DIR = PROJECT_ROOT / "resources"

# results
RESULTS_DIR = PROJECT_ROOT / "results"

# logs
LOGS_DIR = PROJECT_ROOT / "logs"

# monitor reference (last registered monitor measures)
MONITOR_REFERENCE = PROJECT_ROOT / "config" / "monitor_reference.json"


# ---------- Load Instrucrtions ----------

# Load the numbered instruction pages from resources/instructions.
INSTRUCTIONS_DIR = RESOURCES_DIR / "instructions"
INSTRUCTION_PAGE_COUNT = 11
INSTRUCTIONS = [
    INSTRUCTIONS_DIR / f"{i}.png"
    for i in range(1, INSTRUCTION_PAGE_COUNT + 1)
]

def get_instructions(mapping: int = None) -> list[Path]:
    """Return numbered instruction pages from resources/instructions (1.png–11.png)."""
    return INSTRUCTIONS

# Load special instruction page(s)
PRACTICE_INSTRUCTIONS = RESOURCES_DIR / "stimuli" / "practice.png"
TEST_INSTRUCTIONS = INSTRUCTIONS_DIR / "stim_instruction.png"

# TODO: Load additional instructions configurations if necessary


# ---------- Load Stimuli ----------

STIMULI_DIR = RESOURCES_DIR / "stimuli"

CONTEXTUAL_IMG = STIMULI_DIR / "contextual" / "frames"
BASELINE_IMG = STIMULI_DIR / "baseline" / "frames"

STIMPATHS_CSV_A = STIMULI_DIR / "stimPaths_Context_A.csv"

PRACTICE = STIMULI_DIR / "practice.mp4"

# ---------- Load Feedback ----------

FB_CORRECT = RESOURCES_DIR / "feedback" / "correct.png"
FB_INCORRECT = RESOURCES_DIR / "feedback" / "incorrect.png"

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
