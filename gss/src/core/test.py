"""
Test blocks: speed_test / accuracy_test / varying_test_1 / varying_test_2.

- No trial-by-trial feedback (tests).
- Interval behavior mirrors goal_practice.interval (duration-limited, unlimited trials).
- Varying tests mix Speed and Accuracy intervals in randomized order.
- Block execution order is determined by cfg.task_sequence (e.g., V S V A).
  The first 'V' maps to varying_test_1 and the second to varying_test_2.
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
from core.basic_practice import _show_isi, _show_goal_image, _show_interval_feedback, _next_stroop_pair
from utils.time_utils import rand_whole_second_ms

logger = get_logger("./src/core/test")


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _show_centered_stimulus(screen: pygame.Surface, stim_path: Path, goal: str) -> None:
    """Draw stimulus centered without any goal overlay."""
    screen.fill(cfg.BLACK_RGB)
    try:
        stim_img = pygame.image.load(str(stim_path)).convert_alpha()
    except Exception as e:
        logger.error(f"[test:{goal}] Failed to load stimulus: {stim_path} | {e}")
        return
    stim_rect = stim_img.get_rect(center=screen.get_rect().center)
    screen.blit(stim_img, stim_rect)
    pygame.display.flip()


def _durations_for_goal(goal: str) -> list[int] | None:
    """Return preset durations list for S/A in full mode; otherwise None."""
    if getattr(cfg, 'MODE', 'demo') != 'full':
        return None
    if goal == 'S' and hasattr(cfg, 'SPEED_TEST_INTERVALS'):
        return list(getattr(cfg, 'SPEED_TEST_INTERVALS') or [])
    if goal == 'A' and hasattr(cfg, 'ACCURACY_TEST_INTERVALS'):
        return list(getattr(cfg, 'ACCURACY_TEST_INTERVALS') or [])
    return None



def _run_interval_block(screen: pygame.Surface, block_name: str, goal: str) -> pygame.Surface:
    """Core runner: duration-limited intervals with end-of-interval status."""
    event_handler = EventHandler()
    block_started = False

    durations_list = _durations_for_goal(goal)
    if durations_list:
        n_intervals = len(durations_list)
    else:
        n_intervals = int(getattr(cfg, 'SPEED_TEST_COUNT' if goal == 'S' else 'ACCURACY_TEST_COUNT', 0))

    for i in range(int(n_intervals)):
        if durations_list and i < len(durations_list):
            duration = int(durations_list[i])
        else:
            duration = rand_whole_second_ms(int(cfg.INTERVAL_MIN), int(cfg.INTERVAL_MAX))

        interval_t0 = pygame.time.get_ticks()
        prev_pair: tuple[str, str] | None = None
        word, color, stim_path = _next_stroop_pair(None)

        _show_goal_image(screen, goal)
        _show_isi(screen)
        _show_centered_stimulus(screen, stim_path, goal)
        stim_t0 = pygame.time.get_ticks()  # right after flip
        saves.log_joy_frame(stim_t0, block_name, 0.0, 0.0, "stim_onset")
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()
        cfg.joy_response = None
        cfg.key_response = None

        correct_cnt = 0
        total_cnt = 0

        while pygame.time.get_ticks() - interval_t0 < duration:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), block_name, state.x_raw, state.y_raw, "")
            if state.quit:
                pygame.quit()
                raise SystemExit
            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_stimulus(screen, stim_path, goal)
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, block_name, 0.0, 0.0, "stim_onset")
                _flush_input()

            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), block_name, state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                correct_dir = cfg.expected_dir_for_color(color)
                result = 1 if selected_dir == correct_dir else 0
                rt = pygame.time.get_ticks() - stim_t0

                goal_str = 'speed' if goal == 'S' else 'accuracy'
                block_type_str = 'varying' if 'varying' in block_name else 'fixed'
                congruency_str = 'congruent' if word == color else 'incongruent'
                word_dir = cfg.expected_dir_for_color(word)
                time_in_interval = stim_t0 - interval_t0

                update_save(
                    block_name,
                    "test",
                    f"{word}_in_{color}",
                    correct_dir,
                    "",
                    correct_dir,
                    selected_dir or "",
                    result,
                    int(rt),
                    str(stim_path),
                    goal=goal_str,
                    block_type=block_type_str,
                    congruency=congruency_str,
                    word=word,
                    ink=color,
                    interval_index=i + 1,
                    trial_in_interval=total_cnt + 1,
                    interval_duration_ms=duration,
                    time_in_interval_ms=time_in_interval,
                    joy_word_dir=word_dir,
                )

                total_cnt += 1
                if result == 1:
                    correct_cnt += 1

                prev_pair = (word, color)
                word, color, stim_path = _next_stroop_pair(prev_pair)
                _show_isi(screen)
                _show_centered_stimulus(screen, stim_path, goal)
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, block_name, 0.0, 0.0, "stim_onset")
                _flush_input()
                cfg.joy_response = None
                cfg.key_response = None

            pygame.time.delay(1)

        # end-of-interval status
        acc = (correct_cnt / total_cnt * 100.0) if total_cnt > 0 else 0.0
        _show_interval_feedback(screen, acc, total_cnt, is_last=(i == int(n_intervals) - 1))
        _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen

def speed_test(screen: pygame.Surface) -> pygame.Surface:
    return _run_interval_block(screen, "speed_test", 'S')


def accuracy_test(screen: pygame.Surface) -> pygame.Surface:
    return _run_interval_block(screen, "accuracy_test", 'A')



def varying_test_1(screen: pygame.Surface) -> pygame.Surface:
        # Build (goal, duration_ms) list for varying block 1
    if getattr(cfg, "MODE", "demo") == "full" and hasattr(cfg, "VARYING1_TEST_INTERVALS") and getattr(cfg, "VARYING1_TEST_INTERVALS"):
        tokens = list(getattr(cfg, "VARYING1_TEST_INTERVALS") or [])
        pairs = []
        for tok in tokens:
            try:
                sec = int(str(tok).split("_")[-1])
                dur = sec * 1000
            except Exception:
                dur = rand_whole_second_ms(int(cfg.INTERVAL_MIN), int(cfg.INTERVAL_MAX))
            goal = 'S' if str(tok).startswith('SPEED_') else 'A'
            pairs.append((goal, int(dur)))
    else:
        n_s = int(getattr(cfg, 'VARYING_TEST_SPEED_COUNT', 0))
        n_a = int(getattr(cfg, 'VARYING_TEST_ACCURACY_COUNT', 0))
        schedule = ['S'] * n_s + ['A'] * n_a
        random.shuffle(schedule)
        pairs = [(g, rand_whole_second_ms(int(cfg.INTERVAL_MIN), int(cfg.INTERVAL_MAX))) for g in schedule]
    event_handler = EventHandler()
    pairs_len = len(pairs)
    block_started = False
    saves.reset_prev_goal()

    for interval_idx, (goal, duration) in enumerate(pairs, 1):
        interval_t0 = pygame.time.get_ticks()
        prev_pair: tuple[str, str] | None = None
        word, color, stim_path = _next_stroop_pair(None)
        _show_goal_image(screen, goal)
        _show_isi(screen)
        _show_centered_stimulus(screen, stim_path, goal)
        stim_t0 = pygame.time.get_ticks()  # right after flip
        saves.log_joy_frame(stim_t0, "varying_test_1", 0.0, 0.0, "stim_onset")
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()
        cfg.joy_response = None
        cfg.key_response = None

        correct_cnt = 0
        total_cnt = 0

        while pygame.time.get_ticks() - interval_t0 < duration:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "varying_test_1", state.x_raw, state.y_raw, "")
            if state.quit:
                pygame.quit()
                raise SystemExit
            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_stimulus(screen, stim_path, goal)
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "varying_test_1", 0.0, 0.0, "stim_onset")
                _flush_input()

            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "varying_test_1", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                correct_dir = cfg.expected_dir_for_color(color)
                result = 1 if selected_dir == correct_dir else 0
                rt = pygame.time.get_ticks() - stim_t0

                goal_str = 'speed' if goal == 'S' else 'accuracy'
                congruency_str = 'congruent' if word == color else 'incongruent'
                word_dir = cfg.expected_dir_for_color(word)
                time_in_interval = stim_t0 - interval_t0

                update_save(
                    "varying_test_1",
                    "test",
                    f"{word}_in_{color}",
                    correct_dir,
                    "",
                    correct_dir,
                    selected_dir or "",
                    result,
                    int(rt),
                    str(stim_path),
                    goal=goal_str,
                    block_type='varying',
                    congruency=congruency_str,
                    word=word,
                    ink=color,
                    interval_index=interval_idx,
                    trial_in_interval=total_cnt + 1,
                    interval_duration_ms=duration,
                    time_in_interval_ms=time_in_interval,
                    joy_word_dir=word_dir,
                )

                total_cnt += 1
                if result == 1:
                    correct_cnt += 1

                prev_pair = (word, color)
                word, color, stim_path = _next_stroop_pair(prev_pair)
                _show_isi(screen)
                _show_centered_stimulus(screen, stim_path, goal)
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "varying_test_1", 0.0, 0.0, "stim_onset")
                _flush_input()
                cfg.joy_response = None
                cfg.key_response = None

            pygame.time.delay(1)

        acc = (correct_cnt / total_cnt * 100.0) if total_cnt > 0 else 0.0
        _show_interval_feedback(screen, acc, total_cnt, is_last=(interval_idx == pairs_len))
        _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen


def varying_test_2(screen: pygame.Surface) -> pygame.Surface:
        # Build (goal, duration_ms) list for varying block 2
    if getattr(cfg, "MODE", "demo") == "full" and hasattr(cfg, "VARYING2_TEST_INTERVALS") and getattr(cfg, "VARYING2_TEST_INTERVALS"):
        tokens = list(getattr(cfg, "VARYING2_TEST_INTERVALS") or [])
        pairs = []
        for tok in tokens:
            try:
                sec = int(str(tok).split("_")[-1])
                dur = sec * 1000
            except Exception:
                dur = rand_whole_second_ms(int(cfg.INTERVAL_MIN), int(cfg.INTERVAL_MAX))
            goal = 'S' if str(tok).startswith('SPEED_') else 'A'
            pairs.append((goal, int(dur)))
    else:
        n_s = int(getattr(cfg, 'VARYING_TEST_SPEED_COUNT', 0))
        n_a = int(getattr(cfg, 'VARYING_TEST_ACCURACY_COUNT', 0))
        schedule = ['S'] * n_s + ['A'] * n_a
        random.shuffle(schedule)
        pairs = [(g, rand_whole_second_ms(int(cfg.INTERVAL_MIN), int(cfg.INTERVAL_MAX))) for g in schedule]
    event_handler = EventHandler()
    pairs_len = len(pairs)
    block_started = False
    saves.reset_prev_goal()

    for interval_idx, (goal, duration) in enumerate(pairs, 1):
        interval_t0 = pygame.time.get_ticks()
        prev_pair: tuple[str, str] | None = None
        word, color, stim_path = _next_stroop_pair(None)
        _show_goal_image(screen, goal)
        _show_isi(screen)
        _show_centered_stimulus(screen, stim_path, goal)
        stim_t0 = pygame.time.get_ticks()  # right after flip
        saves.log_joy_frame(stim_t0, "varying_test_2", 0.0, 0.0, "stim_onset")
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()
        cfg.joy_response = None
        cfg.key_response = None

        correct_cnt = 0
        total_cnt = 0

        while pygame.time.get_ticks() - interval_t0 < duration:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "varying_test_2", state.x_raw, state.y_raw, "")
            if state.quit:
                pygame.quit()
                raise SystemExit
            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_stimulus(screen, stim_path, goal)
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "varying_test_2", 0.0, 0.0, "stim_onset")
                _flush_input()

            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "varying_test_2", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                correct_dir = cfg.expected_dir_for_color(color)
                result = 1 if selected_dir == correct_dir else 0
                rt = pygame.time.get_ticks() - stim_t0

                goal_str = 'speed' if goal == 'S' else 'accuracy'
                congruency_str = 'congruent' if word == color else 'incongruent'
                word_dir = cfg.expected_dir_for_color(word)
                time_in_interval = stim_t0 - interval_t0

                update_save(
                    "varying_test_2",
                    "test",
                    f"{word}_in_{color}",
                    correct_dir,
                    "",
                    correct_dir,
                    selected_dir or "",
                    result,
                    int(rt),
                    str(stim_path),
                    goal=goal_str,
                    block_type='varying',
                    congruency=congruency_str,
                    word=word,
                    ink=color,
                    interval_index=interval_idx,
                    trial_in_interval=total_cnt + 1,
                    interval_duration_ms=duration,
                    time_in_interval_ms=time_in_interval,
                    joy_word_dir=word_dir,
                )

                total_cnt += 1
                if result == 1:
                    correct_cnt += 1

                prev_pair = (word, color)
                word, color, stim_path = _next_stroop_pair(prev_pair)
                _show_isi(screen)
                _show_centered_stimulus(screen, stim_path, goal)
                stim_t0 = pygame.time.get_ticks()  # right after flip
                saves.log_joy_frame(stim_t0, "varying_test_2", 0.0, 0.0, "stim_onset")
                _flush_input()
                cfg.joy_response = None
                cfg.key_response = None

            pygame.time.delay(1)

        acc = (correct_cnt / total_cnt * 100.0) if total_cnt > 0 else 0.0
        _show_interval_feedback(screen, acc, total_cnt, is_last=(interval_idx == pairs_len))
        _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen

# ---------- Orchestration ----------

def _show_block_intro(screen: pygame.Surface, label: str) -> None:
    """Show a short intro page before each test block.
    - Background: BLACK_RGB
    - Text color: COCO_RGB
    - Content: task sequence + current block label (speed/accuracy/varying)
    """
    screen.fill(cfg.BLACK_RGB)
    try:
        font_title = pygame.font.SysFont(None, cfg.FONT_LARGE)
        font_body = pygame.font.SysFont(None, cfg.FONT_SMALL)
    except Exception:
        font_title = pygame.font.Font(None, cfg.FONT_LARGE)
        font_body = pygame.font.Font(None, cfg.FONT_SMALL)

    seq = cfg.task_sequence if cfg.task_sequence else ("S", "A", "V", "V")
    seq_text = "Task sequence: " + " ".join(seq)
    title_text = f"Current block: {label}"

    title_surf = font_title.render(title_text, True, cfg.COCO_RGB)
    seq_surf = font_body.render(seq_text, True, cfg.COCO_RGB)

    center = screen.get_rect().center
    title_rect = title_surf.get_rect(center=(center[0], center[1]-20))
    seq_rect = seq_surf.get_rect(center=(center[0], center[1]+30))

    screen.blit(title_surf, title_rect)
    screen.blit(seq_surf, seq_rect)
    pygame.display.flip()
    pygame.time.delay(int(getattr(cfg, 'FB_DURATION', 1000)))
    pygame.event.clear()


def run_test(screen: pygame.Surface) -> pygame.Surface:
    """Run 4 test blocks in the order specified by cfg.task_sequence.

    Mapping: S -> speed_test, A -> accuracy_test, V -> varying_test_1 / varying_test_2 (in order).
    """
    sequence = cfg.task_sequence if cfg.task_sequence else ("S","A","V","V")

    v_count = 0
    for code in sequence:
        if code == 'S':
            _show_block_intro(screen, 'speed')
            screen = speed_test(screen)
        elif code == 'A':
            _show_block_intro(screen, 'accuracy')
            screen = accuracy_test(screen)
        elif code == 'V':
            v_count += 1
            _show_block_intro(screen, 'varying')
            if v_count == 1:
                screen = varying_test_1(screen)
            else:
                screen = varying_test_2(screen)
        else:
            logger.warning(f"Unknown code in task_sequence: {code}")
    return screen





