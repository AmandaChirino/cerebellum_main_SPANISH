# ./src/core/three_back.py
"""
3-back task execution with deterministic sequence generation.

Presents stimulus sequences with exact target counts, enforces fixed 3000ms timing
per trial (500ms stimulus + 2500ms ISI), and optionally displays feedback during practice.
"""


from __future__ import annotations
from pathlib import Path
import pygame

import utils.config as cfg
from utils.paths import STIM_BG
from utils.logger import get_logger
from utils.event_handler import EventHandler
from core.pull_stimuli import pull_stimuli_3back
from ui.pygame_render import (
    toggle_full_screen,
    place_image,
    show_feedback,
    show_feedback_timed,
    draw_fixation_cross,
    _play_beep
)
from utils.saves import update_save


logger = get_logger("./src/core/three_back")


def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def run_3back(
    screen: pygame.Surface,
    phase: str,
    condition: str,
    _is_practice: bool,
    event_handler: EventHandler,
    trial_num: int,
) -> pygame.Surface:
    """
    Execute 3-back block with fixed 3000ms timing per trial.

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param phase: Name of the phase
    :type phase: str

    :param condition: Name of the condition
    :type condition: str

    :param _is_practice: True = Practice / False = Test
    :type _is_practice: bool

    :param event_handler: Centralized event handler instance
    :type event_handler: EventHandler

    :param trial_num: Number of trials in this block
    :type trial_num: int

    :return: Active display surface after the block
    :rtype: pygame.Surface
    """
    _stim_seq, _match_map = pull_stimuli_3back(trial_num)

    for i in range(len(_stim_seq)):
        stim_path = _stim_seq[i]
        stim_id = str(stim_path.stem)
        match = _match_map[i] if i > 2 else None

        place_image(screen, STIM_BG)
        place_image(screen, stim_path, None, (cfg.STIM_W, cfg.STIM_H))
        pygame.display.flip()
        _flush_input()

        trial_start = pygame.time.get_ticks()
        total_window = cfg.STIM_DISPLAY_TIME + cfg.ISI
        phase_state = "stim"

        reaction_time = None
        option_selected: int | None = None
        feedback_shown = False
        feedback_start_time = None
        feedback_type = None

        # Phase 1: Stimulus display period
        while (pygame.time.get_ticks() - trial_start) < cfg.STIM_DISPLAY_TIME:
            state = event_handler.poll()

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                place_image(screen, STIM_BG)
                place_image(screen, stim_path, None, (cfg.STIM_W, cfg.STIM_H))
                pygame.display.flip()
                _flush_input()

            # Record first spacebar press only
            if option_selected is None and state.option_1:
                option_selected = 1
                reaction_time = pygame.time.get_ticks() - trial_start
                
                # Mark feedback to show as overlay
                if _is_practice:
                    feedback_start_time = pygame.time.get_ticks()
                    # Determine result immediately for feedback
                    if i < 3:
                        feedback_type = "incorrect"
                    elif match:
                        feedback_type = "correct"
                    else:
                        feedback_type = "incorrect"

            # Draw feedback overlay if within 1000ms of response
            if feedback_start_time is not None:
                elapsed_since_feedback = pygame.time.get_ticks() - feedback_start_time
                if elapsed_since_feedback < cfg.FB_DURATION:
                    show_feedback(screen, feedback_type)
                    pygame.display.flip()

            pygame.time.delay(1)

        # Phase 2: ISI period with feedback
        screen.fill(cfg.BLACK_RGB)
        draw_fixation_cross(screen)
        # Inmediatamente dibujar feedback si está activo
        if feedback_start_time is not None:
            elapsed_since_feedback = pygame.time.get_ticks() - feedback_start_time
            if elapsed_since_feedback < cfg.FB_DURATION:
                show_feedback(screen, feedback_type)
        pygame.display.flip()
        isi_background = screen.copy()

        # Determine result based on match and response
        if i < 3:
            # First three trials: any response is incorrect
            result = "incorrect" if option_selected is not None else "correct"
        elif match:
            # Target trial: response needed
            result = "correct" if option_selected is not None else "incorrect"
        else:
            # Non-target trial: no response needed
            result = "incorrect" if option_selected is not None else "correct"

        # Continue ISI period with response monitoring
        while (pygame.time.get_ticks() - trial_start) < total_window:
            state = event_handler.poll()

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                _flush_input()
                isi_background = screen.copy()

            # Record first spacebar press during ISI
            if option_selected is None and state.option_1:
                option_selected = 1
                reaction_time = pygame.time.get_ticks() - trial_start
                
                # Re-determine result with new response
                if i < 3:
                    result = "incorrect"
                elif match:
                    result = "correct"
                else:
                    result = "incorrect"
                
                # Mark feedback to show as overlay
                if _is_practice:
                    feedback_start_time = pygame.time.get_ticks()
                    feedback_type = result

            # Show delayed feedback for no-response trials
            if _is_practice and not feedback_shown and option_selected is None:
                elapsed = pygame.time.get_ticks() - trial_start
                
                # Miss: show feedback 1000ms before end
                if match and elapsed >= (total_window - cfg.FB_DURATION):
                    if feedback_start_time is None:
                        feedback_start_time = pygame.time.get_ticks()
                        feedback_type = "incorrect"
                        feedback_shown = True
                
                # Correct rejection: show feedback at remaining time
                elif not match and i > 2 and elapsed >= (total_window - cfg.FB_DURATION):
                    if feedback_start_time is None:
                        feedback_start_time = pygame.time.get_ticks()
                        feedback_type = "correct"
                        feedback_shown = True

            # Draw feedback overlay if within 500ms of response
            # Always redraw ISI background first, then overlay feedback if active
            screen.fill(cfg.BLACK_RGB)
            draw_fixation_cross(screen)
            if feedback_start_time is not None:
                elapsed_since_feedback = pygame.time.get_ticks() - feedback_start_time
                if elapsed_since_feedback < cfg.FB_DURATION:
                    show_feedback(screen, feedback_type)
            pygame.display.flip()

            pygame.time.delay(1)

        _flush_input()

        # Determine response classification and signal detection
        if i < 3:
            # First 3 trials cannot be evaluated
            key_response = "space" if option_selected is not None else "none"
            key_correct = ""
            signal_detection = "null"
        else:
            # Trials 4+ can be evaluated
            key_response = "space" if option_selected is not None else "none"
            
            if match:
                # Target trial
                key_correct = "space"
                if option_selected is not None:
                    signal_detection = "hit"
                else:
                    signal_detection = "miss"
            else:
                # Non-target trial
                key_correct = "none"
                if option_selected is not None:
                    signal_detection = "false_alarm"
                else:
                    signal_detection = "correct_rejection"

        logger.info(
            "TRIAL_RESULT | stim=%s | response=%s | result=%s | signal_detection=%s | reaction_time=%s",
            stim_path.name,
            key_response,
            result,
            signal_detection,
            reaction_time if reaction_time is not None else "None",
        )

        # Save trial data
        update_save(condition, "3back", key_response, key_correct, result, signal_detection, reaction_time, stim_id)
        _flush_input()

    return screen
