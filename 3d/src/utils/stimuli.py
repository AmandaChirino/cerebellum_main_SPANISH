"""
Stimulus loading and balancing for the 3D mental-rotation task.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
import re

import utils.config as cfg
from utils.logger import get_logger
from utils.paths import RESOURCES_DIR


logger = get_logger("./src/utils/stimuli")

ANGLES = (0, 50, 100, 150)
ANSWERS = ("normal", "mirrored")
STIMULUS_RE = re.compile(r"^(?P<item_id>\d+)_(?P<angle>0|50|100|150)(?P<mirror>_R)?\.jpg$")

# Fixed test pools (12 IDs total), split into two 6-ID sets to keep 48 trials per test block.
TEST_SET_A = {1, 19, 23, 36, 39, 44}
TEST_SET_B = {8, 21, 25, 30, 31, 43}

# Sequence constraints.
MAX_SAME_ANSWER_RUN = 3
MAX_SAME_ANGLE_RUN = 2
MAX_SAME_ITEM_RUN = 2
FORBID_FIRST_ANGLE = 150
MAX_SEQUENCE_ATTEMPTS = 5000


@dataclass(frozen=True)
class StimulusTrial:
    """
    Parsed stimulus metadata derived from the image filename.
    """
    condition: str
    stimuli_path: Path
    item_id: int
    rotation_angle: int
    correct_answer: str


def _stimuli_dir() -> Path:
    """
    Return the flat stimulus directory.
    """
    preferred = RESOURCES_DIR / "stimuli"
    if preferred.exists():
        return preferred
    return RESOURCES_DIR / "strimuli"


def _parse_stimulus(path: Path) -> StimulusTrial | None:
    """
    Parse an image filename like 34_150_R.jpg into trial metadata.
    """
    match = STIMULUS_RE.match(path.name)
    if match is None:
        return None

    item_id = int(match.group("item_id"))
    angle = int(match.group("angle"))
    correct_answer = "mirrored" if match.group("mirror") else "normal"
    condition = "different" if match.group("mirror") else "same"

    return StimulusTrial(
        condition=condition,
        stimuli_path=path,
        item_id=item_id,
        rotation_angle=angle,
        correct_answer=correct_answer,
    )


def _ids_for_block(block: str) -> set[int]:
    """
    Return item IDs for practice/test blocks under PID-based counterbalancing.
    """
    if block == "practice":
        return {13, 14}

    remainder = cfg.COUNTERBALANCE_REMAINDER
    if remainder not in (0, 1, 2, 3):
        remainder = 1

    first_set = TEST_SET_A
    second_set = TEST_SET_B
    reversed_order = remainder in (0, 3)

    if block == "test1":
        return second_set if reversed_order else first_set

    if block == "test2":
        return first_set if reversed_order else second_set

    raise ValueError(f"Unknown stimulus block: {block}")


def _load_for_ids(item_ids: set[int]) -> list[StimulusTrial]:
    """
    Load all parsed stimuli whose item ID is in item_ids.
    """
    stim_dir = _stimuli_dir()
    trials: list[StimulusTrial] = []

    for path in sorted(stim_dir.glob("*.jpg")):
        trial = _parse_stimulus(path)
        if trial is not None and trial.item_id in item_ids:
            trials.append(trial)

    return trials


def _block_label(block: str) -> str:
    """
    Return a human-readable label for logs (practice/test plus A/B alias).
    """
    if block == "practice":
        return "practice"

    remainder = cfg.COUNTERBALANCE_REMAINDER
    if remainder not in (0, 1, 2, 3):
        remainder = 1

    reversed_order = remainder in (0, 3)
    if block == "test1":
        return "test1(B)" if reversed_order else "test1(A)"
    if block == "test2":
        return "test2(A)" if reversed_order else "test2(B)"
    return block


def _validate_bucket_balance(trials: list[StimulusTrial]) -> None:
    """
    Validate equal counts for all angle x answer cells.
    """
    buckets: dict[tuple[int, str], int] = {
        (angle, answer): 0
        for angle in ANGLES
        for answer in ANSWERS
    }

    for trial in trials:
        buckets[(trial.rotation_angle, trial.correct_answer)] += 1

    if len(set(buckets.values())) != 1:
        raise ValueError(f"Unbalanced stimulus buckets: {buckets}")


def _max_run(values: list[object]) -> int:
    """
    Return the longest run of identical consecutive values.
    """
    if not values:
        return 0

    best = 1
    current = 1
    for i in range(1, len(values)):
        if values[i] == values[i - 1]:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


def _is_valid_sequence(sequence: list[StimulusTrial], relax_first_trial_rule: bool) -> bool:
    """
    Validate sequence against R1-R4 constraints.
    """
    if not sequence:
        return False

    answers = [trial.correct_answer for trial in sequence]
    angles = [trial.rotation_angle for trial in sequence]
    item_ids = [trial.item_id for trial in sequence]

    if _max_run(answers) > MAX_SAME_ANSWER_RUN:
        return False
    if _max_run(angles) > MAX_SAME_ANGLE_RUN:
        return False
    if _max_run(item_ids) > MAX_SAME_ITEM_RUN:
        return False
    if not relax_first_trial_rule and sequence[0].rotation_angle == FORBID_FIRST_ANGLE:
        return False

    return True


def _balanced_bucket_order(trials: list[StimulusTrial], block: str) -> list[StimulusTrial]:
    """
    Generate a sequence using pure rejection sampling over full permutations.

    Constraints:
    - R1: max run of correct_answer <= MAX_SAME_ANSWER_RUN
    - R2: max run of rotation_angle <= MAX_SAME_ANGLE_RUN
    - R3: max run of item_id <= MAX_SAME_ITEM_RUN
    - R4: first trial angle != FORBID_FIRST_ANGLE (relaxed only as fallback)
    """
    _validate_bucket_balance(trials)

    pid = cfg.PID or "unknown"
    block_name = _block_label(block)

    # First pass: enforce R1-R4 strictly.
    for attempt in range(1, MAX_SEQUENCE_ATTEMPTS + 1):
        candidate = list(trials)
        random.shuffle(candidate)
        if _is_valid_sequence(candidate, relax_first_trial_rule=False):
            return candidate

    # Fallback pass: relax only R4 (first trial not 150), keep R1-R3 strict.
    logger.warning(
        "Fallback activated | participant_id=%s | block=%s | relaxed_constraint=R4_first_trial_not_150 "
        "| attempts=%d",
        pid,
        block_name,
        MAX_SEQUENCE_ATTEMPTS,
    )

    for attempt in range(1, MAX_SEQUENCE_ATTEMPTS + 1):
        candidate = list(trials)
        random.shuffle(candidate)
        if _is_valid_sequence(candidate, relax_first_trial_rule=True):
            return candidate

    # Last-resort operational safeguard.
    logger.error(
        "Fallback failed | participant_id=%s | block=%s | relaxed_constraint=R4_first_trial_not_150 "
        "| attempts=%d | action=return_unconstrained_shuffle",
        pid,
        block_name,
        MAX_SEQUENCE_ATTEMPTS,
    )
    candidate = list(trials)
    random.shuffle(candidate)
    return candidate


def load_balanced_stimuli(block: str) -> list[StimulusTrial]:
    """
    Load and balance stimuli for practice, test1, or test2.
    """
    item_ids = _ids_for_block(block)
    trials = _load_for_ids(item_ids)
    expected = len(item_ids) * len(ANGLES) * len(ANSWERS)

    if len(trials) != expected:
        logger.warning(
            "Expected %d stimuli for %s IDs %s, found %d",
            expected,
            block,
            sorted(item_ids),
            len(trials),
        )

    return _balanced_bucket_order(trials, block)


def answer_for_option(option_selected: int | None) -> str | None:
    """
    Convert left/right option selection into normal/mirrored by mapping.
    """
    if option_selected is None:
        return None

    mapping = cfg.MAPPING if cfg.MAPPING in (1, 2) else 1
    if mapping == 1:
        return "normal" if option_selected == 1 else "mirrored"
    return "mirrored" if option_selected == 1 else "normal"


def option_for_answer(answer: str) -> int:
    """
    Convert a correct normal/mirrored answer into left/right option by mapping.
    """
    mapping = cfg.MAPPING if cfg.MAPPING in (1, 2) else 1
    if mapping == 1:
        return 1 if answer == "normal" else 2
    return 1 if answer == "mirrored" else 2
