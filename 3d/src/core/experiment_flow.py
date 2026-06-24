# ./src/ui/main_window.py
"""
Experiment flow runner.

This module orchestrates the full experimental session, including:
    - Initializing the pygame environment and display.
    - Collecting participant metadata (Participant ID, MAPPING).
    - Loading instruction pages and stimulus resources.
    - Sequentially presenting instruction screens.
    - Executing the complete experiment flow, inserting task blocks at the appropriate stages.
"""


from __future__ import annotations
from pathlib import Path
import pygame
import datetime
import random
import time

import utils.config as cfg
from utils.logger import get_logger
from utils.paths import load_instructions, STIMULI
from utils.event_handler import EventHandler
from ui.pygame_render import (
    init_display,
    toggle_full_screen,
    get_participant_id,
    run_admin_flow,
    place_image,
)
from core.practice import run_practice
from core.test import run_test
from utils.saves import create_save

logger = get_logger("./src/core/experiment_flow")


def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _wait_for_next_page(
    screen: pygame.Surface,
    event_handler: EventHandler,
    img_path: Path | None = None,
) -> pygame.Surface:
    """
    Wait until SPACE is pressed (next_page), with min reading time constraint.
    Also handles quit / fullscreen toggle.

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param event_handler: Centralized event handler
    :type event_handler: EventHandler

    :img_path: Image path of the current instruction page
    :type img_path: pathlib.Path

    :return: Possibly updated display surface
    :rtype: pygame.Surface
    """
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
                place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
                pygame.display.flip()
                _flush_input()

        elapsed = pygame.time.get_ticks() - start_ms
        if state.next_page and elapsed >= cfg.MIN_READING_TIME:
            return screen

        pygame.time.delay(10)


def _wait_for_end_page(
    screen: pygame.Surface,
    event_handler: EventHandler,
    img_path: Path | None = None,
    max_duration_ms: int = 10_000,
) -> pygame.Surface:
    """
    End screen behavior:
    - Press SPACE to exit immediately, OR
    - Auto-exit after max_duration_ms.

    Also handles quit / fullscreen toggle.

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param event_handler: Centralized event handler
    :type event_handler: EventHandler

    :param img_path: Image path of the end page (redraw after fullscreen toggle)
    :type img_path: pathlib.Path | None

    :param max_duration_ms: Auto-exit timeout in milliseconds
    :type max_duration_ms: int

    :return: Possibly updated display surface
    :rtype: pygame.Surface
    """
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
                place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
                pygame.display.flip()
                _flush_input()

        elapsed = pygame.time.get_ticks() - start_ms
        if state.next_page:
            return screen

        if elapsed >= max_duration_ms:
            return screen

        pygame.time.delay(10)


def _show_instruction_page(
    screen: pygame.Surface,
    img_path: Path,
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Show a single instruction page and advance on SPACE.

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param img_path: Instruction image path
    :type img_path: pathlib.Path

    :param event_handler: Centralized event handler
    :type event_handler: EventHandler

    :return: Possibly updated display surface
    :rtype: pygame.Surface
    """
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    _flush_input()
    return _wait_for_next_page(screen, event_handler, img_path=img_path)


def _show_end_page(
    screen: pygame.Surface,
    img_path: Path,
    event_handler: EventHandler,
    max_duration_ms: int = 10_000,
) -> pygame.Surface:
    """
    Show the final end screen and exit on SPACE or timeout.

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param img_path: End screen image path
    :type img_path: pathlib.Path

    :param event_handler: Centralized event handler
    :type event_handler: EventHandler

    :param max_duration_ms: Auto-exit timeout in milliseconds
    :type max_duration_ms: int

    :return: Possibly updated display surface
    :rtype: pygame.Surface
    """
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    _flush_input()
    return _wait_for_end_page(
        screen,
        event_handler,
        img_path=img_path,
        max_duration_ms=max_duration_ms,
    )


def run() -> None:
    """
    Deploy the full experiment flow (no result recording in this clean mapping template).

    Steps:
    1) get_participant_id
    2) select_mapping
    3) instructions 1-12 (SPACE to advance)
    4) practice block (with feedback)
    5) instructions 13-16
    6) test 1
    7) instructions 17-21
    8) test 2
    9) instruction 22 end page

    :return: None
    """
    pygame.init()
    pygame.font.init()
    cfg.START_TIME = datetime.datetime.now().isoformat()
    cfg._start_time = cfg.START_TIME

    # macOS + SDL2 joystick lifecycle fix: force HID re-enumeration
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

    try:
        screen = init_display()

        # 1) PID + MAPPING + test order (computed from PID suffix mod 4)
        screen = get_participant_id(screen)

        # 2) Admin flow: Group / Session / Dominant Hand / Hand Used
        screen = run_admin_flow(screen)
        logger.info(
            f"Participant ID = {cfg.PID} | Counterbalance = {cfg.COUNTERBALANCE_REMAINDER} | Mapping = {cfg.MAPPING} | Group = {cfg.GROUP} | Session = {cfg.SESSION} | Dominant Hand = {cfg.DH} | Hand Used = {cfg.UH}"
        )

        # Load assets
        event_handler = EventHandler()
        INSTRUCTIONS = load_instructions()

        # Create save
        create_save()

        
        # 3) instructions 1-12
        for i in range(12):
            screen = _show_instruction_page(screen, INSTRUCTIONS[i], event_handler)

        # 4) practice block (with feedback)
        screen = run_practice(screen, "practice", STIMULI, event_handler)

        # 5) instructions 13-16
        for i in range(12, 16):
            screen = _show_instruction_page(screen, INSTRUCTIONS[i], event_handler)

        # 6) test 1 (no feedback)
        screen = run_test(screen, "test1", STIMULI, event_handler)

        # 7) instructions 17-21
        for i in range(16, 21):
            screen = _show_instruction_page(screen, INSTRUCTIONS[i], event_handler)

        # 8) test 2 (no feedback)
        screen = run_test(screen, "test2", STIMULI, event_handler)

        # 9) instruction 22
        screen = _show_end_page(screen, INSTRUCTIONS[21], event_handler)

        logger.info("Task completed successfully!")
    finally:
        if cfg.START_TIME is not None:
            try:
                start_dt = datetime.datetime.fromisoformat(cfg.START_TIME)
                elapsed_s = (datetime.datetime.now() - start_dt).total_seconds()
                logger.info(f"Total task duration: {elapsed_s / 60:.2f} minutes ({int(elapsed_s)} seconds)")
            except ValueError:
                pass

        pygame.quit()
