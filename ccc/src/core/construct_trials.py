"""
Trial series construction for contextual control tasks.

This module currently supports:
- phonetic practice / phonetic experimental
- orthographic practice / orthographic experimental

Naming follows "experimental" (not "actual").
"""


from __future__ import annotations
from pathlib import Path
import random
from typing import TypedDict

from utils import paths


LETTER_GROUPS: dict[str, dict[str, tuple[Path, ...]]] = {
    "pink": {
        "upper_vowels": (
            paths.A_upper_pink,
            paths.E_upper_pink,
            paths.I_upper_pink,
            paths.U_upper_pink,
        ),
        "upper_consonants": (
            paths.B_upper_pink,
            paths.G_upper_pink,
            paths.P_upper_pink,
            paths.R_upper_pink,
        ),
        "lower_vowels": (
            paths.a_lower_pink,
            paths.e_lower_pink,
            paths.i_lower_pink,
            paths.u_lower_pink,
        ),
        "lower_consonants": (
            paths.b_lower_pink,
            paths.g_lower_pink,
            paths.p_lower_pink,
            paths.r_lower_pink,
        ),
    },
    "yellow": {
        "upper_vowels": (
            paths.A_upper_yellow,
            paths.E_upper_yellow,
            paths.I_upper_yellow,
            paths.U_upper_yellow,
        ),
        "upper_consonants": (
            paths.B_upper_yellow,
            paths.G_upper_yellow,
            paths.P_upper_yellow,
            paths.R_upper_yellow,
        ),
        "lower_vowels": (
            paths.a_lower_yellow,
            paths.e_lower_yellow,
            paths.i_lower_yellow,
            paths.u_lower_yellow,
        ),
        "lower_consonants": (
            paths.b_lower_yellow,
            paths.g_lower_yellow,
            paths.p_lower_yellow,
            paths.r_lower_yellow,
        ),
    },
}

class TrialSpec(TypedDict):
    color: str
    case_type: str
    stimuli: str
    stim_path: Path
    list_name: str
    trial_class: str
    congruency: str
    switching: str
    stim_repetition: str


def _resolve_letter_path(color: str, case_type: str, stimuli: str) -> Path:
    """
    Resolve one letter image path from (color, case_type, stimuli).
    """
    if case_type == "upper":
        var_name = f"{stimuli.upper()}_upper_{color}"
    else:
        var_name = f"{stimuli.lower()}_lower_{color}"
    return getattr(paths, var_name)


def _make_trial(
    color: str,
    case_type: str,
    stimuli: str,
    list_name: str,
    trial_class: str,
    congruency: str,
    switching: str,
    stim_repetition: str,
) -> TrialSpec:
    return {
        "color": color,
        "case_type": case_type,
        "stimuli": stimuli,
        "stim_path": _resolve_letter_path(color, case_type, stimuli),
        "list_name": list_name,
        "trial_class": trial_class,
        "congruency": congruency,
        "switching": switching,
        "stim_repetition": stim_repetition,
    }


