"""Stimulus condition tables migrated from CSV files.

This module replaces the legacy CSV condition files with in-code constants.
Only conditions used by the target 2-block design are kept:
- practice
- experimental block A
- experimental block B

All stimulus paths here are filenames under `resources/stimuli`.
Separate demo/short-test image folders are no longer used.

Version-specific key mapping is derived at runtime:
- version 1: normal -> d, mirrored -> k
- version 2: normal -> k, mirrored -> d
"""

from __future__ import annotations

from pathlib import Path
import re


_BASE_COLUMNS = (
    "letter_name",
    "rotation_angle",
    "condition",
    "difficulty",
    "stimuli_path",
)


def _key_for_condition(condition: str, version: int) -> str:
    if version not in (1, 2):
        raise ValueError(f"Unsupported version: {version}")

    if condition not in ("normal", "mirrored"):
        raise ValueError(f"Unsupported condition: {condition}")

    if version == 1:
        return "d" if condition == "normal" else "k"
    return "k" if condition == "normal" else "d"


def _materialize(base_rows: list[tuple], version: int, script_dir: Path | None) -> list[dict]:
    items: list[dict] = []
    for letter_name, rotation_angle, condition, difficulty, stimuli_relpath in base_rows:
        stimuli_path = str((script_dir / stimuli_relpath).resolve()) if script_dir else stimuli_relpath
        items.append(
            {
                "letter_name": letter_name,
                "rotation_angle": rotation_angle,
                "mirrored": condition == "mirrored",
                "condition": condition,
                "difficulty": difficulty,
                "stimuli_path": stimuli_path,
                "key_correct": _key_for_condition(condition, version),
            }
        )
    return items


def get_conditions(phase: str, version: int, script_dir: Path | None = None) -> list[dict]:
    """Return condition rows for a phase and counterbalance version.

    Supported phase labels:
      - practice                uses ``version`` parameter as-is
      - experimental_block_1   block presented FIRST to this participant
      - experimental_block_2   block presented SECOND to this participant
      - experimental_block_3   block presented THIRD to this participant

    For experimental blocks the ``version`` parameter is ignored; the correct
    joystick mapping is derived automatically from ``utils.config.PID``
    (even PID → version 2 / Normal=Right, odd PID → version 1 / Normal=Left)
    and cached for the whole session.  ``cfg.MAPPING`` is updated as a
    side-effect so the saved CSV always reflects the actual version used.
    Trial order within each block is determined at generation time by a
    constrained shuffle (see _constrained_shuffle).
    """
    if phase == "practice":
        return _materialize(PRACTICE_BASE, version, script_dir)
    elif phase in ("experimental_block_1", "experimental_block_2", "experimental_block_3"):
        blk1, blk2, blk3, auto_version = _get_session_blocks()
        if phase == "experimental_block_1":
            base = blk1
        elif phase == "experimental_block_2":
            base = blk2
        else:
            base = blk3
        return _materialize(base, auto_version, script_dir)
    else:
        raise ValueError(f"Unsupported phase: {phase}")


PRACTICE_BASE: list[tuple[str, int, str, int, str]] = [
    ('G',    0, 'normal',   0,  'G_0.png'),
    ('F',  -15, 'mirrored', 15, 'F_-15_M.png'),
    ('J',  -75, 'mirrored', 75, 'J_-75_M.png'),
    ('J', -105, 'normal',  105, 'J_-105.png'),
    ('J',  105, 'normal',  105, 'J_105.png'),
    ('R',   45, 'normal',   45, 'R_45.png'),
    ('G',  -45, 'mirrored', 45, 'G_-45_M.png'),
    ('F',   75, 'normal',   75, 'F_75.png'),
    ('R',  -15, 'mirrored', 15, 'R_-15_M.png'),
    ('G',  135, 'mirrored',135, 'G_135_M.png'),
]

