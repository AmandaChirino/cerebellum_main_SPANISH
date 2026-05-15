# ./src/core/test.py
"""
Test block execution logic using pygame.

This module presents randomized stimulus blocks, collects keyboard responses with timeout handling, and optionally displays feedback during practice trials.
"""


# TODO: Modify block design based on needs

from __future__ import annotations
from pathlib import Path
import pygame
import random
import datetime

import utils.config as cfg
from utils.logger import get_logger
from utils.event_handler import EventHandler
from ui.pygame_render import (
    toggle_full_screen,
)
from ui.display_word import show_word, show_fixation
from core.saves import update_save


logger = get_logger("./src/core/test")

def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def run_test(
    screen: pygame.Surface,
    block: str,
    sentences: list[dict],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run a stimulus block once (each stimulus exactly once, randomized order).

    During each stimulus:
    - Wait for 'd' / 'k' response within cfg.MAX_REACTION_TIME ms
    - If timeout: outcome = "timeout"
    - If response: outcome = "correct"/"incorrect" based on mapping rule
    - Practice: show_feedback for cfg.FB_DURATION ms
    - Test: no feedback

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param block: Name of the block
    :type block: str

    :param stimuli: List of stimulus image paths
    :type stimuli: list[pathlib.Path]

    :param event_handler: Centralized event handler instance
    :type event_handler: EventHandler

    :return: Active display surface after the block (may be updated by fullscreen toggle)
    :rtype: pygame.Surface
    """
    shuffled = random.sample(sentences, cfg.STIMULI_COUNT_EXPERIMENTAL)
    acc_counter = 0
    sum_RT = 0

    for sentence_data in shuffled:
        words = sentence_data["words"]
        condition = sentence_data["condition"]
        correct_response = sentence_data["correct_response"]
        meaningful = sentence_data["meaningful"]
        cloze = sentence_data["cloze_probability"]
        
        # Fixation cross
        show_fixation(screen)
        _flush_input()
        pygame.time.delay(cfg.FIXATION_CROSS)
        
        starting = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Present words sequentially (all except last)
        for word in words[:-1]:
            show_word(screen, word, is_target=False)
            _flush_input()
            pygame.time.delay(cfg.WORD_PRESENTATION)
        
        # Present target word (last word) and collect response
        target_word = words[-1]
        show_word(screen, target_word, is_target=True)
        _flush_input()
        
        t0 = pygame.time.get_ticks()
        option_selected: str | None = None
        reaction_time = cfg.TARGET_WORD_DURATION
        correct = 0  # Default to incorrect/timeout
        
        # Response collection loop
        while True:
            state = event_handler.poll()
            
            if state.quit:
                pygame.quit()
                raise SystemExit
            
            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                show_word(screen, target_word, is_target=True)
                _flush_input()
            
            # Check if joystick is present
            if pygame.joystick.get_count() == 0:
                joystick_present = False
            else:
                joystick_present = True
            
            elapsed = pygame.time.get_ticks() - t0
            if elapsed >= cfg.MAX_RESPONDE_TIME:
                # Timeout - no response given
                option_selected = None
                correct = 0
                reaction_time = elapsed
                break
            
            if cfg.MAPPING == 1:
                # Mapping 1: d/left = meaningful, k/right = meaningless
                if state.option_1:  # 'd' pressed or joystick left
                    if not joystick_present:
                        option_selected = "d"
                    else:
                        option_selected = "left"
                    correct = 1 if (correct_response == "d") else 0
                    reaction_time = elapsed
                    break
                elif state.option_2:  # 'k' pressed or joystick right
                    if not joystick_present:
                        option_selected = "k"
                    else:
                        option_selected = "right"
                    correct = 1 if (correct_response == "k") else 0
                    reaction_time = elapsed
                    break

            else:
                # Mapping 2: d/left = meaningless, k/right = meaningful
                if state.option_1:  # 'd' pressed or joystick left
                    if not joystick_present:
                        option_selected = "d"
                    else:
                        option_selected = "left"
                    # Invert the logic: correct if correct_response == 'k'
                    correct = 1 if (correct_response == "k") else 0
                    reaction_time = elapsed
                    break
                elif state.option_2:  # 'k' pressed or joystick right
                    if not joystick_present:
                        option_selected = "k"
                    else:
                        option_selected = "right"
                    # Invert the logic: correct if correct_response == 'd'
                    correct = 1 if (correct_response == "d") else 0
                    reaction_time = elapsed
                    break
        
        # Lock input immediately after a decision/timeout (prevents double-response leakage)
        _flush_input()

        # Prepare correct response values for logging
        # Translate d/k to left/right for joystick display
        joy_correct_response = "NA"  # Default value
        if joystick_present:
            if cfg.MAPPING == 1:
                # Mapping 1: d=left (meaningful), k=right (meaningless)
                joy_correct_response = "left" if correct_response == "d" else "right"
            else:
                # Mapping 2: d=left (meaningless), k=right (meaningful)
                # In Mapping 2, the semantic meaning is inverted:
                # correct_response="d" means meaningful, which maps to k/right in Mapping 2
                joy_correct_response = "right" if correct_response == "d" else "left"
        
        # Handle timeout case
        if option_selected is None:
            # Timeout - no response given
            key_resp = "NA"
            joy_resp = "NA"
            key_corr = correct_response if not joystick_present else "NA"
            joy_corr = joy_correct_response if joystick_present else "NA"
        else:
            # Response was given
            if joystick_present:
                key_resp = "NA"
                key_corr = "NA"
                joy_resp = option_selected
                joy_corr = joy_correct_response
            else:
                key_resp = option_selected
                key_corr = correct_response
                joy_resp = "NA"
                joy_corr = "NA"

        # Log result
        logger.info(
            f"TRIAL_RESULT | block={block} | condition={condition} | "
            f"cloze_prob={cloze} | target_word={target_word} | response={option_selected} | reaction_time_ms={reaction_time}",
        )

        typeblock = "experimental"

        acc_counter += correct
        sum_RT += reaction_time

        # Update save
        update_save(
            block=block,
            type=typeblock,
            starttime=starting,
            endtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            condition=sentence_data["condition"],
            correct=correct,
            reaction_time=reaction_time,
            cloze_probability=sentence_data["cloze_probability"],
            meaningful=sentence_data["meaningful"],
            sentence=sentence_data["sentence"],
            item_og=sentence_data["item_og"],
            last_word=sentence_data["last_word"],
            og_dataset=sentence_data["og_dataset"],
            num_letters=sentence_data["num_letters"],
            word_freq=sentence_data["word_freq"],
            spell_mod=sentence_data["spelling_mod"],
            word_count=sentence_data["word_count"],
            key_corr=key_corr,
            key_resp=key_resp,
            joy_corr=joy_corr,
            joy_resp=joy_resp,
        )

    logger.info({acc_counter})
    accuracy = f"{(acc_counter/cfg.STIMULI_COUNT_EXPERIMENTAL)*100:.2f}"
    avg_RT = f"{(sum_RT/cfg.STIMULI_COUNT_EXPERIMENTAL)/1000:.2f}"
        
    return screen, accuracy, avg_RT