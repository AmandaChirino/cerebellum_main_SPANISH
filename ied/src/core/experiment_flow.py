# ./src/core/experiment_flow.py
"""
Experiment flow runner.
"""

from __future__ import annotations

import datetime
import pygame

import utils.config as cfg
from utils.logger import get_logger
from utils.event_handler import EventHandler
from utils.paths import load_instructions, load_stimuli
from utils.saves import create_save, finalize_phase, finalize_experiment
from ui.pygame_renderer import (
    init_display,
    toggle_full_screen,
    get_participant_id,
    place_image,
)
from core.practice import run_practice_phase
from core.test import (
    run_single_stimulus_phase,
    run_side_by_side_multiple_stimulus_phase,
    run_overlapped_multiple_stimulus_phase_targeting_shape,
    run_overlapped_multiple_stimulus_phase_targeting_line,
)


logger = get_logger("./src/core/experiment_flow")


def _flush_input() -> None:
    """Flush all pending pygame input events."""
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _wait_for_next_page(
    screen: pygame.Surface,
    event_handler: EventHandler,
    img_path,
    timeout_ms: int | None = None,
) -> pygame.Surface:
    """
    Wait until SPACE is pressed (next_page), with min reading time constraint.
    Also handles quit / fullscreen toggle.
    """
    start_ms = pygame.time.get_ticks()
    deadline = start_ms + timeout_ms if timeout_ms is not None else None

    while True:
        state = event_handler.poll()

        if state.quit:
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            place_image(screen, img_path, max_fraction=0.9)
            pygame.display.flip()
            _flush_input()

        now_ms = pygame.time.get_ticks()
        elapsed = now_ms - start_ms
        if state.next_page and elapsed >= cfg.MIN_READING_TIME:
            return screen

        if deadline is not None and now_ms >= deadline:
            return screen

    pygame.time.delay(10)


def _pre_block_isi(screen: pygame.Surface) -> pygame.Surface:
    """Show a pre-block ISI (black screen) before the first fixation cross."""
    screen.fill(cfg.BLACK_RGB)
    pygame.display.flip()
    pygame.time.delay(cfg.ISI_MS)
    pygame.event.clear()
    return screen


def run() -> None:
    """
    Deploy the full experiment flow for IED.
    """
    pygame.init()
    pygame.font.init()

    def _ts() -> str:
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        start_dt = datetime.datetime.now()
        cfg.START_TIME = _ts()
        cfg.RESULTS_DATE = start_dt.strftime("%Y_%m_%d")

        screen = init_display()

        # Admin phase: PID entry + GROUP/SESSION/DH/HU as per new flow
        screen = get_participant_id(screen)
        if cfg.MAPPING not in (1, 2):
            logger.warning("Invalid MAPPING=%s. Falling back to 1.", cfg.MAPPING)
            cfg.MAPPING = 1
        logger.info("Participant ID = %s | MAPPING = %s", cfg.PID, cfg.MAPPING)

        event_handler = EventHandler()
        create_save()

        instructions = load_instructions()
        stimuli = load_stimuli()

        current_page = 0
        while True:
            img_path = instructions[current_page]
            place_image(screen, img_path, max_fraction=0.9)
            pygame.display.flip()
            _flush_input()

            is_last_instruction = current_page >= cfg.INSTRUCTION_COUNT - 1
            timeout_ms = cfg.FINAL_INSTRUCTION_TIMEOUT_MS if is_last_instruction else None
            screen = _wait_for_next_page(screen, event_handler, img_path, timeout_ms=timeout_ms)

            if current_page >= cfg.INSTRUCTION_COUNT - 1:
                break

            current_page += 1

            if current_page == cfg.PRACTICE1:
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_practice_phase(screen, "PRACTICE1", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()
                finalize_phase("PRACTICE1", cfg.PHASE_END_TIME)
            elif current_page == cfg.PRACTICE2:
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_practice_phase(screen, "PRACTICE2", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()
                finalize_phase("PRACTICE2", cfg.PHASE_END_TIME)
            elif current_page == cfg.PHASES:
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_single_stimulus_phase(screen, "P1", stimuli, event_handler, False)
                cfg.PHASE_END_TIME = _ts()
                finalize_phase("P1", cfg.PHASE_END_TIME)
                if cfg.force_quit:
                    current_page = cfg.INSTRUCTION_COUNT - 1
                    continue
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_single_stimulus_phase(screen, "P2", stimuli, event_handler, True)
                cfg.PHASE_END_TIME = _ts()
                finalize_phase("P2", cfg.PHASE_END_TIME)
                if cfg.force_quit:
                    current_page = cfg.INSTRUCTION_COUNT - 1
                    continue
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_side_by_side_multiple_stimulus_phase(screen, "P3", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()
                finalize_phase("P3", cfg.PHASE_END_TIME)
                if cfg.force_quit:
                    current_page = cfg.INSTRUCTION_COUNT - 1
                    continue
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_overlapped_multiple_stimulus_phase_targeting_shape(screen, "P4", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()

                finalize_phase("P4", cfg.PHASE_END_TIME)
                if cfg.force_quit:
                    current_page = cfg.INSTRUCTION_COUNT - 1
                    continue
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_overlapped_multiple_stimulus_phase_targeting_shape(screen, "P5", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()

                finalize_phase("P5", cfg.PHASE_END_TIME)
                if cfg.force_quit:
                    current_page = cfg.INSTRUCTION_COUNT - 1
                    continue
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_overlapped_multiple_stimulus_phase_targeting_shape(screen, "P6", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()

                finalize_phase("P6", cfg.PHASE_END_TIME)
                if cfg.force_quit:
                    current_page = cfg.INSTRUCTION_COUNT - 1
                    continue
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_overlapped_multiple_stimulus_phase_targeting_shape(screen, "P7", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()

                finalize_phase("P7", cfg.PHASE_END_TIME)
                if cfg.force_quit:
                    current_page = cfg.INSTRUCTION_COUNT - 1
                    continue
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_overlapped_multiple_stimulus_phase_targeting_line(screen, "P8", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()

                finalize_phase("P8", cfg.PHASE_END_TIME)
                if cfg.force_quit:
                    current_page = cfg.INSTRUCTION_COUNT - 1
                    continue
                cfg.PHASE_START_TIME = _ts()
                cfg.PHASE_END_TIME = None
                screen = _pre_block_isi(screen)
                run_overlapped_multiple_stimulus_phase_targeting_line(screen, "P9", stimuli, event_handler)
                cfg.PHASE_END_TIME = _ts()

                finalize_phase("P9", cfg.PHASE_END_TIME)
    finally:
        cfg.GLOBAL_END_TIME = _ts()
        finalize_experiment(cfg.GLOBAL_END_TIME)
        pygame.quit()
