# ./src/core/practice.py
"""
Practice block execution logic using pygame.
"""

from __future__ import annotations

import random
import pygame
from pathlib import Path

import utils.config as cfg
from utils.logger import get_logger
from utils.event_handler import EventHandler
from utils.saves import update_save
from ui.pygame_renderer import (
    toggle_full_screen,
    show_ied_ui,
    place_single_image,
    show_feedback,
)


logger = get_logger("./src/core/practice")


def _flush_input() -> None:
    """Flush all pending pygame input events."""
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _response_from_state(state) -> tuple[int | None, str | None, str | None]:
    if state.up:
        return 1, "up", state.input_source
    if state.down:
        return 2, "down", state.input_source
    if state.left:
        return 3, "left", state.input_source
    if state.right:
        return 4, "right", state.input_source
    return None, None, None


def _correct_dir_from_index(correct_ind: int | None) -> str | None:
    mapping = {1: "up", 2: "down", 3: "left", 4: "right"}
    return mapping.get(correct_ind)


def run_practice_phase(
    screen: pygame.Surface,
    phase: str,
    stimuli: dict[str, "Path"],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run one practice phase (PRACTICE1 / PRACTICE2).
    Automatically quit when reaching PRACTICE_TRIAL_REQUIREMENT trials.
    """
    running = True
    waiting = True
    trial_start: int | None = None
    clock = pygame.time.Clock()
    feedback_until = 0
    feedback_is_correct = None

    correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
    cfg.correct_ind = correct_ind
    cfg.trial_count = 0

    while running:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()

        if waiting:
            response, response_dir, input_source = _response_from_state(state)
            if response is not None and response in (correct_ind, incorrect_ind):
                correct_dir = _correct_dir_from_index(cfg.correct_ind)
                correct_img = stimuli[f"{phase}_CORRECT"]
                incorrect_img = stimuli[f"{phase}_INCORRECT"]
                reaction_time = pygame.time.get_ticks() - trial_start if trial_start is not None else None
                if response == cfg.correct_ind:
                    feedback_is_correct = True
                    cfg.trial_count += 1
                    update_save(phase, 1, correct_dir, response_dir, input_source, 
                                str(correct_img.name), str(incorrect_img.name),
                                reaction_time=reaction_time)
                else:
                    feedback_is_correct = False
                    cfg.trial_count += 1
                    update_save(phase, 0, correct_dir, response_dir, input_source,
                                str(correct_img.name), str(incorrect_img.name),
                                reaction_time=reaction_time)
                feedback_until = pygame.time.get_ticks() + cfg.FB_DURATION
                waiting = False

        show_ied_ui(screen)
        correct_img = stimuli[f"{phase}_CORRECT"]
        incorrect_img = stimuli[f"{phase}_INCORRECT"]
        place_single_image(screen, correct_img, correct_ind)
        place_single_image(screen, incorrect_img, incorrect_ind)

        now = pygame.time.get_ticks()
        if feedback_is_correct is not None:
            if now < feedback_until:
                show_feedback(screen, feedback_is_correct)
            else:
                feedback_is_correct = None
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.wait(cfg.ISI_MS)
                pygame.event.clear()
                correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
                cfg.correct_ind = correct_ind
                waiting = True
                trial_start = None

                if cfg.trial_count >= cfg.PRACTICE_TRIAL_REQUIREMENT:
                    if pygame.time.get_ticks() >= feedback_until:
                        logger.info("Passed phase %s", phase)
                        running = False

        pygame.display.flip()
        if waiting and trial_start is None:
            trial_start = pygame.time.get_ticks()
        clock.tick(60)

    return screen
