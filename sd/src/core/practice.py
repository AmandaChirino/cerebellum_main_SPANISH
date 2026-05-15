# ./src/core/test.py
"""
Practice block execution logic using pygame.

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
    show_feedback,
)
from ui.display_word import show_word, show_fixation
from core.saves import update_save


logger = get_logger("./src/core/practice")
def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def run_practice(
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
    shuffled = random.sample(sentences, cfg.STIMULI_COUNT_PRAC)
    acc_counter = 0
    sum_RT = 0

    for sentence_data in shuffled:
        words = sentence_data["words"]
        correct_response = sentence_data["correct_response"]
        
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
        correct = "timeout"
        
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
            
           # elapsed = pygame.time.get_ticks() - t0
            
            if pygame.joystick.get_count() == 0:
                joystick_present = False
            else:
                joystick_present = True
            
            if cfg.MAPPING == 1:
                elapsed = pygame.time.get_ticks() - t0
                if elapsed >= cfg.MAX_RESPONDE_TIME:
                    option_selected = None
                    correct = 0
                    reaction_time = elapsed
                    break
                if state.option_1:  # 'd' = Meaningful
                    if not joystick_present:
                        option_selected = "d"
                    else:
                        option_selected = "left"
                    correct = 1 if (correct_response == "d") else 0
                    reaction_time = elapsed
                    break
                elif state.option_2:  # 'k' = Meaningless
                    if not joystick_present:
                        option_selected = "k"
                    else:
                        option_selected = "right"
                    correct = 1 if (correct_response == "k") else 0
                    reaction_time = elapsed
                    break

            else:
                elapsed = pygame.time.get_ticks() - t0
                if elapsed >= cfg.MAX_RESPONDE_TIME:
                    option_selected = None
                    correct = 0
                    reaction_time = elapsed
                    break
                if state.option_1:  # 'd' = Meaningful in CSV but meaningless in Mapping 2
                    if not joystick_present:
                        option_selected = "d"
                    else:
                        option_selected = "left"
                    # Invert the logic: correct if correct_response == 'k'
                    correct = 1 if (correct_response == "k") else 0
                    reaction_time = elapsed
                    break
                elif state.option_2:  # 'k' = Meaningless in CSV but meaningful in Mapping 2
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
        
        # Prepare correct response for CSV output
        # Translate d/k to left/right for joystick
        joy_correct_response = "NA"  # Default value
        if joystick_present:
            if cfg.MAPPING == 1:
                joy_correct_response = "left" if correct_response == "d" else "right"
            else:
                joy_correct_response = "right" if correct_response == "d" else "left"

        # Handle timeout case for CSV output
        if option_selected is None:
            key_resp = "NA"
            joy_resp = "NA"
        else:
            if joystick_present:
                key_resp = "NA"
                joy_resp = option_selected
            else:
                key_resp = option_selected
                joy_resp = "NA"

        # Log result
        logger.info(
            "TRIAL_RESULT | block=%s | condition=%s | predictability=%s | "
            "cloze_prob=%.2f | meaningful=%s | target_word=%s | response=%s | status=%s | reaction_time_ms=%d",
            block,
            sentence_data["condition"],
            sentence_data["cloze_probability"],
            sentence_data["meaningful"],
            sentence_data["last_word"],
            option_selected if option_selected is not None else "None",
            correct,
            reaction_time,
        )

        typeblock = "practice"

        if correct == "timeout":
            acc_counter += 0
        else:
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
            key_corr=(correct_response if not joystick_present else "NA"),
            key_resp=key_resp,
            joy_corr=(joy_correct_response if joystick_present else "NA"),
            joy_resp=joy_resp,
        )

        accuracy = f"{(acc_counter/cfg.STIMULI_COUNT_PRAC)*100:.2f}"
        avg_RT = f"{(sum_RT/cfg.STIMULI_COUNT_PRAC)/1000:.2f}"

        # Restaurar feedback visual de Timeout en amarillo si no hubo respuesta
        if option_selected is None:
            show_feedback(screen, "timeout")
        else:
            show_feedback(screen, correct)
        pygame.display.flip()
        pygame.time.delay(cfg.FB_DURATION)
        _flush_input()

    return screen, accuracy, avg_RT
