"""
Goal practice blocks (Speed / Accuracy / Varying): interval-based trials.
"""

from __future__ import annotations

import datetime
import random
from pathlib import Path

import pygame

import utils.config as cfg
from utils.logger import get_logger
from utils.event_handler import EventHandler
from ui.pygame_render import toggle_full_screen
from utils.saves import update_save, finalize_block_end_time
import utils.saves as saves
from utils.paths import WORD_COLOR_STIMULI
from core.basic_practice import _show_interval_feedback, _show_isi, _show_goal_image, _next_stroop_pair
from utils.time_utils import rand_whole_second_ms


logger = get_logger("./src/core/goal_practice")


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _show_centered_stimulus(screen: pygame.Surface, stim_path: Path, context: str) -> None:
    """Draw the stimulus centered without any goal overlay."""
    screen.fill(cfg.BLACK_RGB)
    try:
        stim_img = pygame.image.load(str(stim_path)).convert_alpha()
    except Exception as e:
        logger.error(f"[{context}] Failed to load stimulus: {stim_path} | {e}")
        return
    stim_rect = stim_img.get_rect(center=screen.get_rect().center)
    screen.blit(stim_img, stim_rect)
    pygame.display.flip()


def speed_practice(screen: pygame.Surface) -> pygame.Surface:
    """Interval-based practice with Speed goal."""
    event_handler = EventHandler()

    # Block start time on first stimulus flip
    block_started = False

    total_intervals = int(getattr(cfg, "SPEED_PRACTICE_COUNT", cfg.INTERVAL_PRACTICE_COUNT))
    _whole_secs = list(range(int(cfg.INTERVAL_MIN) // 1000, int(cfg.INTERVAL_MAX) // 1000 + 1))
    random.shuffle(_whole_secs)
    _durations = [s * 1000 for s in _whole_secs[:total_intervals]]

    for interval_idx, duration in enumerate(_durations):
        interval_t0 = pygame.time.get_ticks()
        correct_cnt = 0
        total_cnt = 0

        # seed first stimulus
        prev_pair: tuple[str, str] | None = None
        word, color, stim_path = _next_stroop_pair(None)
        _show_goal_image(screen, "S")
        _show_isi(screen)
        _show_centered_stimulus(screen, stim_path, "speed_practice")
        stim_t0 = pygame.time.get_ticks()  # right after flip
        saves.log_joy_frame(stim_t0, "speed_practice", 0.0, 0.0, "stim_onset")
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()
        cfg.joy_response = None
        cfg.key_response = None

        while pygame.time.get_ticks() - interval_t0 < duration:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "speed_practice", state.x_raw, state.y_raw, "")

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_stimulus(screen, stim_path, "speed_practice")
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "speed_practice", 0.0, 0.0, "stim_onset")
                _flush_input()

            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "speed_practice", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                correct_dir = cfg.expected_dir_for_color(color)
                result = 1 if selected_dir == correct_dir else 0
                rt = pygame.time.get_ticks() - stim_t0

                total_cnt += 1
                if result == 1:
                    correct_cnt += 1

                # save
                update_save(
                    "speed_practice",
                    "practice",
                    f"{word}_in_{color}",
                    correct_dir,
                    "",
                    correct_dir,
                    selected_dir or "",
                    result,
                    int(rt),
                    str(stim_path),
                    goal='speed',
                    block_type='fixed',
                    congruency='congruent' if word == color else 'incongruent',
                    word=word,
                    ink=color,
                    interval_index=interval_idx + 1,
                    trial_in_interval=total_cnt,
                    interval_duration_ms=duration,
                    time_in_interval_ms=stim_t0 - interval_t0,
                    joy_word_dir=cfg.expected_dir_for_color(word),
                )

                # next stimulus (avoid same word and same color)
                prev_pair = (word, color)
                word, color, stim_path = _next_stroop_pair(prev_pair)
                _show_isi(screen)
                _show_centered_stimulus(screen, stim_path, "speed_practice")
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "speed_practice", 0.0, 0.0, "stim_onset")
                _flush_input()
                cfg.joy_response = None
                cfg.key_response = None

            pygame.time.delay(1)

        # interval feedback screen
        _show_interval_feedback(screen, correct_cnt, is_last=(interval_idx == total_intervals - 1))
        pygame.time.delay(int(cfg.FB_SCREEN_DURATION))
        _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen

