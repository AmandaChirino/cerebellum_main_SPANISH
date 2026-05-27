"""
Main experiment flow for current CCC task.
"""


from __future__ import annotations
from pathlib import Path
import datetime
import time

import pygame

import utils.config as cfg
from utils.logger import get_logger
from utils.paths import load_instructions
from utils.event_handler import EventHandler, reset_joystick_cache
from utils.saves import create_save, finalize_save
from ui.pygame_render import (
    init_display,
    toggle_full_screen,
    get_participant_id,
    admin,
    place_image,
)
from core.construct_trials import (
    construct_single_task_trial_series,
    construct_multi_task_trial_series,
)
from core.single_tasks import run_single_task_phase
from core.multi_tasks import run_multi_task_phase


logger = get_logger("./src/core/experiment_flow")


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _wait_for_next_page(
    screen: pygame.Surface,
    event_handler: EventHandler,
    img_path: Path | None = None,
    fit_mode: str = "cover",
    max_fraction: float = 1.0,
) -> pygame.Surface:
    start_ms = pygame.time.get_ticks()

    while True:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            if img_path is not None:
                place_image(screen, img_path, fit_mode=fit_mode, max_fraction=max_fraction)
                pygame.display.flip()
                _flush_input()

        elapsed = pygame.time.get_ticks() - start_ms
        if state.next_page and elapsed >= cfg.MIN_READING_TIME:
            return screen

        pygame.time.delay(10)


def _show_instruction_page(
    screen: pygame.Surface,
    img_path: Path,
    event_handler: EventHandler,
) -> pygame.Surface:
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    _flush_input()
    return _wait_for_next_page(screen, event_handler, img_path, fit_mode="contain", max_fraction=0.9)


def _play_isi(screen: pygame.Surface, event_handler: EventHandler) -> pygame.Surface:
    """
    Play a pre-block ISI: fill BLACK and wait cfg.ISI_TIME ms.
    Honors quit and fullscreen toggle.
    """
    start_ms = pygame.time.get_ticks()
    while True:
        # Draw black screen
        screen.fill(cfg.BLACK_RGB)
        pygame.display.flip()

        state = event_handler.poll()
        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            # continue loop to redraw black on new surface

        if pygame.time.get_ticks() - start_ms >= cfg.ISI_TIME:
            return screen

        pygame.time.delay(10)


def run() -> None:
    pygame.init()
    pygame.font.init()
    cfg.START_TIME = datetime.datetime.now().isoformat()
    cfg.GLOBAL_END_TIME = None
    cfg._start_time = cfg.START_TIME

    # Force a full joystick subsystem cycle on macOS.
    # After the previous process calls pygame.quit(), macOS needs time to finish
    # releasing the IOHIDManager HID handle.  If the next process re-opens the
    # device too quickly, SDL's IOHIDManager callbacks do not fully re-register
    # and get_axis() returns 0 while JOYAXISMOTION events are never generated.
    #
    # Fix: quit the joystick subsystem, sleep 300 ms, then re-init fresh.
    # Then wait up to 2 s for SDL's JOYDEVICEADDED confirmation.
    pygame.joystick.quit()
    time.sleep(0.3)
    pygame.joystick.init()
    reset_joystick_cache()
    _joy_count = 0
    _joy_deadline = pygame.time.get_ticks() + 2000
    while pygame.time.get_ticks() < _joy_deadline:
        for _ev in pygame.event.get():
            if _ev.type == pygame.JOYDEVICEADDED:
                _joy_count += 1
        if _joy_count > 0:
            break
        pygame.time.delay(20)
    if _joy_count == 0:
        _joy_count = pygame.joystick.get_count()
    logger.info(f"Joystick count at startup: {_joy_count}")

    try:
        screen = init_display()
        screen = get_participant_id(screen)
        screen = admin(screen)

        logger.info(
            "Participant ID=%s | Mapping=%s | Group=%s | Session=%s | DH=%s | UH=%s",
            cfg.PID,
            cfg.MAPPING,
            str(cfg.GROUP),
            str(cfg.SESSION),
            cfg.DH,
            cfg.UH,
        )

        create_save()

        single_task_series = construct_single_task_trial_series()
        multi_task_series = construct_multi_task_trial_series()
        # In the multi-task phases:
        # - block_1 = List 1
        # - block_2 = List 2
        # Mappings 5-8 present List 2 first, then List 1.
        if cfg.mapping_uses_list2_first(cfg.MAPPING):
            multi_task_series["multi_task_experimental_block_1"], \
            multi_task_series["multi_task_experimental_block_2"] = \
                multi_task_series["multi_task_experimental_block_2"], \
                multi_task_series["multi_task_experimental_block_1"]
        all_task_series: dict[str, list] = {**single_task_series, **multi_task_series}

        event_handler = EventHandler()
        instruction_pages = load_instructions()
        task_order = cfg.INSTRUCTION_TASK_ORDER
        checkpoints = cfg.INSTRUCTION_TASK_AFTER_PNG_BY_MAPPING[cfg.MAPPING]

        for img_path in instruction_pages:
            screen = _show_instruction_page(screen, img_path, event_handler)

            if not img_path.stem.isdigit():
                continue
            page_no = int(img_path.stem)
            if page_no not in checkpoints:
                continue

            task_idx = checkpoints.index(page_no)
            task_phase = task_order[task_idx]
            trial_series = all_task_series[task_phase]

            logger.info(
                "TASK_START | phase=%s | after_instruction_page=%d | trials=%d",
                task_phase,
                page_no,
                len(trial_series),
            )

            # Pre-block ISI before the very first fixation cross
            screen = _play_isi(screen, event_handler)

            if task_phase.startswith("multi_task"):
                screen = run_multi_task_phase(screen, task_phase, trial_series, event_handler)
            else:
                screen = run_single_task_phase(screen, task_phase, trial_series, event_handler)

        logger.info("Task completed successfully")
    finally:
        cfg.GLOBAL_END_TIME = datetime.datetime.now().isoformat()
        finalize_save()

        if cfg.START_TIME is not None:
            try:
                start_dt = datetime.datetime.fromisoformat(cfg.START_TIME)
                elapsed_s = (datetime.datetime.now() - start_dt).total_seconds()
                logger.info(
                    "Total task duration: %.2f minutes (%d seconds)",
                    elapsed_s / 60,
                    int(elapsed_s),
                )
            except ValueError:
                pass

        pygame.quit()
