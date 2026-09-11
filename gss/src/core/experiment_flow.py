# ./src/ui/main_window.py
"""
Experiment flow runner.

This module runs the practice blocks with pygame, including:
  - Display init + participant metadata collection (PID, mapping).
  - Ordered practice blocks: color → stroop → interval → speed → accuracy → varying → test.
  - Start block is controlled by `start_from` (default: color_practice).
"""


from __future__ import annotations
from pathlib import Path
import pygame
import datetime
import time
import re

import utils.config as cfg
import utils.paths as paths
from utils.logger import get_logger
from utils.event_handler import EventHandler
from ui.pygame_render import (
    init_display,
    toggle_full_screen,
    get_participant_id,
    admin,
    place_image,
)
from core.goal_practice import speed_practice, accuracy_practice, varying_practice
from core.test import speed_test, accuracy_test, varying_test_1, varying_test_2
from core.basic_practice import color_practice, stroop_practice, interval_practice
from utils.saves import create_save, finalize_global_end_time
import utils.saves as saves

logger = get_logger("./src/core/experiment_flow")


def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _place_instruction_image(screen: pygame.Surface, img_path: Path) -> None:
    """Place an instruction image with aspect ratio preserved."""
    try:
        img = pygame.image.load(str(img_path)).convert_alpha()
    except Exception as e:
        logger.error(f"[instruction_image] Failed to load image -> {img_path} | {e}")
        return

    screen_w, screen_h = screen.get_size()
    img_w, img_h = img.get_size()
    scale = min(screen_w / img_w, screen_h / img_h)
    resize = (max(1, int(img_w * scale)), max(1, int(img_h * scale)))
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)


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
                _place_instruction_image(screen, img_path)
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
                _place_instruction_image(screen, img_path)
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
    _place_instruction_image(screen, img_path)
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
    _place_instruction_image(screen, img_path)
    pygame.display.flip()
    _flush_input()
    return _wait_for_end_page(
        screen,
        event_handler,
        img_path=img_path,
        max_duration_ms=max_duration_ms,
    )


def _show_block_prompt_page(
    screen: pygame.Surface,
    img_path: Path,
    event_handler: EventHandler,
) -> pygame.Surface:
    """Show the goal prompt page using the same paging behavior as instructions."""
    return _show_instruction_page(screen, img_path, event_handler)


def _goal_prompt_for_code(code: str) -> Path:
    """Return the prompt page path for a goal code."""
    if code == "S":
        return paths.Speed_Block
    if code == "A":
        return paths.Accuracy_Block
    return paths.Varying_Block


def _run_test_round(screen: pygame.Surface, code: str, varying_index: int) -> tuple[pygame.Surface, int]:
    """Run a single test round from cfg.task_sequence."""
    if code == "S":
        return speed_test(screen), varying_index
    if code == "A":
        return accuracy_test(screen), varying_index
    if code == "V":
        if varying_index == 0:
            return varying_test_1(screen), 1
        return varying_test_2(screen), varying_index + 1

    logger.warning(f"Unknown code in task_sequence: {code}")
    return screen, varying_index