# ──────────────────────────────────────────────────────────────────────────────
# Strictly counterbalanced factorial design — 144 trials across 3 × 48-trial blocks
#
# BLOCK A & B (complementary pair, 48 trials each):
#   • 40 non-zero : 4 letters × 5 magnitudes × 2 conditions
#     Sign (+/−) is assigned at the (letter, magnitude) level at random per
#     session; Block B always receives the complementary sign.
#     → Across A+B: 80 unique (letter, signed_angle, condition) combinations.
#   • 8 zero : 4 letters × 2 conditions × 1 rep per block.
#
# BLOCK C (condition-flipped replica of Block A, 48 trials):
#   • 40 non-zero : same (letter, signed_angle) pairs as Block A, but with
#     condition flipped (normal ↔ mirrored).
#   • 8 zero : 4 letters × 2 conditions × 1 rep (3rd repetition overall).
#   → Block C shares no (letter, signed_angle, condition) tuple with Block B.
#
# Per block (48 trials):  24 Normal + 24 Mirrored  |  12 per letter
#                         20 negative + 20 positive + 8 zero
#
# Subject-based counterbalancing (trailing digits of cfg.PID):
#   Even PID → version 2 (Normal → key k)
#   Odd  PID → version 1 (Normal → key d)
#   Block order is always A → B → C.  Since sign assignment is random per
#   session, block order provides no systematic advantage and needs no
#   counterbalancing.
#
# Constrained shuffle (applied at generation time per block):
#   • Max 2 consecutive trials of the same condition (run of 3+ forbidden)
#   • Max 3 consecutive trials of the same letter   (run of 4+ forbidden)
#   • First and last trial of each block must not be 0°
#
# cfg.MAPPING is auto-set to the derived version on first access, so the
# response-key display and saved CSV reflect the actual counterbalance used.
# ──────────────────────────────────────────────────────────────────────────────

import random as _random

_N = 'normal'
_M = 'mirrored'

_LETTERS    = ('F', 'G', 'J', 'R')
_MAGNITUDES = (15, 45, 75, 105, 135)


def _fname(letter: str, angle: int, condition: str) -> str:
    suffix = '_M' if condition == _M else ''
    return f'{letter}_{angle}{suffix}.png'


def _extract_pid_number(pid: str | None) -> int:
    """Return the trailing integer from a PID string (e.g. 'amanda02' → 2).

    Returns 0 (even/default) if no trailing digits are found.
    """
    match = re.search(r"\d+$", (pid or "").strip())
    return int(match.group()) if match else 0


def mapping_from_pid(pid: str | None) -> int:
    """Derive the 2D mapping version from the participant ID.

    Rule:
    - even trailing digit (or no digits) -> version 2
    - odd trailing digit -> version 1
    """
    pid_num = _extract_pid_number(pid)
    return 1 if (pid_num % 2 == 1) else 2


def _constrained_shuffle(trials: list[tuple]) -> list[tuple]:
    """Return a shuffled copy of *trials* satisfying run-length/boundary rules.

    Constraints enforced:
      • Max 2 consecutive trials with the same condition (run of 3+ forbidden).
      • Max 3 consecutive trials of the same letter   (run of 4+ forbidden).
      • First and last trials must not be 0°.

    Uses rejection sampling.  Raises RuntimeError if no valid order is found
    within MAX_ATTEMPTS iterations (should never happen for a 48-trial block).
    """
    MAX_ATTEMPTS = 500_000
    t = trials.copy()
    for _ in range(MAX_ATTEMPTS):
        _random.shuffle(t)
        # Boundary: no 0° at either end
        if t[0][1] == 0 or t[-1][1] == 0:
            continue
        # Run-length checks
        ok = True
        for i in range(2, len(t)):
            if t[i][2] == t[i - 1][2] == t[i - 2][2]:                    # 3+ same cond
                ok = False
                break
            if i >= 3 and t[i][0] == t[i-1][0] == t[i-2][0] == t[i-3][0]:  # 4+ same letter
                ok = False
                break
        if ok:
            return t
    raise RuntimeError(
        "_constrained_shuffle: could not satisfy run-length constraints after "
        f"{MAX_ATTEMPTS} attempts.  Check trial pool composition."
    )


