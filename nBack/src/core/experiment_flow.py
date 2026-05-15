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

import utils.config as cfg
from utils.logger import get_logger
import utils.paths as paths
from utils.event_handler import EventHandler
from ui.pygame_render import (
    init_display,
    toggle_full_screen,
    get_participant_id,

    place_image,
)
from core.one_back import run_1back
from core.two_back import run_2back
from core.three_back import run_3back
from utils.saves import create_save, finalize_experiment

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



def _pre_block_isi(screen: pygame.Surface, event_handler: EventHandler) -> pygame.Surface:
    """Show a pre-block ISI: fill screen with BLACK and wait cfg.ISI ms.

    Handles quit and fullscreen toggle during the wait. Returns (possibly) updated screen.
    """
    # Paint black once
    screen.fill(cfg.BLACK_RGB)
    pygame.display.flip()

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
            screen.fill(cfg.BLACK_RGB)
            pygame.display.flip()
        if (pygame.time.get_ticks() - start_ms) >= cfg.ISI_BEFORE_FIRST_TRIAL:
            return screen
        pygame.time.delay(5)

def run() -> None:
    """
    Deploy the full experiment flow (no result recording in this clean version).

    Steps:
    1) run_1back

    :return: None
    """
    pygame.init()
    pygame.font.init()
    cfg.START_TIME = datetime.datetime.now().isoformat()

    screen = init_display()

    # 1) PID
    screen = get_participant_id(screen)

    # 2) MAPPING
    logger.info(f"Participant ID = {cfg.PID} | Dominant Hand = {cfg.dominant_hand} | Used Hand = {cfg.hand_used}")

    # Load assets
    event_handler = EventHandler()

    # Create save
    create_save()

    # 3) run_1back
    # Practice 1a (first 10 trials)
    cfg.practice_block_count += 1
    cfg.current_block_label = f"p{cfg.practice_block_count}"
    # Show initial 1-back instructions (legacy 1-7 without removed 4)
    for i in range(1, 7):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
    screen = _pre_block_isi(screen, event_handler)
    screen = run_1back(screen, "1back_practice1a", "practice", True, event_handler, 10)
    # Pause break
    screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / "7.png", event_handler)
    # Practice 1b (second 10 trials)
    cfg.practice_block_count += 1
    cfg.current_block_label = f"p{cfg.practice_block_count}"
    screen = _pre_block_isi(screen, event_handler)
    screen = run_1back(screen, "1back_practice1b", "practice", True, event_handler, 10)
    # Block 1
    cfg.test_block_count += 1
    cfg.current_block_label = f"b{cfg.test_block_count}"
    # Show instructions before Block 1
    for i in range(8, 11):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
    screen = _pre_block_isi(screen, event_handler)
    screen = run_1back(screen, "1back_block1", "test", False, event_handler, cfg.BLOCK1_COUNT)
    
    if cfg.MODE == "full":
        # Block 2
        cfg.test_block_count += 1
        cfg.current_block_label = f"b{cfg.test_block_count}"
        for i in range(11, 14):
            screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
        screen = _pre_block_isi(screen, event_handler)
        screen = run_1back(screen, "1back_block2", "test", False, event_handler, cfg.BLOCK2_COUNT)
        # Block 3
        cfg.test_block_count += 1
        cfg.current_block_label = f"b{cfg.test_block_count}"
        for i in range(14, 16):
            screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
        screen = _pre_block_isi(screen, event_handler)
        screen = run_1back(screen, "1back_block3", "test", False, event_handler, cfg.BLOCK1_COUNT)

    # Show page 17 (now mapped to 16) before starting 2-back
    screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / "16.png", event_handler)
    
    # 4) run_2back
    # Practice 2a (first 10 trials)
    cfg.practice_block_count += 1
    cfg.current_block_label = f"p{cfg.practice_block_count}"
    # Show initial 2-back instructions (legacy 18-24 without removed 21)
    for i in range(17, 23):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
    screen = _pre_block_isi(screen, event_handler)
    screen = run_2back(screen, "2back_practice2a", "practice", True, event_handler, 10)
    # Pause break
    screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / "23.png", event_handler)
    # Practice 2b (second 10 trials)
    cfg.practice_block_count += 1
    cfg.current_block_label = f"p{cfg.practice_block_count}"
    screen = _pre_block_isi(screen, event_handler)
    screen = run_2back(screen, "2back_practice2b", "practice", True, event_handler, 10)
    # Block 4
    cfg.test_block_count += 1
    cfg.current_block_label = f"b{cfg.test_block_count}"
    # Show initial instructions before Block 4
    for i in range(24, 27):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
    screen = _pre_block_isi(screen, event_handler)
    screen = run_2back(screen, "2back_block4", "test", False, event_handler, cfg.BLOCK3_COUNT)
    
    if cfg.MODE == "full":
        # Block 5
        cfg.test_block_count += 1
        cfg.current_block_label = f"b{cfg.test_block_count}"
        # Show initial instructions before Block 5
        for i in range(27, 30):
            screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
        screen = _pre_block_isi(screen, event_handler)
        screen = run_2back(screen, "2back_block5", "test", False, event_handler, cfg.BLOCK4_COUNT)
        # Block 6
        cfg.test_block_count += 1
        cfg.current_block_label = f"b{cfg.test_block_count}"
        # Show initial instructions before Block 6
        for i in range(30, 33):
            screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
        screen = _pre_block_isi(screen, event_handler)
        screen = run_2back(screen, "2back_block6", "test", False, event_handler, cfg.BLOCK3_COUNT)

    # 5) run_3back
   # Practice 3a (first 10 trials)
    cfg.practice_block_count += 1
    cfg.current_block_label = f"p{cfg.practice_block_count}"
    # Show initial 3-back instructions (legacy 35-41 without removed 38)
    for i in range(33, 39):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
    screen = _pre_block_isi(screen, event_handler)
    screen = run_3back(screen, "3back_practice3a", "practice", True, event_handler, 10)
    # Pause break
    screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / "39.png", event_handler)
    # Practice 3b (second 10 trials)
    cfg.practice_block_count += 1
    cfg.current_block_label = f"p{cfg.practice_block_count}"
    screen = _pre_block_isi(screen, event_handler)
    screen = run_3back(screen, "3back_practice3b", "practice", True, event_handler, 10)
    # Block 7
    cfg.test_block_count += 1
    cfg.current_block_label = f"b{cfg.test_block_count}"
    # Show initial instructions before Block 7
    for i in range(40, 43):
        screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
    screen = _pre_block_isi(screen, event_handler)
    screen = run_3back(screen, "3back_block7", "test", False, event_handler, cfg.BLOCK5_COUNT)
    
    if cfg.MODE == "full":
        # Block 8
        cfg.test_block_count += 1
        cfg.current_block_label = f"b{cfg.test_block_count}"
        # Show initial instructions before Block 8
        for i in range(43, 46):
            screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
        screen = _pre_block_isi(screen, event_handler)
        screen = run_3back(screen, "3back_block8", "test", False, event_handler, cfg.BLOCK6_COUNT)
        # Block 9
        cfg.test_block_count += 1
        cfg.current_block_label = f"b{cfg.test_block_count}"
        # Show initial instructions before Block 9
        for i in range(46, 49):
            screen = _show_instruction_page(screen, paths.INSTRUCTIONS_DIR / f"{i}.png", event_handler)
        screen = _pre_block_isi(screen, event_handler)
        screen = run_3back(screen, "3back_block9", "test", False, event_handler, cfg.BLOCK5_COUNT)
        # Final screen before ending (max 6 seconds or until SPACE)
        img_path = paths.INSTRUCTIONS_DIR / "49.png"
        place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
        pygame.display.flip()
        _flush_input()
        
        start_time = pygame.time.get_ticks()
        max_duration = 10000  # 10 seconds in milliseconds
        
        while True:
            state = event_handler.poll()
            
            if state.quit:
                pygame.quit()
                raise SystemExit
            
            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                place_image(screen, img_path)
                pygame.display.flip()
                _flush_input()
            
            elapsed = pygame.time.get_ticks() - start_time
            
            # Exit if SPACE pressed (after min reading time) or 6 seconds elapsed
            if (state.next_page and elapsed >= cfg.MIN_READING_TIME) or elapsed >= max_duration:
                break
            
            pygame.time.delay(10)

    # 10) end
    # Calculate and display total task duration
    end_time = datetime.datetime.now()
    start_time_obj = datetime.datetime.fromisoformat(cfg.START_TIME)
    total_duration = end_time - start_time_obj
    total_minutes = total_duration.total_seconds() / 60
    
    logger.info(f"Task completed successfully!")
    logger.info(f"Total task duration: {total_minutes:.2f} minutes ({int(total_duration.total_seconds())} seconds)")

    cfg.GLOBAL_END_TIME = end_time.isoformat()
    finalize_experiment(cfg.GLOBAL_END_TIME)

    pygame.quit()




