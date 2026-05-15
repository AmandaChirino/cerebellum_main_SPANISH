# ./src/core/pull_stimuli.py
"""
Deterministic stimulus sequence generation for n-back tasks.

Generates sequences with exact target counts and validated constraints:
- Practice blocks: 3 targets per 10 trials
- Experimental blocks: 6 targets per block (21-23 trials depending on n-level)
- Maximum 3 consecutive repetitions of any stimulus
- Automatic n-back rule validation
"""

from __future__ import annotations
from pathlib import Path
from typing import Tuple
import random

import utils.config as cfg
from utils.logger import get_logger
from utils.paths import STIMULI


logger = get_logger("./src/core/pull_stimuli")


def _is_practice_block(trial_num: int) -> bool:
    """
    Determine if block is practice based on trial count.
    
    :param trial_num: Number of trials in the block
    :type trial_num: int
    
    :return: True if practice block, False if experimental
    :rtype: bool
    """
    return trial_num == 10


def _create_deterministic_sequence(n_back_level: int, total_trials: int, target_count: int) -> Tuple[list[Path], list[bool]]:
    """
    Generate stimulus sequence with exact target count and repetition constraints.
    
    Uses iterative generation until valid sequence found:
    1. Generate random sequence
    2. Identify targets based on n-back rule
    3. Validate target count matches requirement
    4. Validate no more than MAX_CONSECUTIVE_REPEATS consecutive repetitions
    
    :param n_back_level: N-back level (1, 2, or 3)
    :type n_back_level: int
    
    :param total_trials: Total number of trials in sequence
    :type total_trials: int
    
    :param target_count: Required number of targets
    :type target_count: int
    
    :return: Tuple of (stimulus_paths, match_map)
    :rtype: Tuple[list[Path], list[bool]]
    """
    all_stimuli = list(STIMULI)
    
    while True:
        sequence = [random.choice(all_stimuli) for _ in range(total_trials)]
        
        # Identify targets based on n-back rule
        found_targets = 0
        target_positions = []
        
        for pos in range(n_back_level, len(sequence)):
            if sequence[pos] == sequence[pos - n_back_level]:
                found_targets += 1
                target_positions.append(pos)
        
        # Validate exact target count
        if found_targets != target_count:
            continue
            
        # Validate consecutive repetition constraint
        has_too_many_repeats = False
        for i in range(len(sequence) - cfg.MAX_CONSECUTIVE_REPEATS):
            consecutive_same = all(
                sequence[i] == sequence[i + j] 
                for j in range(1, cfg.MAX_CONSECUTIVE_REPEATS + 1)
            )
            if consecutive_same:
                has_too_many_repeats = True
                break
        
        if has_too_many_repeats:
            continue
            
        # Valid sequence found - generate match map
        match_map = [i in target_positions for i in range(total_trials)]
        
        logger.info(f"{n_back_level}-back: {found_targets} targets in {total_trials} trials")
        return sequence, match_map


def pull_stimuli_1back(trial_num: int) -> Tuple[list[Path], list[bool]]:
    """
    Generate deterministic stimulus sequence for 1-back.
    
    Practice: 3 targets in 10 trials
    Experimental: 6 targets in 21 trials
    
    :param trial_num: Number of trials
    :type trial_num: int
    
    :return: Tuple of (stimulus_paths, match_map)
    :rtype: Tuple[list[Path], list[bool]]
    """
    target_count = 3 if _is_practice_block(trial_num) else cfg.TARGETS_PER_BLOCK
    return _create_deterministic_sequence(1, trial_num, target_count)


def pull_stimuli_2back(trial_num: int) -> Tuple[list[Path], list[bool]]:
    """
    Generate deterministic stimulus sequence for 2-back.
    
    Practice: 3 targets in 10 trials
    Experimental: 6 targets in 22 trials
    
    :param trial_num: Number of trials
    :type trial_num: int
    
    :return: Tuple of (stimulus_paths, match_map)
    :rtype: Tuple[list[Path], list[bool]]
    """
    target_count = 3 if _is_practice_block(trial_num) else cfg.TARGETS_PER_BLOCK
    return _create_deterministic_sequence(2, trial_num, target_count)


def pull_stimuli_3back(trial_num: int) -> Tuple[list[Path], list[bool]]:
    """
    Generate deterministic stimulus sequence for 3-back.
    
    Practice: 3 targets in 10 trials
    Experimental: 6 targets in 23 trials
    
    :param trial_num: Number of trials
    :type trial_num: int
    
    :return: Tuple of (stimulus_paths, match_map)
    :rtype: Tuple[list[Path], list[bool]]
    """
    target_count = 3 if _is_practice_block(trial_num) else cfg.TARGETS_PER_BLOCK
    return _create_deterministic_sequence(3, trial_num, target_count)