def _validate_block(block: list[tuple], label: str) -> None:
    """Assert all structural invariants of a 48-trial experimental block."""
    assert len(block) == 48, \
        f"{label}: expected 48 trials, got {len(block)}"

    norm = sum(1 for r in block if r[2] == _N)
    mirr = sum(1 for r in block if r[2] == _M)
    assert norm == 24 and mirr == 24, \
        f"{label}: expected 24 Normal + 24 Mirrored, got {norm}N / {mirr}M"

    for letter in _LETTERS:
        n = sum(1 for r in block if r[0] == letter)
        assert n == 12, f"{label}: letter '{letter}' expected 12 trials, got {n}"

    zeros = sum(1 for r in block if r[1] == 0)
    assert zeros == 8, f"{label}: expected 8 zero-degree trials, got {zeros}"

    neg = sum(1 for r in block if r[1] < 0)
    pos = sum(1 for r in block if r[1] > 0)
    assert neg == 20 and pos == 20, \
        f"{label}: expected 20 negative + 20 positive, got {neg} neg / {pos} pos"

    # Condition run-length
    for i in range(2, len(block)):
        assert not (block[i][2] == block[i-1][2] == block[i-2][2]), \
            f"{label}: condition run ≥3 starting at index {i}"

    # Boundary
    assert block[0][1]  != 0, f"{label}: first trial must not be 0°"
    assert block[-1][1] != 0, f"{label}: last trial must not be 0°"