def accuracy_practice(screen: pygame.Surface) -> pygame.Surface:
    """Interval-based practice with Accuracy goal."""
    event_handler = EventHandler()
    block_started = False

    total_intervals = int(getattr(cfg, "ACCURACY_PRACTICE_COUNT", cfg.INTERVAL_PRACTICE_COUNT))
    _whole_secs = list(range(int(cfg.INTERVAL_MIN) // 1000, int(cfg.INTERVAL_MAX) // 1000 + 1))
    random.shuffle(_whole_secs)
    _durations = [s * 1000 for s in _whole_secs[:total_intervals]]

    for interval_idx, duration in enumerate(_durations):
        interval_t0 = pygame.time.get_ticks()
        correct_cnt = 0
        total_cnt = 0

        # seed first stimulus
        prev_pair: tuple[str, str] | None = None
        word, color, stim_path = _next_stroop_pair(None)
        _show_goal_image(screen, "A")
        _show_isi(screen)
        _show_centered_stimulus(screen, stim_path, "accuracy_practice")
        stim_t0 = pygame.time.get_ticks()  # right after flip
        saves.log_joy_frame(stim_t0, "accuracy_practice", 0.0, 0.0, "stim_onset")
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()
        cfg.joy_response = None
        cfg.key_response = None

        while pygame.time.get_ticks() - interval_t0 < duration:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "accuracy_practice", state.x_raw, state.y_raw, "")

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_stimulus(screen, stim_path, "accuracy_practice")
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "accuracy_practice", 0.0, 0.0, "stim_onset")
                _flush_input()

            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "accuracy_practice", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                correct_dir = cfg.expected_dir_for_color(color)
                result = 1 if selected_dir == correct_dir else 0
                rt = pygame.time.get_ticks() - stim_t0

                total_cnt += 1
                if result == 1:
                    correct_cnt += 1

                update_save(
                    "accuracy_practice",
                    "practice",
                    f"{word}_in_{color}",
                    correct_dir,
                    "",
                    correct_dir,
                    selected_dir or "",
                    result,
                    int(rt),
                    str(stim_path),
                    goal='accuracy',
                    block_type='fixed',
                    congruency='congruent' if word == color else 'incongruent',
                    word=word,
                    ink=color,
                    interval_index=interval_idx + 1,
                    trial_in_interval=total_cnt,
                    interval_duration_ms=duration,
                    time_in_interval_ms=stim_t0 - interval_t0,
                    joy_word_dir=cfg.expected_dir_for_color(word),
                )

                prev_pair = (word, color)
                word, color, stim_path = _next_stroop_pair(prev_pair)
                _show_isi(screen)
                _show_centered_stimulus(screen, stim_path, "accuracy_practice")
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "accuracy_practice", 0.0, 0.0, "stim_onset")
                _flush_input()
                cfg.joy_response = None
                cfg.key_response = None

            pygame.time.delay(1)

        _show_interval_feedback(screen, correct_cnt, is_last=(interval_idx == total_intervals - 1))
        pygame.time.delay(int(cfg.FB_SCREEN_DURATION))
        _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen

