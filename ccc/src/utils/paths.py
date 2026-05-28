"""
Filesystem path definitions for the current CCC task.
"""


from pathlib import Path

import utils.config as cfg


# ---------- Directories ----------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESOURCES_DIR = PROJECT_ROOT / "resources"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

STIMULI_DIR = RESOURCES_DIR / "stimuli"
LETTERS_DIR = STIMULI_DIR / "Letters"
MAPPING_DIR = STIMULI_DIR / "Mapping"


# ---------- Instructions ----------

INSTRUCTIONS_V11_DIR = STIMULI_DIR / "instructions_v11"
INSTRUCTIONS_V12_DIR = STIMULI_DIR / "instructions_v12"
INSTRUCTIONS_V21_DIR = STIMULI_DIR / "instructions_v21"
INSTRUCTIONS_V22_DIR = STIMULI_DIR / "instructions_v22"


def load_instructions() -> list[Path]:
    assert cfg.MAPPING in [1, 2, 3, 4, 5, 6, 7, 8]
    mapping_to_dir = {
        1: INSTRUCTIONS_V11_DIR,
        2: INSTRUCTIONS_V21_DIR,
        3: INSTRUCTIONS_V12_DIR,
        4: INSTRUCTIONS_V22_DIR,
        5: INSTRUCTIONS_V11_DIR,  # same as 1
        6: INSTRUCTIONS_V21_DIR,  # same as 2
        7: INSTRUCTIONS_V12_DIR,  # same as 3
        8: INSTRUCTIONS_V22_DIR,  # same as 4
    }
    instructions_dir = mapping_to_dir[cfg.MAPPING]
    return sorted(
        instructions_dir.glob("*.png"),
        key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem,
    )


# ---------- Stimuli ----------

FIXATION_CROSS = STIMULI_DIR / "Fixation_Cross.png"

# a
a_lower_pink = LETTERS_DIR / "a_lower_pink.png"
a_lower_yellow = LETTERS_DIR / "a_lower_yellow.png"
A_upper_pink = LETTERS_DIR / "A_upper_pink.png"
A_upper_yellow = LETTERS_DIR / "A_upper_yellow.png"

# b
b_lower_pink = LETTERS_DIR / "b_lower_pink.png"
b_lower_yellow = LETTERS_DIR / "b_lower_yellow.png"
B_upper_pink = LETTERS_DIR / "B_upper_pink.png"
B_upper_yellow = LETTERS_DIR / "B_upper_yellow.png"

# e
e_lower_pink = LETTERS_DIR / "e_lower_pink.png"
e_lower_yellow = LETTERS_DIR / "e_lower_yellow.png"
E_upper_pink = LETTERS_DIR / "E_upper_pink.png"
E_upper_yellow = LETTERS_DIR / "E_upper_yellow.png"

# g
g_lower_pink = LETTERS_DIR / "g_lower_pink.png"
g_lower_yellow = LETTERS_DIR / "g_lower_yellow.png"
G_upper_pink = LETTERS_DIR / "G_upper_pink.png"
G_upper_yellow = LETTERS_DIR / "G_upper_yellow.png"

# i
i_lower_pink = LETTERS_DIR / "i_lower_pink.png"
i_lower_yellow = LETTERS_DIR / "i_lower_yellow.png"
I_upper_pink = LETTERS_DIR / "I_upper_pink.png"
I_upper_yellow = LETTERS_DIR / "I_upper_yellow.png"

# p
p_lower_pink = LETTERS_DIR / "p_lower_pink.png"
p_lower_yellow = LETTERS_DIR / "p_lower_yellow.png"
P_upper_pink = LETTERS_DIR / "P_upper_pink.png"
P_upper_yellow = LETTERS_DIR / "P_upper_yellow.png"

# r
r_lower_pink = LETTERS_DIR / "r_lower_pink.png"
r_lower_yellow = LETTERS_DIR / "r_lower_yellow.png"
R_upper_pink = LETTERS_DIR / "R_upper_pink.png"
R_upper_yellow = LETTERS_DIR / "R_upper_yellow.png"

# u
u_lower_pink = LETTERS_DIR / "u_lower_pink.png"
u_lower_yellow = LETTERS_DIR / "u_lower_yellow.png"
U_upper_pink = LETTERS_DIR / "U_upper_pink.png"
U_upper_yellow = LETTERS_DIR / "U_upper_yellow.png"


# ---------- Mapping ----------

MAPPING_1 = MAPPING_DIR / "CCC_Mapping_1.png"
MAPPING_1_PINK = MAPPING_DIR / "CCC_Mapping_1_Pink.png"
MAPPING_1_YELLOW = MAPPING_DIR / "CCC_Mapping_1_Yellow.png"

MAPPING_2 = MAPPING_DIR / "CCC_Mapping_2.png"
MAPPING_2_PINK = MAPPING_DIR / "CCC_Mapping_2_Pink.png"
MAPPING_2_YELLOW = MAPPING_DIR / "CCC_Mapping_2_Yellow.png"

PHONETIC_TASK_PHASES = {
    "phonetic_task_practice",
    "phonetic_task_experimental",
}
ORTHOGRAPHIC_TASK_PHASES = {
    "orthographic_task_practice",
    "orthographic_task_experimental",
}
MULTI_TASK_PHASES = {
    "multi_task_practice",
    "multi_task_experimental_block_1",
    "multi_task_experimental_block_2",
}


def load_mapping_images() -> tuple[Path, Path, Path]:
    assert cfg.MAPPING in [1, 2, 3, 4, 5, 6, 7, 8]
    if cfg.mapping_left_is_vowel_lower(cfg.MAPPING):
        return MAPPING_1, MAPPING_1_PINK, MAPPING_1_YELLOW
    return MAPPING_2, MAPPING_2_PINK, MAPPING_2_YELLOW


def get_mapping_image_for_task_phase(task_phase: str) -> Path:
    base_img, pink_img, yellow_img = load_mapping_images()
    if task_phase in PHONETIC_TASK_PHASES:
        return pink_img
    if task_phase in ORTHOGRAPHIC_TASK_PHASES:
        return yellow_img
    if task_phase in MULTI_TASK_PHASES:
        return base_img
    raise ValueError(f"Unsupported task phase: {task_phase}")


# ---------- Feedback ----------

FEEDBACK_DIR = RESOURCES_DIR / "feedback"
FB_CORRECT = FEEDBACK_DIR / "correct.png"
FB_INCORRECT = FEEDBACK_DIR / "incorrect.png"
BEEP = FEEDBACK_DIR / "beep.wav"


# ---------- Load Admin (dynamic) ----------

# Read and bind all .png files under ADMINH_DIR; variable names
# match filenames (without extension). Example: Admin.png -> Admin
# This supports runtime composition rules (e.g., adding _Next, _1-6, _L/R).

ADMIN_DIR = RESOURCES_DIR / "admin"

def _bind_admin_images():
    images = {}
    if ADMIN_DIR.exists():
        for path in ADMIN_DIR.glob('*.png'):
            var_name = path.stem  # filename without extension
            globals()[var_name] = path
            images[var_name] = path
    return images

ADMIN_IMAGES = _bind_admin_images()