def run() -> None:
    """
    Run the full practice flow.

    Steps:
        1) init display
        2) get PID + mapping
        3) admin: group/session/DH/UH
        4) create save
        5) run blocks by order from `start_from`:
            color_practice
            → stroop_practice
            → interval_practice
            → spee_practice
            → accuracy_practice
            → varying_practice
            → run_test
        6) finalize and quit

    :return: None
    """
    pygame.init()
    pygame.font.init()
    # Fix macOS IOHIDManager joystick lifecycle bug:
    # joystick appears detected but get_axis() returns 0 because HID cleanup
    # from previous run hasn't finished. Force a full subsystem cycle.
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
    cfg.START_TIME = datetime.datetime.now().isoformat()
    cfg._start_time = cfg.START_TIME

    try:
        screen = init_display()
        cfg.global_start_time = datetime.datetime.now().isoformat()
        # 1) PID + MAPPING (computed from PID suffix in admin flow)
        screen = get_participant_id(screen)
        paths.bind_instructions()

        # 2) Hands (admin flow)
        screen = admin(screen)
        logger.info(f"Participant ID={cfg.PID} | GROUP={cfg.GROUP} | SESSION={cfg.SESSION} | DH={cfg.DH} | UH={cfg.UH}")
                # Derive PID-based version (mod 12) from PID suffix split by '-' or '_' and store in cfg.version
        try:
            pid_str = cfg.PID or ""
            parts = [p for p in re.split(r"[-_]\s*", pid_str) if p]
            suffix = parts[-1] if parts else ""
            # Try the last token directly; if it has letters (e.g. "aaa05"), extract trailing digits
            m = re.search(r'\d+$', suffix)
            if m:
                pid_suffix_num = int(m.group())
                cfg.version = pid_suffix_num % 12
                logger.info(f"Derived version={cfg.version} from PID trailing digits {pid_suffix_num}")
            else:
                cfg.version = None
                logger.info("No trailing digits found in PID; will use default task sequence index 0")
        except Exception as e:
            cfg.version = None
            logger.warning(f"Failed to derive version from PID: {e}")

        # Set task_sequence from version; if version is None, fallback to index 0
        try:
            if hasattr(cfg, "TASK_SEQUENCES") and cfg.TASK_SEQUENCES:
                _seq_idx = (cfg.version % len(cfg.TASK_SEQUENCES)) if (cfg.version is not None) else 0
                cfg.task_sequence = cfg.TASK_SEQUENCES[_seq_idx]
                logger.info(f"Task sequence index={_seq_idx} value={cfg.task_sequence}")
            else:
                cfg.task_sequence = None
                logger.info("Task sequence not set (sequences missing)")
        except Exception as e:
            cfg.task_sequence = None
            logger.warning(f"Failed to set task_sequence: {e}")# Event handling
        create_save()
        saves.create_joy_save()

        instruction_pages = getattr(paths, "INSTRUCTIONS", [])
        if len(instruction_pages) < 50:
            raise RuntimeError(f"Expected 50 instruction pages, found {len(instruction_pages)}")

        event_handler = EventHandler()
        test_sequence = tuple(cfg.task_sequence or ('S', 'A', 'V', 'V'))
        if len(test_sequence) < 4:
            raise RuntimeError(f"Expected 4 test rounds in task_sequence, found {len(test_sequence)}")

                # --- start_from support (string-based) ---
        def _normalize(name: str) -> str:
            return ''.join(ch for ch in name.lower() if ch.isalnum())

        def _lookup_start_page(name: str) -> int:
            key_norm = _normalize(name)
            # prefer exact key in config (allow underscores)
            pages = getattr(cfg, 'START_FROM_PAGES', {}) or {}
            # try exact
            if key_norm in (k.replace('_','') for k in pages.keys()):
                for k,v in pages.items():
                    if key_norm == k.replace('_',''):
                        return int(v)
            # simple aliases
            aliases = {
                'color': 'color_practice',
                'stroop': 'stroop_practice',
                'interval': 'interval_practice',
                'speed': 'speed_practice',
                'accuracy': 'accuracy_practice',
                'varying': 'varying_practice',
                'test': 'run_test', 'tests': 'run_test', 'runtest': 'run_test',
                'end': 'end', 'finish': 'end',
            }
            if key_norm in aliases:
                canon = aliases[key_norm]
                if canon in pages:
                    return int(pages[canon])
            return 1

        start_from = getattr(cfg, 'start_from', None)
        if isinstance(start_from, str) and start_from.strip():
            start_page = max(1, min(_lookup_start_page(start_from), len(instruction_pages)))
            logger.info(f"start_from='{start_from}' -> starting at instruction page {start_page}")
        else:
            start_page = 1

        # If starting within the tests, pre-compute how many V rounds have already occurred
        test_pages = [40, 43, 46, 49]
        varying_index = 0
        if start_page > test_pages[0]:
            prior_vs = sum(1 for p, code in zip(test_pages, test_sequence) if (p < start_page and code == 'V'))
            varying_index = prior_vs

        for page_number, img_path in enumerate(instruction_pages, start=1):
            if page_number < start_page:
                continue
            if page_number == 50:
                screen = _show_end_page(screen, img_path, event_handler)
                break

            if page_number not in (28, 32, 40, 43, 46, 49):
                screen = _show_instruction_page(screen, img_path, event_handler)

            if page_number == 10:
                screen = color_practice(screen)
            elif page_number == 18:
                screen = stroop_practice(screen)
            elif page_number == 22:
                screen = interval_practice(screen)
            elif page_number == 28:
                screen = _show_instruction_page(screen, img_path, event_handler)
                screen = speed_practice(screen)
            elif page_number == 32:
                screen = _show_instruction_page(screen, img_path, event_handler)
                screen = accuracy_practice(screen)
            elif page_number == 36:
                screen = varying_practice(screen)
            elif page_number == 40:
                screen = _show_block_prompt_page(screen, _goal_prompt_for_code(test_sequence[0]), event_handler)
                screen = _show_instruction_page(screen, img_path, event_handler)
                screen, varying_index = _run_test_round(screen, test_sequence[0], varying_index)
            elif page_number == 43:
                screen = _show_block_prompt_page(screen, _goal_prompt_for_code(test_sequence[1]), event_handler)
                screen = _show_instruction_page(screen, img_path, event_handler)
                screen, varying_index = _run_test_round(screen, test_sequence[1], varying_index)
            elif page_number == 46:
                screen = _show_block_prompt_page(screen, _goal_prompt_for_code(test_sequence[2]), event_handler)
                screen = _show_instruction_page(screen, img_path, event_handler)
                screen, varying_index = _run_test_round(screen, test_sequence[2], varying_index)
            elif page_number == 49:
                screen = _show_block_prompt_page(screen, _goal_prompt_for_code(test_sequence[3]), event_handler)
                screen = _show_instruction_page(screen, img_path, event_handler)
                screen, varying_index = _run_test_round(screen, test_sequence[3], varying_index)
        logger.info("Task completed successfully!")
    finally:
        if cfg.START_TIME is not None:
            try:
                start_dt = datetime.datetime.fromisoformat(cfg.START_TIME)
                elapsed_s = (datetime.datetime.now() - start_dt).total_seconds()
                logger.info(f"Total task duration: {elapsed_s / 60:.2f} minutes ({int(elapsed_s)} seconds)")
            except ValueError:
                pass

        finalize_global_end_time()
        cfg.global_end_time = datetime.datetime.now().isoformat()














