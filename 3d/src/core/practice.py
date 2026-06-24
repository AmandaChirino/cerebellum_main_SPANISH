# ./src/core/test.py
"""
Practice block for the imported 3D mental‑rotation task (template format).

This overwrites the template's demo/practice logic to reproduce the
`imported_project` behavior while keeping the surrounding template API
unchanged. Trials are driven by CSV condition files from
the flat `resources/stimuli` image directory.

Key behavior replicated:
- Fixation cross (250 ms), then stimulus image centered.
- Response window up to 7500 ms for keyboard `d`/`k` or joystick left/right.
- Mapping 1: left/D = normal, right/K = mirrored. Mapping 2 reverses it.
- Immediate per‑trial save using the template's `update_save` schema.
- Practice shows feedback for 1000 ms; test block suppresses feedback.
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
    show_feedback,
    _play_beep,
)
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


def run_practice(
    screen: pygame.Surface,
    block: str,
    stimuli: list[Path],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run the demo/practice block using parsed stimulus filenames.

    - Draws fixation, then a single composite stimulus image centered.
    - Displays D/K labels according to mapping; records keyboard or joystick.
    - Shows feedback for 1000 ms.

    The `stimuli` parameter is ignored but kept for API compatibility.

    :return: Possibly updated display surface
    """
    try:
        trials = load_balanced_stimuli("practice")
    except Exception as e:
        logger.error(f"Failed to load practice stimuli: {e}")
        return screen

    # Constants from imported_project
    MAX_RESP_MS = 12000
    FIX_MS = cfg.FIXATION_CROSS
    ISI_MS = 500
    FB_MS = 1000

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

        # Response loop
        t0 = pygame.time.get_ticks()
        option_selected: int | None = None  # 1 = left/D, 2 = right/K
        reaction_time = MAX_RESP_MS
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
                # redraw stimulus after toggle
                place_stimulus_with_mapping(screen, stim_path, mapping_image_path())
                pygame.display.flip()
                _flush_input()

            elapsed = pygame.time.get_ticks() - t0

            if state.option_1:
                _play_beep()
                option_selected = 1
                reaction_time = elapsed
                break

            if state.option_2:
                _play_beep()
                option_selected = 2
                reaction_time = elapsed
                break

            if elapsed >= MAX_RESP_MS:
                break

            pygame.time.delay(1)

        # Lock input immediately
        _flush_input()

        # Determine correctness vs filename-derived normal/mirrored answer.
        correct_answer = trial.correct_answer
        if option_selected is None:
            correct_flag: int | None = None
            result = "timeout"
        else:
            selected_answer = answer_for_option(option_selected)
            correct_flag = 1 if selected_answer == correct_answer else 0
            result = "correct" if correct_flag == 1 else "incorrect"

        # Log result
        logger.info(
            "TRIAL_RESULT | block=%s | stim=%s | response=%s | result=%s | reaction_time_ms=%d",
            block,
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
            block_name="practice",
            trial_type="practice",
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

        # Feedback (overlay on the stimulus)
        show_feedback(screen, result)
        pygame.display.flip()
        pygame.time.delay(FB_MS)
        _flush_input()

    return screen
