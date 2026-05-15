# ./src/core/test.py
"""
Practice block execution logic using pygame.

This module presents randomized stimulus blocks, collects keyboard responses with timeout handling, and optionally displays feedback during practice trials.
"""



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
    place_image,
    show_feedback,
    _play_beep
)
from utils.paths import FIXATION_CROSS_IMAGE
from utils.saves import update_save


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
    stimuli: list[Path],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run a stimulus block once.

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
    shuffled = random.sample(stimuli, k=len(stimuli))

    for stim_path in shuffled:
        stim_id = int(stim_path.stem)  # 1..5
        correct_response = 1 if (stim_id % 2 == 1) else 2

        # ISI: black screen before first and between stimuli
        screen.fill(cfg.BLACK_RGB)
        pygame.display.flip()
        _flush_input()
        pygame.time.delay(cfg.ISI)

        # Fixation cross
        if FIXATION_CROSS_IMAGE.exists():
            place_image(screen, FIXATION_CROSS_IMAGE, fit_mode="contain")
        else:
            screen.fill(cfg.BLACK_RGB)
        pygame.display.flip()
        _flush_input()
        pygame.time.delay(cfg.FIXATION_CROSS)

        # Stimulus
        place_image(screen, stim_path, None, (400,300))
        pygame.display.flip()
        _flush_input()

        t0 = pygame.time.get_ticks()
        option_selected: int | None = None
        reaction_time = cfg.MAX_RESPONSE_TIME
        result = "timeout"

        while True:
            state = event_handler.poll()

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                place_image(screen, stim_path)
                pygame.display.flip()
                _flush_input()

            elapsed = pygame.time.get_ticks() - t0

            if state.option_1:
                _play_beep()
                option_selected = 1
                result = "correct" if correct_response == 1 else "incorrect"
                reaction_time = elapsed
                break

            if state.option_2:
                _play_beep()
                option_selected = 2
                result = "correct" if correct_response == 2 else "incorrect"
                reaction_time = elapsed
                break

            if elapsed >= cfg.MAX_RESPONSE_TIME:
                break

            pygame.time.delay(1)

        # Lock input immediately after a decision/timeout (prevents double-response leakage)
        _flush_input()

        # Log result
        logger.info(
            "TRIAL_RESULT | block=%s | stim=%s | response=%s | result=%s | reaction_time_ms=%d",
            block,
            stim_path.name,
            option_selected if option_selected is not None else "None",
            result,
            reaction_time,
        )

        cfg._end_time = datetime.datetime.now().isoformat()
        # Update save
        key_response = "d" if option_selected == 1 else "k"
        key_correct = "d" if correct_response == 1 else "k"
        joy_response = "left" if option_selected == 1 else "right"
        joy_correct = "left" if correct_response == 1 else "right"
        update_save("practice", "practice", None, key_correct, key_response, joy_correct, joy_response, result, reaction_time, stim_path)
        cfg._start_time = datetime.datetime.now().isoformat()


        # Show feedback
        show_feedback(screen, result)

        pygame.display.flip()
        pygame.time.delay(cfg.FB_DURATION)
        _flush_input()

    return screen
