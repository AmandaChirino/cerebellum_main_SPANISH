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

# TODO: Add additional paths if necessary


# ---------- Load Instrucrtions ----------

# Load general instruction pages
INSTRUCTIONS_DIR = RESOURCES_DIR / "instructions"
INSTRUCTIONS = []
for i in range(cfg.INSTRUCTIONS_COUNT):
    INSTRUCTIONS.append(INSTRUCTIONS_DIR / f"{i+1}.png")

# Load special instruction page(s)
PRACTICE_INSTRUCTIONS = INSTRUCTIONS_DIR / "practice.png"
TEST_INSTRUCTIONS = INSTRUCTIONS_DIR / "test.png"
PRACTICE_BREAK = INSTRUCTIONS_DIR / "practice.png"  # Pause screen between practice blocks

# TODO: Load additional instructions configurations if necessary


# ---------- Load Stimuli ----------

STIMULI_DIR = RESOURCES_DIR / "stimuli"

STIM_BG = STIMULI_DIR / "stim_bg.png"
STIM_D = STIMULI_DIR / "nb_d.png"
STIM_F = STIMULI_DIR / "nb_f.png"
STIM_H = STIMULI_DIR / "nb_h.png"
STIM_J = STIMULI_DIR / "nb_j.png"
STIM_K = STIMULI_DIR / "nb_k.png"
STIM_L = STIMULI_DIR / "nb_l.png"
STIM_M = STIMULI_DIR / "nb_m.png"
STIM_S = STIMULI_DIR / "nb_s.png"
STIM_T = STIMULI_DIR / "nb_t.png"
STIM_V = STIMULI_DIR / "nb_v.png"

STIMULI = [STIM_D, STIM_F, STIM_H, STIM_J, STIM_K, STIM_L, STIM_M, STIM_S, STIM_T, STIM_V]


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
