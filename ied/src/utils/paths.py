# ./src/utils/paths.py
"""
Path management module.

This module defines and centralizes all filesystem paths used throughout the application.
It also provides loader helpers for a single-mapping setup.
"""

from __future__ import annotations

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

INSTRUCTIONS_DIR = RESOURCES_DIR / "instructions"


def load_instructions() -> list[Path]:
    """
    Load instruction pages for a single mapping.

    :return: Ordered list of instruction image paths
    :rtype: list[pathlib.Path]
    """
    return [INSTRUCTIONS_DIR / f"{i+1}.png" for i in range(cfg.INSTRUCTION_COUNT)]


# ---------- Load Stimuli ----------

STIMULI_DIR = RESOURCES_DIR / "stimuli"


def load_stimuli() -> dict[str, Path]:
    """
    Load stimulus paths.

    Mapping rule:
    - MAPPING == 1: default mapping.
    - MAPPING == 2: swap CORRECT/INCORRECT for experimental blocks P1-P9.
      Practice blocks remain unchanged.

    :return: Mapping from stimulus key to file path
    :rtype: dict[str, pathlib.Path]
    """
    stimuli = {
        "PRACTICE1_CORRECT": STIMULI_DIR / "ied_circle_big.png",
        "PRACTICE1_INCORRECT": STIMULI_DIR / "ied_circle_little.png",
        "PRACTICE2_CORRECT": STIMULI_DIR / "ied_circle_little.png",
        "PRACTICE2_INCORRECT": STIMULI_DIR / "ied_circle_big.png",

        "P1_CORRECT": STIMULI_DIR / "ied_s1.png",
        "P1_INCORRECT": STIMULI_DIR / "ied_s2.png",
        "P2_CORRECT": STIMULI_DIR / "ied_s2.png",
        "P2_INCORRECT": STIMULI_DIR / "ied_s1.png",

        "P3_CORRECT": STIMULI_DIR / "ied_s2.png",
        "P3_INCORRECT": STIMULI_DIR / "ied_s1.png",
        "P3_BUFFER1": STIMULI_DIR / "ied_l1.png",
        "P3_BUFFER2": STIMULI_DIR / "ied_l2.png",

        "P4_CORRECT": STIMULI_DIR / "ied_s2.png",
        "P4_INCORRECT": STIMULI_DIR / "ied_s1.png",
        "P4_BUFFER1": STIMULI_DIR / "ied_l1.png",
        "P4_BUFFER2": STIMULI_DIR / "ied_l2.png",

        "P5_CORRECT": STIMULI_DIR / "ied_s1.png",
        "P5_INCORRECT": STIMULI_DIR / "ied_s2.png",
        "P5_BUFFER1": STIMULI_DIR / "ied_l1.png",
        "P5_BUFFER2": STIMULI_DIR / "ied_l2.png",

        "P6_CORRECT": STIMULI_DIR / "ied_s3.png",
        "P6_INCORRECT": STIMULI_DIR / "ied_s4.png",
        "P6_BUFFER1": STIMULI_DIR / "ied_l3.png",
        "P6_BUFFER2": STIMULI_DIR / "ied_l4.png",

        "P7_CORRECT": STIMULI_DIR / "ied_s4.png",
        "P7_INCORRECT": STIMULI_DIR / "ied_s3.png",
        "P7_BUFFER1": STIMULI_DIR / "ied_l3.png",
        "P7_BUFFER2": STIMULI_DIR / "ied_l4.png",

        "P8_CORRECT": STIMULI_DIR / "ied_l5.png",
        "P8_INCORRECT": STIMULI_DIR / "ied_l6.png",
        "P8_BUFFER1": STIMULI_DIR / "ied_s5.png",
        "P8_BUFFER2": STIMULI_DIR / "ied_s6.png",

        "P9_CORRECT": STIMULI_DIR / "ied_l6.png",
        "P9_INCORRECT": STIMULI_DIR / "ied_l5.png",
        "P9_BUFFER1": STIMULI_DIR / "ied_s5.png",
        "P9_BUFFER2": STIMULI_DIR / "ied_s6.png",
    }

    if cfg.MAPPING == 2:
        for phase in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"):
            correct_key = f"{phase}_CORRECT"
            incorrect_key = f"{phase}_INCORRECT"
            stimuli[correct_key], stimuli[incorrect_key] = stimuli[incorrect_key], stimuli[correct_key]

    return stimuli


# ---------- Load Feedback ----------

FEEDBACK_DIR = RESOURCES_DIR / "feedback"

FB_CORRECT = FEEDBACK_DIR / "feedback_correct.png"
FB_INCORRECT = FEEDBACK_DIR / "feedback_incorrect.png"


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
