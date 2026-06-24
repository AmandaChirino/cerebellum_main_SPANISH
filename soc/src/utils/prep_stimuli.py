"""
prep_stimuli.py - Build a randomized trial sequence for one session.

Structure:
    - 12 combos: 3 players x 2 conditions x 2 difficulties
    - 20 videos per combo randomly selected -> 240 experimental trials
    - 1 video per combo from the remainder -> 12 practice trials
    - 4 blocks x 5 videos/combo x 12 combos = 60 trials/block
    - Order constraints: <=2 consecutive same player, <=3 consecutive same condition/difficulty
"""

import csv
import random
from collections import defaultdict
from pathlib import Path
import utils.config as cfg
import utils.paths as paths

_PLAYERS = ['DC', 'EW', 'FI']
_CONDITIONS = ['left', 'right']
_DIFFICULTIES = ['hard', 'easy']
_COMBOS = [(p, c, d) for p in _PLAYERS for c in _CONDITIONS for d in _DIFFICULTIES]


def _load_stimuli(csv_path: Path) -> dict:
    groups = defaultdict(list)
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            key = (row['player_name'], row['condition'], row['difficulty'])
            groups[key].append(dict(row))
    return groups


def _select_pool(groups: dict) -> tuple:
    experimental, practice = {}, {}
    for combo in _COMBOS:
        available = groups[combo][:]
        random.shuffle(available)
        experimental[combo] = available[:cfg.VIDEOS_PER_COMBO]
        practice[combo] = available[cfg.VIDEOS_PER_COMBO: cfg.VIDEOS_PER_COMBO + cfg.PRACTICE_PER_COMBO]
    return experimental, practice


def _trailing_count(seq: list, key: str) -> int:
    if not seq:
        return 0
    val = seq[-1][key]
    n = 0
    for item in reversed(seq):
        if item[key] == val:
            n += 1
        else:
            break
    return n


def _valid_next(seq: list, candidate: dict) -> bool:
    if not seq:
        return True
    last = seq[-1]
    if candidate['player_name'] == last['player_name'] and _trailing_count(seq, 'player_name') >= cfg.MAX_CONSEC_PLAYER:
        return False
    if candidate['condition'] == last['condition'] and _trailing_count(seq, 'condition') >= cfg.MAX_CONSEC_CONDITION:
        return False
    if candidate['difficulty'] == last['difficulty'] and _trailing_count(seq, 'difficulty') >= cfg.MAX_CONSEC_DIFFICULTY:
        return False
    return True


def _order_trials(trials: list) -> list:
    for _ in range(cfg.MAX_RETRIES):
        pool = trials[:]
        random.shuffle(pool)
        seq = []
        while pool:
            choices = [t for t in pool if _valid_next(seq, t)]
            if not choices:
                break
            pick = random.choice(choices)
            seq.append(pick)
            pool.remove(pick)
        if not pool:
            return seq
    raise RuntimeError(f"Could not order {len(trials)} trials within {cfg.MAX_RETRIES} attempts.")


def _assign_blocks(experimental: dict) -> list:
    blocks = [[] for _ in range(cfg.NUM_BLOCKS)]
    for combo in _COMBOS:
        videos = experimental[combo][:]
        random.shuffle(videos)
        for i in range(cfg.NUM_BLOCKS):
            blocks[i].extend(videos[i * cfg.TRIALS_PER_BLOCK:(i + 1) * cfg.TRIALS_PER_BLOCK])
    return blocks


def build_trials() -> list:
    """
    Return the full randomized trial list for the current session.

    Each trial is a dict with:
        phase           -- 'practice' or 'block1'-'block4'
        block           -- 0 (practice) or 1-4
        trial_in_phase  -- 1-based index within phase
        video_name, player_name, condition, difficulty
        + all other columns from SOC_stimuli_info.csv
    """
    groups = _load_stimuli(paths.CSV_PATH)
    experimental, practice = _select_pool(groups)

    trials = []

    prac_trials = [row for combo in _COMBOS for row in practice[combo]]
    for i, t in enumerate(_order_trials(prac_trials), start=1):
        trials.append({**t, 'phase': 'practice', 'block': 0, 'trial_in_phase': i})

    for b_idx, block_trials in enumerate(_assign_blocks(experimental), start=1):
        for t_idx, t in enumerate(_order_trials(block_trials), start=1):
            trials.append({**t, 'phase': f'block{b_idx}', 'block': b_idx, 'trial_in_phase': t_idx})

    return trials
