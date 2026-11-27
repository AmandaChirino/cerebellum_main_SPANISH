# ./src/ui/main_window.py
"""
Experiment flow runner.

This module orchestrates the full experimental session, including:
    - Initializing the pygame environment and display.
    - Collecting participant metadata (Participant ID, VERSION).
    - Loading instruction pages and stimulus resources.
    - Sequentially presenting instruction screens.
    - Executing the complete experiment flow, inserting task blocks at the appropriate stages.
"""


from __future__ import annotations
from pathlib import Path
import pygame
import datetime
import random

import utils.config as cfg
from ui.pygame_render import _compute_mapping_from_pid
from ui.monitor_check import check_monitor, log_system_info, show_mouse_notice
from ui.files_check import check_stimuli_files
from utils.logger import get_logger, name_log_with_pid
import utils.paths as paths
from utils.event_handler import EventHandler
from ui.pygame_render import (
    init_display,
    toggle_full_screen,
    get_participant_id,
    run_admin_flow,
    place_image,
    _compute_mode_from_pid,
    _wait_for_next_page,
)
from core.practice import run_practice
from core.test import run_test
from core.saves import create_save

logger = get_logger("./src/core/emotional_tracking")


def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


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
    :type img_path: Path

    :param event_handler: Centralized event handler
    :type event_handler: EventHandler

    :return: Possibly updated display surface
    :rtype: pygame.Surface
    """
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    _flush_input()
    return _wait_for_next_page(screen, event_handler)


def _show_end_page(
    screen: pygame.Surface,
    img_path: Path,
    event_handler: EventHandler,
    timeout_ms: int = 10_000,
) -> pygame.Surface:
    """Show the final page and end on SPACE or after the timeout."""
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    _flush_input()
    start_ms = pygame.time.get_ticks()

    while True:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
            pygame.display.flip()
            _flush_input()

        elapsed = pygame.time.get_ticks() - start_ms
        if state.next_page or elapsed >= timeout_ms:
            return screen

        pygame.time.delay(10)


def run() -> None:
    """
    Deploy the full experiment flow (no result recording in this clean version).

    Flow: participant/admin screens, instructions 1-7, practice video,
    instructions 8-10, test videos, then final page 11 (SPACE or 10-second timeout).

    :return: None
    """
    cfg.START_TIME = datetime.datetime.now().isoformat()
    try:
        pygame.init()
        pygame.font.init()
        pygame.joystick.init()

        screen = init_display()
        show_mouse_notice(screen)
        log_system_info(screen)
        check_monitor(screen)
        check_stimuli_files(screen, paths.STIMPATHS_CSV_A)

        # 1) PID
        get_participant_id(screen)
        name_log_with_pid(cfg.PID)
        cfg.MODE = _compute_mode_from_pid(cfg.PID)
        cfg.initialize_mode_settings()

        paths.INSTRUCTIONS = paths.get_instructions(cfg.MAPPING)

        # 2) VERSION
        screen = run_admin_flow(screen)

        # 3) Assign stimulus set
        cfg.stimulus_set = "A"
        stimpaths_csv = paths.STIMPATHS_CSV_A

        logger.info(f"Participant ID = {cfg.PID} | Dominant Hand = {cfg.dominant_hand} | Less Affected Hand = {cfg.less_affected_hand} | Stimulus Set = {cfg.stimulus_set}")

        event_handler = EventHandler()
        create_save()

        # Show instructions 1-7 before the practice video.
        for instruction_path in paths.INSTRUCTIONS[:7]:
            screen = _show_instruction_page(screen, instruction_path, event_handler)

        screen = run_practice(screen, "practice", [paths.PRACTICE], event_handler)

        # Show instructions 8-10 before the existing test-video loop.
        for instruction_path in paths.INSTRUCTIONS[7:10]:
            screen = _show_instruction_page(screen, instruction_path, event_handler)

        screen = run_test(screen, "test", stimpaths_csv, event_handler)

        # The final page ends on SPACE or automatically after 10 seconds.
        screen = _show_end_page(screen, paths.INSTRUCTIONS[10], event_handler)
    finally:
        if cfg.START_TIME is not None:
            try:
                start_dt = datetime.datetime.fromisoformat(cfg.START_TIME)
                elapsed_s = (datetime.datetime.now() - start_dt).total_seconds()
                cfg.END_TIME = datetime.datetime.now().isoformat()
                logger.info(
                    "Total task duration: %.2f minutes (%d seconds)",
                    elapsed_s / 60,
                    int(elapsed_s),
                )
            except ValueError:
                pass
        pygame.quit()
