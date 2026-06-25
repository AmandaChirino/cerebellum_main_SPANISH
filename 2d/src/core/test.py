"""Experimental block execution for the target mental-rotation task."""

from __future__ import annotations

import random
from pathlib import Path

import pygame

import utils.config as cfg
from ui.pygame_render import place_image, place_mapping_background, toggle_full_screen
from utils.event_handler import EventHandler
from utils.logger import get_logger
from utils.paths import FIXATION_CROSS_IMAGE
from utils.saves import format_time, update_save
from utils.stimuli_conditions import get_conditions
from utils.stimuli_conditions import mapping_from_pid


logger = get_logger("./src/core/test")


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _draw_fixation_cross(screen: pygame.Surface) -> None:
    if FIXATION_CROSS_IMAGE.exists():
        place_image(screen, FIXATION_CROSS_IMAGE, fit_mode="contain")
    else:
        screen.fill(cfg.BLACK_RGB)
    pygame.display.flip()


def run_experimental_block(
    screen: pygame.Surface,
    event_handler: EventHandler,
    phase_label: str,
    block_name: str,
    stimuli_root: Path,
    show_trial_feedback: bool = False,
    break_duration_ms: int = 0,
) -> tuple[pygame.Surface, float]:
    """Run one block and return `(screen, accuracy_percent)`.

    `phase_label` must match `utils.stimuli_conditions.get_conditions`.
    """
    version = cfg.MAPPING if cfg.MAPPING in (1, 2) else mapping_from_pid(cfg.PID)
    conditions = get_conditions(phase_label, version, script_dir=stimuli_root)
    # Trial order is determined by the constrained shuffle in stimuli_conditions.

    correct_flags: list[bool] = []
    block_start_time = format_time()
    global_start_time = format_time(cfg.START_TIME)

    block_map = {
        "practice": "p1",
        "experimental_block_1": "b1",
        "experimental_block_2": "b2",
        "experimental_block_3": "b3",
    }
    block_short = block_map.get(block_name, block_name)
    block_type = "practice" if block_short == "p1" else "experimental"

    for idx, cond in enumerate(conditions, start=1):
        stim_path = Path(cond["stimuli_path"])

        _draw_fixation_cross(screen)
        pygame.time.delay(cfg.FIXATION_CROSS)

        event_handler.reset_trial_input()
        place_mapping_background(screen)
        place_image(
            screen,
            stim_path,
            center=(screen.get_width() / 2, screen.get_height() / 2),
            resize=(200, 200),
            overlay=True,
        )
        pygame.display.flip()

        t0 = pygame.time.get_ticks()

        selected_option: int | None = None
        key_response: str | None = None
        joy_response: str | None = None
        reaction_time = cfg.MAX_RESPONSE_TIME
        result = "timeout"

        while pygame.time.get_ticks() - t0 < cfg.MAX_RESPONSE_TIME:
            state = event_handler.poll()

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                place_mapping_background(screen)
                place_image(
                    screen,
                    stim_path,
                    center=(screen.get_width() / 2, screen.get_height() / 2),
                    resize=(200, 200),
                    overlay=True,
                )
                pygame.display.flip()
                _flush_input()
                continue

            elapsed = pygame.time.get_ticks() - t0
            if state.option_1:
                selected_option = 1
                key_response = cfg.key_for_option(1)
                joy_response = cfg.joy_for_key(key_response)
                reaction_time = elapsed
                break

            if state.option_2:
                selected_option = 2
                key_response = cfg.key_for_option(2)
                joy_response = cfg.joy_for_key(key_response)
                reaction_time = elapsed
                break

            pygame.time.delay(1)

        if selected_option is not None:
            result = "correct" if key_response == cond["key_correct"] else "incorrect"

        correct_val = 1 if result == "correct" else 0
        correct_flags.append(result == "correct")

        
        logger.info(
            "TRIAL_RESULT | block=%s | item=%d | stim=%s | result=%s | rt_ms=%d",
            block_name,
            idx,
            stim_path.name,
            result,
            reaction_time,
        )

        if show_trial_feedback:
            from ui.pygame_render import show_feedback

            show_feedback(screen, result)
            pygame.display.flip()
            pygame.time.delay(cfg.FB_DURATION)

        
        # Persist this trial immediately
        update_save(
            block=block_short,
            block_type=block_type,
            letter=cond["letter_name"],
            condition=cond["condition"],
            rotation_angle=cond["rotation_angle"],
            rotation=cond["difficulty"],
            stimuli_path=cond["stimuli_path"],
            key_correct=cond["key_correct"],
            key_response=key_response,
            joy_correct=cfg.joy_for_key(cond["key_correct"]),
            joy_response=joy_response,
            correct=1 if result == "correct" else 0,
            reaction_time=reaction_time,
            start_time=block_start_time,
            end_time=format_time(),
            gloabl_start_time=global_start_time,
        )

        screen.fill(cfg.BLACK_RGB)
        pygame.display.flip()
        pygame.time.delay(cfg.ISI_TIME)
        _flush_input()


    accuracy = 100.0 * sum(correct_flags) / len(correct_flags) if correct_flags else 0.0
    return screen, accuracy
