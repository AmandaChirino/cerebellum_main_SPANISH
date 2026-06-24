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
import time
import random

import utils.config as cfg
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
    block_results,
)
from core.practice import run_practice
from core.experimental import run_block
from core.saves import create_save, create_joystick_log
from utils.prep_stimuli import build_trials

logger = get_logger("./src/core/main_window")


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


def run() -> None:
    """
    Full experiment flow for the soccer prediction task.

    Steps:
        1) Collect participant ID, mapping, and mode.
        2) Run admin flow (dominant hand, used hand).
        3) Build the full trial sequence for this participant.
        4) Instructions → practice block (with feedback).
        5) Instructions → block 1 → block 2 → block 3 → block 4 (no feedback).
        6) End screen.
    """
    pygame.init()
    pygame.font.init()
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
    cfg.START_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    screen = init_display()

    # 1) PID, MODE
    get_participant_id(screen)
    cfg.MODE = _compute_mode_from_pid(cfg.PID)
    cfg.initialize_mode_settings()

    paths.INSTRUCTIONS = paths.get_instructions(cfg.MAPPING)

    # 2) Admin flow (hands)
    screen = run_admin_flow(screen)

    logger.info(
        "Participant ID = %s | Dominant Hand = %s | Hand Used = %s | "
        "Version = %s | Mode = %s",
        cfg.PID, cfg.DH, cfg.UH, cfg.MAPPING, cfg.MODE,
    )

    event_handler = EventHandler()
    create_save()
    create_joystick_log()

    # 3) Build full trial sequence
    all_trials = build_trials()
    prac_trials = [t for t in all_trials if t['phase'] == 'practice']
    block_trials = {b: [t for t in all_trials if t['block'] == b] for b in range(1, 5)}

    # INSTRUCTIONS → PRACTICE   
    for i in range(cfg.PRACTICE1_PG):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)
    # PRACTICE BLOCK
    screen, _, _ = run_practice(screen, "p1", prac_trials, event_handler)

    # INSTRUCTIONS → BLOCK 1
    for i in range(cfg.PRACTICE1_PG, cfg.BLOCK1_PG):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)
    screen, _, _ = run_block(screen, "b1", block_trials[1], event_handler)

    # INSTRUCTIONS → BLOCK 2
    for i in range(cfg.BLOCK1_PG, cfg.BLOCK2_PG):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)
    screen, _, _ = run_block(screen, "b2", block_trials[2], event_handler)

    # INSTRUCTIONS → BLOCK 3
    for i in range(cfg.BLOCK2_PG, cfg.BLOCK3_PG):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)
    screen, _, _ = run_block(screen, "b3", block_trials[3], event_handler)

    # INSTRUCTIONS → BLOCK 4
    for i in range(cfg.BLOCK3_PG, cfg.BLOCK4_PG):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS[i], event_handler)
    screen, _, _ = run_block(screen, "b4", block_trials[4], event_handler)

    # END SCREEN
    place_image(screen, paths.INSTRUCTIONS[cfg.LAST_PG - 1], fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    _flush_input()
    screen = _wait_for_next_page_or_timeout(screen, event_handler, timeout_ms=10000)

    cfg.END_TIME = datetime.datetime.now()
    total = cfg.END_TIME - datetime.datetime.fromisoformat(cfg.START_TIME)
    logger.info("Task completed. Duration: %.2f min (%d s)", total.total_seconds() / 60, int(total.total_seconds()))

    pygame.quit()
