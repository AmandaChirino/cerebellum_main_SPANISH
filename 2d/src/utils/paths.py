"""Centralized path and loading definitions for the target task."""

from __future__ import annotations

from pathlib import Path

import utils.config as cfg
from utils.stimuli_conditions import mapping_from_pid


# ---------- Directories ----------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESOURCES_DIR = PROJECT_ROOT / "resources"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

# ---------- Instruction Directories ----------

INSTRUCTIONS_V1_DIR = RESOURCES_DIR / "instructions_v1"
INSTRUCTIONS_V2_DIR = RESOURCES_DIR / "instructions_v2"


# ---------- Instruction Page Labels (1-based page index) ----------

TOTAL_INSTRUCTION_PAGES = 23

INTRO_PAGE_1 = 1
INTRO_PAGE_2 = 2
INTRO_PAGE_3 = 3
INTRO_PAGE_4 = 4
INTRO_PAGE_5 = 5
INTRO_PAGE_6 = 6
INTRO_PAGE_7 = 7

PRACTICE_BLOCK_TRIGGER_PAGE = 8
EXPERIMENTAL_BLOCK_1_TRIGGER_PAGE = 12
INTER_BLOCK_1_BREAK_START_PAGE = 13
EXPERIMENTAL_BLOCK_2_TRIGGER_PAGE = 17
INTER_BLOCK_2_BREAK_START_PAGE = 18
EXPERIMENTAL_BLOCK_3_TRIGGER_PAGE = 22

FINAL_PAGE = 23


# ---------- Load Stimuli (single mapping) ----------

# Single-mapping stimuli root for the target task.
STIMULI_ROOT_DIR = RESOURCES_DIR / "stimuli"


# ---------- Load Mapping Overlay ----------

MAPPING_DIR = RESOURCES_DIR / "mapping"
FIXATION_CROSS_IMAGE = RESOURCES_DIR / "Fixation_Cross.png"


# ---------- Load Instructions ----------

def _instruction_dir_by_mapping(mapping: int) -> Path:
    if mapping == 1:
        return INSTRUCTIONS_V1_DIR
    if mapping == 2:
        return INSTRUCTIONS_V2_DIR
    return INSTRUCTIONS_V1_DIR


def _active_mapping() -> int:
    """Resolve the current mapping from cfg.MAPPING or the confirmed PID."""
    if cfg.MAPPING in (1, 2):
        return cfg.MAPPING
    return mapping_from_pid(cfg.PID)


def _resolve_instruction_page(mapping: int, page_num: int) -> Path:
    """Resolve one instruction page path from mapping-specific instruction set."""
    page_path = _instruction_dir_by_mapping(mapping) / f"{page_num}.png"
    if page_path.exists():
        return page_path
    raise FileNotFoundError(
        f"Missing instruction page {page_num}.png in mapping-specific directory: "
        f"{_instruction_dir_by_mapping(mapping)}"
    )


def load_instruction_pages() -> dict[int, Path]:
    """Return page_num -> image path for all instruction pages in the task."""
    mapping = _active_mapping()
    pages: dict[int, Path] = {}
    for page_num in range(1, TOTAL_INSTRUCTION_PAGES + 1):
        pages[page_num] = _resolve_instruction_page(mapping, page_num)
    return pages


def load_stimuli_root() -> Path:
    """Return single-mapping stimuli root path."""
    return STIMULI_ROOT_DIR


def load_mapping_image() -> Path:
    """Return mapping overlay image by current mapping (1 -> 1.png, 2 -> 2.png)."""
    mapping = _active_mapping()
    mapping_path = MAPPING_DIR / f"{mapping}.png"
    if not mapping_path.exists():
        raise FileNotFoundError(f"Missing mapping image: {mapping_path}")
    return mapping_path


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