# Fixed mixed-task trial series (directly materialized from provided spreadsheets).
MULTI_TASK_PRACTICE: list[TrialSpec] = [
    _make_trial("pink",   "lower", "a", "practice", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("pink",   "upper", "B", "practice", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("yellow", "lower", "a", "practice", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "G", "practice", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("pink",   "upper", "E", "practice", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "r", "practice", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("yellow", "lower", "e", "practice", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "I", "practice", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("pink",   "lower", "u", "practice", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("yellow", "lower", "p", "practice", "consonant", "incongruent", "switch",    "no"),
]

MULTI_TASK_EXPERIMENTAL_BLOCK_1: list[TrialSpec] = [
    _make_trial("yellow", "upper", "I", "list1", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("yellow", "lower", "a", "list1", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("pink",   "upper", "U", "list1", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "e", "list1", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("pink",   "upper", "R", "list1", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("pink",   "upper", "I", "list1", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("pink",   "upper", "G", "list1", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("yellow", "lower", "p", "list1", "consonant", "incongruent", "switch",    "yes"),
    _make_trial("yellow", "upper", "P", "list1", "consonant", "congruent",   "no_switch", "yes"),
    _make_trial("yellow", "lower", "a", "list1", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("yellow", "lower", "u", "list1", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("yellow", "lower", "r", "list1", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("pink",   "upper", "B", "list1", "consonant", "congruent",   "switch",    "no"),
    _make_trial("yellow", "lower", "e", "list1", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("yellow", "lower", "g", "list1", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("yellow", "upper", "B", "list1", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("yellow", "lower", "r", "list1", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("pink",   "lower", "e", "list1", "vocal",     "congruent",   "switch",    "yes"),
    _make_trial("pink",   "upper", "E", "list1", "vocal",     "incongruent", "no_switch", "yes"),
    _make_trial("pink",   "upper", "A", "list1", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("yellow", "lower", "i", "list1", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "U", "list1", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("pink",   "lower", "i", "list1", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "A", "list1", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("pink",   "upper", "U", "list1", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("yellow", "upper", "E", "list1", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "a", "list1", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("pink",   "lower", "u", "list1", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("pink",   "lower", "i", "list1", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("yellow", "upper", "P", "list1", "consonant", "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "U", "list1", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("pink",   "upper", "R", "list1", "consonant", "congruent",   "switch",    "yes"),
    _make_trial("yellow", "upper", "R", "list1", "consonant", "congruent",   "switch",    "yes"),
    _make_trial("yellow", "upper", "B", "list1", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("pink",   "upper", "P", "list1", "consonant", "congruent",   "switch",    "no"),
    _make_trial("pink",   "upper", "B", "list1", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("yellow", "upper", "G", "list1", "consonant", "congruent",   "switch",    "no"),
    _make_trial("pink",   "lower", "b", "list1", "consonant", "incongruent", "switch",    "no"),
    _make_trial("yellow", "upper", "I", "list1", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "g", "list1", "consonant", "incongruent", "switch",    "yes"),
    _make_trial("pink",   "lower", "g", "list1", "consonant", "incongruent", "no_switch", "yes"),
    _make_trial("yellow", "lower", "e", "list1", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("pink",   "lower", "p", "list1", "consonant", "incongruent", "switch",    "no"),
    _make_trial("yellow", "lower", "g", "list1", "consonant", "incongruent", "switch",    "no"),
    _make_trial("pink",   "upper", "A", "list1", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "r", "list1", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("pink",   "lower", "p", "list1", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("yellow", "lower", "b", "list1", "consonant", "incongruent", "switch",    "no"),
]

MULTI_TASK_EXPERIMENTAL_BLOCK_2: list[TrialSpec] = [
    _make_trial("pink",   "lower", "b", "list2", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("yellow", "upper", "I", "list2", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "g", "list2", "consonant", "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "i", "list2", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("pink",   "upper", "G", "list2", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("pink",   "lower", "e", "list2", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("yellow", "upper", "A", "list2", "vocal",     "incongruent", "switch",    "yes"),
    _make_trial("pink",   "upper", "A", "list2", "vocal",     "incongruent", "switch",    "yes"),
    _make_trial("pink",   "upper", "R", "list2", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("pink",   "lower", "a", "list2", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("yellow", "lower", "b", "list2", "consonant", "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "p", "list2", "consonant", "incongruent", "switch",    "no"),
    _make_trial("yellow", "upper", "E", "list2", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("yellow", "lower", "r", "list2", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("pink",   "upper", "G", "list2", "consonant", "congruent",   "switch",    "no"),
    _make_trial("pink",   "upper", "U", "list2", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("pink",   "upper", "I", "list2", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("pink",   "upper", "P", "list2", "consonant", "congruent",   "no_switch", "yes"),
    _make_trial("yellow", "lower", "p", "list2", "consonant", "incongruent", "switch",    "yes"),
    _make_trial("yellow", "upper", "A", "list2", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("yellow", "lower", "p", "list2", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("yellow", "upper", "R", "list2", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("pink",   "upper", "E", "list2", "vocal",     "incongruent", "switch",    "yes"),
    _make_trial("pink",   "upper", "E", "list2", "vocal",     "incongruent", "no_switch", "yes"),
    _make_trial("yellow", "lower", "u", "list2", "vocal",     "congruent",   "switch",    "yes"),
    _make_trial("pink",   "lower", "u", "list2", "vocal",     "congruent",   "switch",    "yes"),
    _make_trial("pink",   "lower", "r", "list2", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("yellow", "upper", "G", "list2", "consonant", "congruent",   "switch",    "no"),
    _make_trial("pink",   "upper", "P", "list2", "consonant", "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "B", "list2", "consonant", "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "U", "list2", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("yellow", "lower", "e", "list2", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("yellow", "upper", "P", "list2", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("yellow", "lower", "u", "list2", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("pink",   "lower", "r", "list2", "consonant", "incongruent", "switch",    "no"),
    _make_trial("yellow", "lower", "i", "list2", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("pink",   "upper", "B", "list2", "consonant", "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "R", "list2", "consonant", "congruent",   "switch",    "no"),
    _make_trial("pink",   "upper", "I", "list2", "vocal",     "incongruent", "switch",    "no"),
    _make_trial("yellow", "lower", "g", "list2", "consonant", "incongruent", "switch",    "no"),
    _make_trial("pink",   "lower", "u", "list2", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("yellow", "lower", "i", "list2", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("yellow", "upper", "G", "list2", "consonant", "congruent",   "no_switch", "no"),
    _make_trial("yellow", "upper", "E", "list2", "vocal",     "incongruent", "no_switch", "no"),
    _make_trial("yellow", "lower", "a", "list2", "vocal",     "congruent",   "no_switch", "no"),
    _make_trial("yellow", "lower", "b", "list2", "consonant", "incongruent", "no_switch", "no"),
    _make_trial("pink",   "lower", "a", "list2", "vocal",     "congruent",   "switch",    "no"),
    _make_trial("pink",   "lower", "b", "list2", "consonant", "incongruent", "no_switch", "no"),
]


def _build_practice_trials(color: str, rng: random.Random) -> list[Path]:
    """
    Build one 8-trial practice set from same-color letters:
    2 upper vowels + 2 upper consonants + 2 lower vowels + 2 lower consonants.
    """
    groups = LETTER_GROUPS[color]
    practice_trials = []
    practice_trials.extend(rng.sample(groups["upper_vowels"], 2))
    practice_trials.extend(rng.sample(groups["upper_consonants"], 2))
    practice_trials.extend(rng.sample(groups["lower_vowels"], 2))
    practice_trials.extend(rng.sample(groups["lower_consonants"], 2))
    rng.shuffle(practice_trials)
    return practice_trials


def _build_experimental_trials(
    color: str,
    practice_trials: list[Path],
    rng: random.Random,
) -> list[Path]:
    """
    Build one 24-trial experimental set:
    practice 8 + all 16 same-color letters (each once).
    """
    groups = LETTER_GROUPS[color]
    all_letters = (
        *groups["upper_vowels"],
        *groups["upper_consonants"],
        *groups["lower_vowels"],
        *groups["lower_consonants"],
    )
    experimental_trials = [*practice_trials, *all_letters]
    rng.shuffle(experimental_trials)
    return experimental_trials


def construct_phonetic_trials(
    seed: int | None = None,
    color: str = "pink",
) -> tuple[list[Path], list[Path]]:
    """
    Construct phonetic task trials (practice, experimental).
    """
    rng = random.Random(seed)
    phonetic_practice = _build_practice_trials(color, rng)
    phonetic_experimental = _build_experimental_trials(color, phonetic_practice, rng)
    return phonetic_practice, phonetic_experimental


def construct_orthographic_trials(
    seed: int | None = None,
    color: str = "yellow",
) -> tuple[list[Path], list[Path]]:
    """
    Construct orthographic task trials (practice, experimental).

    Orthographic trial color is configurable.
    """
    rng = random.Random(seed)
    orthographic_practice = _build_practice_trials(color, rng)
    orthographic_experimental = _build_experimental_trials(color, orthographic_practice, rng)
    return orthographic_practice, orthographic_experimental


def construct_single_task_trial_series(
    seed: int | None = None,
) -> dict[str, list[Path]]:
    """
    Construct all single-task trial series for current scope.

    Returns keys:
    - phonetic_task_practice
    - phonetic_task_experimental
    - orthographic_task_practice
    - orthographic_task_experimental
    """
    rng = random.Random(seed)

    # Task-color binding is fixed by task definition:
    # - phonetic: pink
    # - orthographic: yellow
    phonetic_practice = _build_practice_trials("pink", rng)
    phonetic_experimental = _build_experimental_trials("pink", phonetic_practice, rng)

    orthographic_practice = _build_practice_trials("yellow", rng)
    orthographic_experimental = _build_experimental_trials("yellow", orthographic_practice, rng)

    return {
        "phonetic_task_practice": phonetic_practice,
        "phonetic_task_experimental": phonetic_experimental,
        "orthographic_task_practice": orthographic_practice,
        "orthographic_task_experimental": orthographic_experimental,
    }


def construct_multi_task_trial_series() -> dict[str, list[TrialSpec]]:
    """
    Return fixed mixed-task trial series (no runtime generation).

    Keys:
    - multi_task_practice
    - multi_task_experimental_block_1
    - multi_task_experimental_block_2
    """
    return {
        "multi_task_practice": MULTI_TASK_PRACTICE,
        "multi_task_experimental_block_1": MULTI_TASK_EXPERIMENTAL_BLOCK_1,
        "multi_task_experimental_block_2": MULTI_TASK_EXPERIMENTAL_BLOCK_2,
    }