def _generate_session_blocks(
    pid: str | None,
) -> tuple[list[tuple], list[tuple], int]:
    """Build a counterbalanced, constrained-shuffled block pair for this session.

    Parameters
    ----------
    pid :
        Participant ID (e.g. ``'amanda02'``).  Trailing digits determine
        even/odd counterbalancing.  ``None`` or digit-free strings → pid_num=0
        (treated as even).

    Returns
    -------
    (phase1_block, phase2_block, version)
        *phase1_block* is the block the participant experiences first;
        *phase2_block* is second.  Both are already constrained-shuffled.
        *version*: 2 for even PIDs (Normal → key 'k'), 1 for odd (Normal → 'd').
    """
    version = mapping_from_pid(pid)

    # ── Build canonical block pair (block_a, block_b) ───────────────────────────
    # Sign is assigned at the (letter, magnitude) level — not per condition —
    # so that both conditions for a given (letter, mag) share the same sign in
    # block_a (and the opposite in block_b).  Exactly 10 of the 20 (letter, mag)
    # pairs receive a negative sign in block_a, guaranteeing exactly
    # 20 negative + 20 positive non-zero trials in every block regardless of
    # random outcome.  Across both blocks every (letter, signed_angle, condition)
    # appears exactly once (80 unique non-zero combinations total).
    import itertools as _it
    _all_letter_mag = list(_it.product(_LETTERS, _MAGNITUDES))  # 20 pairs
    _random.shuffle(_all_letter_mag)
    _neg_in_a: set[tuple] = set(map(tuple, _all_letter_mag[:10]))   # 10 → negative

    block_a: list[tuple] = []
    block_b: list[tuple] = []

    for letter in _LETTERS:
        for mag in _MAGNITUDES:
            a_angle = -mag if (letter, mag) in _neg_in_a else mag
            b_angle = -a_angle                                    # always complement
            for cond in (_N, _M):
                block_a.append((letter, a_angle, cond, mag, _fname(letter, a_angle, cond)))
                block_b.append((letter, b_angle, cond, mag, _fname(letter, b_angle, cond)))

        # 0°: one Normal + one Mirrored per letter in EACH block
        block_a.append((letter, 0, _N, 0, _fname(letter, 0, _N)))
        block_a.append((letter, 0, _M, 0, _fname(letter, 0, _M)))
        block_b.append((letter, 0, _N, 0, _fname(letter, 0, _N)))
        block_b.append((letter, 0, _M, 0, _fname(letter, 0, _M)))

    # ── Block order ────────────────────────────────────────────────────────────
    # Block A is always presented first, Block B second.
    # Since sign assignment is random per session, block order has no systematic
    # effect across subjects — only the key-mapping version (par/impar) is
    # counterbalanced via PID.
    phase1_raw, phase2_raw = block_a, block_b

    # ── Constrained shuffle ─────────────────────────────────────────────────────
    phase1 = _constrained_shuffle(phase1_raw)
    phase2 = _constrained_shuffle(phase2_raw)

    # ── Build Block C ─────────────────────────────────────────────────────────
    # 1. Rotated trials (40): same letter + signed angle from block_a, flipped condition
    block_c_raw: list[tuple] = []
    for r in block_a:
        letter, angle, cond, difficulty, _ = r
        if angle != 0:
            flip_cond = _M if cond == _N else _N
            block_c_raw.append((letter, angle, flip_cond, difficulty, _fname(letter, angle, flip_cond)))

    # 2. Zero-degree trials (8): 3rd repetition of all 8 unique zero-degree cells
    for letter in _LETTERS:
        block_c_raw.append((letter, 0, _N, 0, _fname(letter, 0, _N)))
        block_c_raw.append((letter, 0, _M, 0, _fname(letter, 0, _M)))

    # 3. Constrained shuffle
    phase3 = _constrained_shuffle(block_c_raw)

    # ── Structural validation (asserts) ───────────────────────────────────────
    _validate_block(phase1, "Phase-1 block")
    _validate_block(phase2, "Phase-2 block")
    _validate_block(phase3, "Phase-3 block")

    all_nonzero = [(r[0], r[1], r[2]) for r in phase1 + phase2 if r[1] != 0]
    assert len(set(all_nonzero)) == len(all_nonzero) == 80, (
        f"Expected 80 unique non-zero (letter, signed_angle, condition) tuples; "
        f"got {len(set(all_nonzero))} unique out of {len(all_nonzero)}."
    )

    # ── Block C internal balance ───────────────────────────────────────────────
    from collections import Counter as _Counter
    assert len(phase3) == 48
    assert sum(1 for t in phase3 if t[2] == _N) == 24
    assert sum(1 for t in phase3 if t[2] == _M) == 24
    assert all(v == 12 for v in _Counter(t[0] for t in phase3).values())
    assert sum(1 for t in phase3 if t[1] == 0) == 8
    assert sum(1 for t in phase3 if t[1] > 0) == 20
    assert sum(1 for t in phase3 if t[1] < 0) == 20

    # No exact rotated trial repeated between any pair of blocks
    # NOTE: Block A has both conditions per (letter, angle), so after flipping
    # conditions Block C's rotated set is IDENTICAL to Block A's — that is the
    # correct invariant.  Block B uses the opposite angle signs, so its rotated
    # set is provably disjoint from Block C's.
    def _rotated_set(block: list[tuple]) -> set:
        return {(t[0], t[1], t[2]) for t in block if t[1] != 0}

    assert _rotated_set(block_a) == _rotated_set(phase3), \
        "Block C rotated set must equal Block A rotated set (same angles, flipped conditions cancel out)"
    assert len(_rotated_set(block_b) & _rotated_set(phase3)) == 0, \
        "Block B and Block C must not share any rotated (letter, angle, condition) tuple"

    # Global count
    all_trials = phase1 + phase2 + phase3
    assert len(all_trials) == 144

    return phase1, phase2, phase3, version


# Session cache — generated once on first access, stable for the whole session.
_SESSION_BLOCKS: tuple[list[tuple], list[tuple], list[tuple], int] | None = None


def _get_session_blocks() -> tuple[list[tuple], list[tuple], list[tuple], int]:
    """Return the cached (phase1, phase2, phase3, version) quad, generating if needed.

    Reads ``utils.config.PID`` for the participant ID and writes the derived
    ``version`` back to ``cfg.MAPPING`` so the rest of the experiment uses the
    correct response-key labels without any additional configuration.
    """
    global _SESSION_BLOCKS
    if _SESSION_BLOCKS is None:
        import utils.config as _cfg          # lazy import — avoids circular deps
        _SESSION_BLOCKS = _generate_session_blocks(_cfg.PID)
        _cfg.MAPPING = _SESSION_BLOCKS[3]    # propagate version to config
    return _SESSION_BLOCKS


def reset_session_blocks() -> None:
    """Force regeneration of the block triple (useful for testing / new session)."""
    global _SESSION_BLOCKS
    _SESSION_BLOCKS = None