def varying_practice(screen: pygame.Surface) -> pygame.Surface:
    """Interval-based practice mixing Speed and Accuracy goals.

    The block contains cfg.VARYING_PRACTICE_SPEED_COUNT Speed intervals and
    cfg.VARYING_PRACTICE_ACCURACY_COUNT Accuracy intervals in randomized order.
    Each interval behaves like speed_practice/accuracy_practice: unlimited trials
    within a randomly sampled duration [cfg.INTERVAL_MIN, cfg.INTERVAL_MAX].
    """
    event_handler = EventHandler()

    # Build randomized schedule, e.g., ['S','A','S','A','A','A']
    n_s = int(getattr(cfg, "VARYING_PRACTICE_SPEED_COUNT", 0))
    n_a = int(getattr(cfg, "VARYING_PRACTICE_ACCURACY_COUNT", 0))
    schedule: list[str] = ["S"] * n_s + ["A"] * n_a
    random.shuffle(schedule)

    _whole_secs = list(range(int(cfg.INTERVAL_MIN) // 1000, int(cfg.INTERVAL_MAX) // 1000 + 1))
    random.shuffle(_whole_secs)
    _durations = [s * 1000 for s in _whole_secs[:len(schedule)]]

    block_started = False

    for idx, (goal, duration) in enumerate(zip(schedule, _durations)):
        interval_t0 = pygame.time.get_ticks()
        correct_cnt = 0
        total_cnt = 0

        # seed first stimulus
        prev_pair: tuple[str, str] | None = None
        word, color, stim_path = _next_stroop_pair(None)
        _show_goal_image(screen, goal)
        _show_isi(screen)

        if goal == "S":
            _show_centered_stimulus(screen, stim_path, "varying_practice")
        else:
            _show_centered_stimulus(screen, stim_path, "varying_practice")
        stim_t0 = pygame.time.get_ticks()  # right after flip
        saves.log_joy_frame(stim_t0, "varying_practice", 0.0, 0.0, "stim_onset")

        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()
        cfg.joy_response = None
        cfg.key_response = None

        while pygame.time.get_ticks() - interval_t0 < duration:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "varying_practice", state.x_raw, state.y_raw, "")

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                if goal == "S":
                    _show_centered_stimulus(screen, stim_path, "varying_practice")
                else:
                    _show_centered_stimulus(screen, stim_path, "varying_practice")
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "varying_practice", 0.0, 0.0, "stim_onset")
                _flush_input()

            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "varying_practice", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                correct_dir = cfg.expected_dir_for_color(color)
                result = 1 if selected_dir == correct_dir else 0
                rt = pygame.time.get_ticks() - stim_t0

                total_cnt += 1
                if result == 1:
                    correct_cnt += 1

                # save
                goal_tag = "speed" if goal == "S" else "accuracy"
                update_save(
                    "varying_practice",
                    "practice",
                    f"{word}_in_{color}",
                    correct_dir,
                    "",
                    correct_dir,
                    selected_dir or "",
                    result,
                    int(rt),
                    str(stim_path),
                    goal=goal_tag,
                    block_type='varying',
                    congruency='congruent' if word == color else 'incongruent',
                    word=word,
                    ink=color,
                    interval_index=idx + 1,
                    trial_in_interval=total_cnt,
                    interval_duration_ms=duration,
                    time_in_interval_ms=stim_t0 - interval_t0,
                    joy_word_dir=cfg.expected_dir_for_color(word),
                )

                # next stimulus (avoid same word and same color)
                prev_pair = (word, color)
                word, color, stim_path = _next_stroop_pair(prev_pair)
                _show_isi(screen)
                if goal == "S":
                    _show_centered_stimulus(screen, stim_path, "varying_practice")
                else:
                    _show_centered_stimulus(screen, stim_path, "varying_practice")
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "varying_practice", 0.0, 0.0, "stim_onset")
                _flush_input()
                cfg.joy_response = None
                cfg.key_response = None

            pygame.time.delay(1)

        # interval feedback screen
        _show_interval_feedback(screen, correct_cnt, is_last=(idx == len(schedule) - 1))
        pygame.time.delay(int(cfg.FB_SCREEN_DURATION))
        _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen



