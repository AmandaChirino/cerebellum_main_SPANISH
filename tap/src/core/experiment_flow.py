from __future__ import annotations
from pathlib import Path
import datetime

import pygame

from core.run_trial import *

import utils.config as cfg
from ui.pygame_render import _compute_mapping_from_pid
from utils.logger import get_logger
import utils.paths as paths
from utils.event_handler import EventHandler
from ui.pygame_render import (
    init_display,
    toggle_full_screen,
    get_participant_id,
    run_admin_flow,
    place_image,
    _compute_mode_from_pid,
)
from core.saves import create_save

# Global variables for screen
screen = None
SCREEN_WIDTH = None 
SCREEN_HEIGHT = None


global_start = pygame.time.get_ticks()
results = []


logger = get_logger("./src/core/tapping")


def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _wait_for_next_page(screen: pygame.Surface, event_handler: EventHandler) -> pygame.Surface:
    """
    Wait until SPACE is pressed (next_page), with min reading time constraint.
    Also handles quit / fullscreen toggle.

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param event_handler: Centralized event handler
    :type event_handler: EventHandler

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

        elapsed = pygame.time.get_ticks() - start_ms
        if state.next_page and elapsed >= cfg.MIN_READING_TIME:
            return screen

        pygame.time.delay(10)

def _wait_for_next_page_or_timeout(
    screen: pygame.Surface, 
    event_handler: EventHandler,
    timeout_ms: int = 10000
) -> pygame.Surface:
    """
    Wait until SPACE is pressed (next_page) OR timeout expires.
    Also handles quit / fullscreen toggle.

    :param screen: Current display surface
    :param event_handler: Centralized event handler
    :param timeout_ms: Timeout in milliseconds (default 10000 = 10 seconds)
    :return: Possibly updated display surface
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

        elapsed = pygame.time.get_ticks() - start_ms
        
        # Exit if timeout reached
        if elapsed >= timeout_ms:
            logger.info(f"Timeout, end task")
            return screen
        
        # Exit if next_page pressed (and min reading time met)
        if state.next_page and elapsed >= cfg.MIN_READING_TIME:
            logger.info(f"Timeout, end task")
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


def _show_transition_page(
    screen: pygame.Surface,
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Show the inter-trial transition page (11.png) and advance on SPACE.

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param event_handler: Centralized event handler
    :type event_handler: EventHandler

    :return: Possibly updated display surface
    :rtype: pygame.Surface
    """
    return _show_instruction_page(screen, paths.INSTRUCTIONS[10], event_handler)


def _get_final_page_path() -> Path:
    """
    Return the final task page path.

    Uses the final instruction page `10.png`.
    """
    return paths.INSTRUCTIONS[cfg.BLOCK_2]


def _show_final_page(
    screen: pygame.Surface,
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Show the closing page and wait for SPACE or timeout.
    """
    final_page = _get_final_page_path()
    place_image(screen, final_page, fit_mode="contain", max_fraction=0.9)
    logger.info("Display final page: %s", final_page.name)
    pygame.display.flip()
    _flush_input()
    return _wait_for_next_page_or_timeout(screen, event_handler, timeout_ms=10000)


def run() -> None:
    """
    Deploy the full experiment flow (no result recording in this clean version).

    Steps:
    1) get_participant_id
    2) select_version
    3) instructions 1-3 (SPACE to advance)
    4) instruction practice
    5) practice block (randomized 5 stimuli, with feedback)
    6) instruction 4
    7) instruction test
    8) test block (randomized 5 stimuli, no feedback)
    9) instruction 5
    10) end task

    :return: None
    """
    pygame.init()
    pygame.font.init()
    pygame.joystick.init()
    cfg.START_TIME = datetime.datetime.now().isoformat()

    screen = init_display()

    # 1) PID
    get_participant_id(screen)
    cfg.MAPPING = _compute_mapping_from_pid(cfg.PID)
    cfg.MODE = _compute_mode_from_pid(cfg.PID)
    cfg.initialize_mode_settings()
    

    paths.INSTRUCTIONS = paths.get_instructions(cfg.MAPPING)

    # 2) VERSION
    screen = run_admin_flow(screen)

    logger.info(f"Participant ID = {cfg.PID} | Dominant Hand = {cfg.dominant_hand} | Less Affected Hand = {cfg.less_affected_hand}")

    # Load assets
    event_handler = EventHandler()

    # Create save
    create_save()
    
    # 3) instructions for practice
    for i in range(cfg.PRACTICE_1):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)

    # 4) practice trial 1
    screen, result = single_trial(screen, "p1", global_start, "practice", pygame.K_SPACE, 1, event_handler)

    # 6) instructions
    for i in range(cfg.PRACTICE_1, cfg.PRACTICE_2):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)
    
    # 8) practice trial 2
    screen, result = single_trial(screen, "p2", global_start, "practice", pygame.K_SPACE, 1, event_handler)

    # 7) instruction for test
    for i in range(cfg.PRACTICE_2, cfg.BLOCK_1):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)

    # 9) test block 1
    trial_num, u, s = 0, 0, 0
    b1_trial_idx = 0
    while u < 3 and s < 6:
        if b1_trial_idx > 0:
            screen = _show_transition_page(screen, event_handler)
        trial_num += 1
        b1_trial_idx += 1
        screen, result = single_trial(screen, "b1", global_start, "experimental", pygame.K_SPACE, trial_num, event_handler)
        if result:
            s += 1
        else:
            u += 1

    # Instructions between blocks
    for i in range(cfg.BLOCK_1, cfg.BLOCK_2):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)

    # test block 2
    u, s = 0, 0
    b2_trial_idx = 0
    while u < 3 and s < 6:
        if b2_trial_idx > 0:
            screen = _show_transition_page(screen, event_handler)
        trial_num += 1
        b2_trial_idx += 1
        screen, result = single_trial(screen, "b2", global_start, "experimental", pygame.K_SPACE, trial_num, event_handler)
        if result:
            s += 1
        else:
            u += 1

    # END
    screen = _show_final_page(screen, event_handler)

    # Calculate and display total task duration
    cfg.END_TIME = datetime.datetime.now()
    start_time_obj = datetime.datetime.fromisoformat(cfg.START_TIME)
    total_duration = cfg.END_TIME - start_time_obj
    total_minutes = total_duration.total_seconds() / 60

    logger.info("Task completed. Duration: %.2f min (%d s)", total_minutes, int(total_duration.total_seconds()))

    pygame.quit()
