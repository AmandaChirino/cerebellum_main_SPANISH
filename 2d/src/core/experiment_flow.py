"""Target experiment flow: instruction pages + practice + 4 experimental blocks."""

from __future__ import annotations

import datetime
import time
from pathlib import Path

import pygame

import utils.config as cfg
from core.practice import run_practice
from core.test import run_experimental_block
from ui.pygame_render import (
    get_participant_id,
    init_display,
    place_image,
    toggle_full_screen,
)
from utils.event_handler import EventHandler
from utils.logger import get_logger
from utils.paths import (
    EXPERIMENTAL_BLOCK_1_TRIGGER_PAGE,
    EXPERIMENTAL_BLOCK_2_TRIGGER_PAGE,
    EXPERIMENTAL_BLOCK_3_TRIGGER_PAGE,
    FINAL_PAGE,
    INTER_BLOCK_1_BREAK_START_PAGE,
    INTER_BLOCK_2_BREAK_START_PAGE,
    PRACTICE_BLOCK_TRIGGER_PAGE,
    TOTAL_INSTRUCTION_PAGES,
    load_instruction_pages,
    load_stimuli_root,
)
from utils.saves import create_save, finalize_save, format_time


logger = get_logger("./src/core/experiment_flow")


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _wait_next_page(screen: pygame.Surface, event_handler: EventHandler, img_path: Path) -> pygame.Surface:
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
            place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
            pygame.display.flip()
            _flush_input()

        if state.next_page and (pygame.time.get_ticks() - start_ms) >= cfg.MIN_READING_TIME:
            return screen

        pygame.time.delay(10)


def _wait_end_page(screen: pygame.Surface, event_handler: EventHandler, img_path: Path) -> pygame.Surface:
    while True:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
            pygame.display.flip()
            _flush_input()

        if state.next_page:
            return screen

        pygame.time.delay(10)


def run() -> None:
    """Run the full target experiment flow."""
    pygame.init()
    pygame.font.init()
    cfg.START_TIME = datetime.datetime.now().isoformat()
    cfg._start_time = cfg.START_TIME
    pygame.joystick.quit()
    time.sleep(0.3)
    pygame.joystick.init()
    pygame.event.clear()
    _joy_deadline = pygame.time.get_ticks() + 2000
    _joy_count = 0
    while pygame.time.get_ticks() < _joy_deadline:
        for _ev in pygame.event.get():
            if _ev.type == pygame.JOYDEVICEADDED:
                _joy_count += 1
        if _joy_count > 0:
            break
        pygame.time.delay(20)
    logger.info(f"Joystick subsystem ready, JOYDEVICEADDED events: {_joy_count}")

    break1_start_time: float | None = None
    break2_start_time: float | None = None

    try:
        screen = init_display()
        screen = get_participant_id(screen)

        event_handler = EventHandler()
        pages = load_instruction_pages()
        stimuli_root = load_stimuli_root()

        create_save()

        for page_num in range(1, TOTAL_INSTRUCTION_PAGES + 1):
            img_path = pages[page_num]
            place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
            pygame.display.flip()
            _flush_input()

            if page_num == FINAL_PAGE:
                screen = _wait_end_page(screen, event_handler, img_path)
                break

            screen = _wait_next_page(screen, event_handler, img_path)

            if page_num == PRACTICE_BLOCK_TRIGGER_PAGE:
                # Pre-block ISI: show blank screen before first fixation
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.delay(cfg.ISI_TIME)
                screen, _ = run_practice(screen, event_handler, stimuli_root)

            elif page_num == EXPERIMENTAL_BLOCK_1_TRIGGER_PAGE:
                # Pre-block ISI: show blank screen before first fixation
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.delay(cfg.ISI_TIME)
                screen, _ = run_experimental_block(
                    screen=screen,
                    event_handler=event_handler,
                    phase_label="experimental_block_1",
                    block_name="experimental_block_1",
                    stimuli_root=stimuli_root,
                    show_trial_feedback=False,
                    break_duration_ms=0,
                )

            elif page_num == INTER_BLOCK_1_BREAK_START_PAGE:
                break1_start_time = time.time()

            elif page_num == EXPERIMENTAL_BLOCK_2_TRIGGER_PAGE:
                # Pre-block ISI: show blank screen before first fixation
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.delay(cfg.ISI_TIME)
                break_duration = 0
                if break1_start_time is not None:
                    break_duration = int((time.time() - break1_start_time) * 1000)
                    logger.info("Inter-block break 1 duration: %d ms", break_duration)

                screen, _ = run_experimental_block(
                    screen=screen,
                    event_handler=event_handler,
                    phase_label="experimental_block_2",
                    block_name="experimental_block_2",
                    stimuli_root=stimuli_root,
                    show_trial_feedback=False,
                    break_duration_ms=break_duration,
                )

            elif page_num == INTER_BLOCK_2_BREAK_START_PAGE:
                break2_start_time = time.time()

            elif page_num == EXPERIMENTAL_BLOCK_3_TRIGGER_PAGE:
                # Pre-block ISI: show blank screen before first fixation
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.delay(cfg.ISI_TIME)
                break_duration = 0
                if break2_start_time is not None:
                    break_duration = int((time.time() - break2_start_time) * 1000)
                    logger.info("Inter-block break 2 duration: %d ms", break_duration)

                screen, _ = run_experimental_block(
                    screen=screen,
                    event_handler=event_handler,
                    phase_label="experimental_block_3",
                    block_name="experimental_block_3",
                    stimuli_root=stimuli_root,
                    show_trial_feedback=False,
                    break_duration_ms=break_duration,
                )

        logger.info("Task completed successfully")

    finally:
        finalize_save(format_time())
        if cfg.START_TIME is not None:
            try:
                start_dt = datetime.datetime.fromisoformat(cfg.START_TIME)
                elapsed_s = (datetime.datetime.now() - start_dt).total_seconds()
                logger.info("Total task duration: %.2f minutes (%d seconds)", elapsed_s / 60, int(elapsed_s))
            except ValueError:
                pass

        pygame.quit()
