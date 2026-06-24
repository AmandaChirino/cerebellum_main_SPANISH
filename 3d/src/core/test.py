# ./src/core/test.py
"""
Experimental blocks for the imported 3D mental‑rotation task (template format).

This overwrites the template's test logic to reproduce the
`imported_project` behavior while keeping the surrounding template API
unchanged. It can run one phase at a time (test1 or test2)
or both phases when called with any other phase name.

- PID suffix mod 4 controls mapping and test object order:
  remainders 1/2 use IDs 1-6 then 7-12; remainders 3/0 reverse them.

Correct normal/mirrored answers are parsed from stimulus filenames. No feedback
is shown in test phases. Results are saved through the template's `update_save`.
"""



from __future__ import annotations
from pathlib import Path
import pygame
import datetime

import utils.config as cfg
from utils.logger import get_logger
from utils.event_handler import EventHandler
from utils.paths import FIXATION_CROSS_IMAGE, mapping_image_path
from utils.stimuli import answer_for_option, load_balanced_stimuli, option_for_answer
from ui.pygame_render import (
    toggle_full_screen,
    place_image,
    place_stimulus_with_mapping,
)
from utils.saves import update_save


logger = get_logger("./src/core/test")

def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _draw_fixation_cross(screen: pygame.Surface) -> None:
    """
    Draw fixation cross using the shared image when available.

    :return: None
    """
    if FIXATION_CROSS_IMAGE.exists():
        place_image(screen, FIXATION_CROSS_IMAGE, fit_mode="contain")
    else:
        screen.fill(cfg.BLACK_RGB)
    pygame.display.flip()


def run_test(
    screen: pygame.Surface,
    test_phase: str,
    stimuli: list[Path],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run one or both experimental phases using parsed stimulus filenames.

    The `stimuli` parameter is ignored but kept for API compatibility.
    """
    all_phases = ("test1", "test2")
    phases = (test_phase,) if test_phase in all_phases else all_phases

    MAX_RESP_MS = 12000
    FIX_MS = cfg.FIXATION_CROSS
    ISI_MS = 500

    for test_name in phases:
        try:
            trials = load_balanced_stimuli(test_name)
        except Exception as e:
            logger.error(f"Failed to load test stimuli for {test_name}: {e}")
            continue

        for trial in trials:
            stim_path: Path = trial.stimuli_path

            # ISI
            screen.fill(cfg.BLACK_RGB)
            pygame.display.flip()
            _flush_input()
            pygame.time.delay(ISI_MS)

            # Fixation
            _draw_fixation_cross(screen)
            _flush_input()
            pygame.time.delay(FIX_MS)

            # Stimulus on top of the full-screen mapping cue.
            event_handler.reset_trial_input()
            place_stimulus_with_mapping(screen, stim_path, mapping_image_path())

            pygame.display.flip()

            # Response
            t0 = pygame.time.get_ticks()
            option_selected: int | None = None
            reaction_time = MAX_RESP_MS

            while True:
                state = event_handler.poll()

                if state.quit:
                    pygame.quit()
                    raise SystemExit

                if state.toggle_full_screen:
                    pygame.event.clear()
                    screen = toggle_full_screen(screen)
                    pygame.event.clear()
                    place_stimulus_with_mapping(screen, stim_path, mapping_image_path())
                    pygame.display.flip()
                    _flush_input()

                elapsed = pygame.time.get_ticks() - t0

                if state.option_1:
                    option_selected = 1
                    reaction_time = elapsed
                    break

                if state.option_2:
                    option_selected = 2
                    reaction_time = elapsed
                    break

                if elapsed >= MAX_RESP_MS:
                    break

                pygame.time.delay(1)

            _flush_input()

            # Evaluate against filename-derived normal/mirrored answer.
            correct_answer = trial.correct_answer
            if option_selected is None:
                correct_flag: int | None = None
                result = "timeout"
            else:
                selected_answer = answer_for_option(option_selected)
                correct_flag = 1 if selected_answer == correct_answer else 0
                result = "correct" if correct_flag == 1 else "incorrect"

            logger.info(
                "TRIAL_RESULT | test=%s | stim=%s | response=%s | result=%s | reaction_time_ms=%d",
                test_name,
                Path(stim_path).name,
                ("d" if option_selected == 1 else ("k" if option_selected == 2 else "None")),
                result,
                reaction_time,
            )

            # Save
            cfg._end_time = datetime.datetime.now().isoformat()
            key_response = "d" if option_selected == 1 else ("k" if option_selected == 2 else "")
            joy_response = "left" if option_selected == 1 else ("right" if option_selected == 2 else "")
            correct_option = option_for_answer(correct_answer)
            key_correct = "d" if correct_option == 1 else "k"
            joy_correct = "left" if correct_option == 1 else "right"

            update_save(
                block_name=test_name,
                trial_type="experimental",
                object_id=trial.item_id,
                condition=trial.condition,
                rotation_angle=trial.rotation_angle,
                angle=trial.rotation_angle,
                key_correct=key_correct,
                key_response=key_response,
                joy_correct=joy_correct,
                joy_response=joy_response,
                correct=correct_flag,
                reaction_time=reaction_time if option_selected is not None else None,
                stimulus_path=str(stim_path),
            )
            cfg._start_time = datetime.datetime.now().isoformat()

    return screen
