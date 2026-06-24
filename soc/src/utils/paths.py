# ./src/utils/paths.py
"""
Path management module.

This module defines and centralizes all filesystem paths used throughout the application.
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

STIMULI_DIR = RESOURCES_DIR / "stimuli"


# ---------- Load Instructions ----------

# Load general instruction pages
def get_instructions(mapping: int = None) -> list[Path]:
    """Load instruction pages based on mapping version."""
    if mapping is None:
        mapping = cfg.MAPPING
    
    instructions_dir = RESOURCES_DIR / "instructions"
    
    return [instructions_dir / f"{i+1}.PNG" for i in range(cfg.INSTRUCTIONS_COUNT)]

# ---------- Load Stimuli ----------

CSV_PATH = STIMULI_DIR / "SOC_stimuli_info.csv"
VIDEOS = STIMULI_DIR / "videos"
FIXATION_CROSS = STIMULI_DIR / "Fixation_Cross.png"

MAPPING = RESOURCES_DIR / "mapping" / "SOC_Guide.png"

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

# ---------- Font ----------

FONT = RESOURCES_DIR / "OpenSans.ttf"