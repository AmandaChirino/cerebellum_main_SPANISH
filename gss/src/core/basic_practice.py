"""
Color mapping practice using joystick with JOY_MODE == 4.

Plays a randomized sequence of X_[COLOR].png stimuli and collects joystick
responses with no fixed response window. Feedback is shown after each trial.
The sequence contains cfg.COLOR_PRACTICE_COUNT items and avoids consecutive
repetition of the same color.
"""

from __future__ import annotations

import datetime
import random
from pathlib import Path

import pygame

import utils.config as cfg
from utils.logger import get_logger
from utils.paths import X_COLOR_STIMULI, GSS_Speed, GSS_Accuracy, RESOURCES_DIR
from utils.event_handler import EventHandler
from ui.pygame_render import toggle_full_screen, show_feedback, place_image
from utils.saves import update_save, finalize_block_end_time
import utils.saves as saves
from utils.time_utils import rand_whole_second_ms


logger = get_logger("./src/core/practice")


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _show_isi(screen: pygame.Surface) -> None:
    """Render a black inter-stimulus interval and swallow stray input."""
    screen.fill(cfg.BLACK_RGB)
    pygame.display.flip()
    _flush_input()
    pygame.time.delay(int(cfg.ISI_DURATION))
    _flush_input()


def _show_goal_image(screen: pygame.Surface, goal: str) -> None:
    """Show the goal image scaled to fit the screen, centered, before an interval begins."""
    goal_path = GSS_Speed if goal == "S" else GSS_Accuracy
    place_image(screen, goal_path, fit_mode="contain")
    pygame.display.flip()
    _flush_input()
    pygame.time.delay(int(cfg.DISPLAY_GOAL_DURATION))
    _flush_input()


def _show_centered_image(screen: pygame.Surface, img_path: Path) -> None:
    screen.fill(cfg.BLACK_RGB)
    try:
        img = pygame.image.load(str(img_path)).convert_alpha()
    except Exception as e:
        logger.error(f"[practice] Failed to load image: {img_path} | {e}")
        return
    rect = img.get_rect(center=screen.get_rect().center)
    screen.blit(img, rect)
    pygame.display.flip()

def _build_sequence(n: int) -> list[tuple[str, Path]]:
    colors = list(X_COLOR_STIMULI.keys())  # ['BLUE','GREEN','RED','YELLOW']
    seq: list[tuple[str, Path]] = []
    prev: str | None = None
    for _ in range(n):
        choices = [c for c in colors if c != prev] if prev else colors
        color = random.choice(choices)
        seq.append((color, X_COLOR_STIMULI[color]))
        prev = color
    return seq


def _show_extra_instruction(screen: pygame.Surface, img_path: Path) -> pygame.Surface:
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    pygame.event.clear()
    event_handler = EventHandler()
    while True:
        state = event_handler.poll()
        if state.quit:
            pygame.quit(); raise SystemExit
        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
            pygame.display.flip()
        if state.next_page:
            return screen
        pygame.time.delay(10)


def _color_practice_extra(screen: pygame.Surface) -> pygame.Surface:
    instr_dir = RESOURCES_DIR / ("instructions_v1" if cfg.MAPPING == 1 else "instructions_v2")
    for name in ("Extra1", "Extra2", "Extra3"):
        screen = _show_extra_instruction(screen, instr_dir / f"{name}.png")

    event_handler = EventHandler()
    sequence = _build_sequence(20)
    block_started = False

    for trial_index, (color, stim_path) in enumerate(sequence, start=1):
        if trial_index == 1:
            _show_isi(screen)

        _show_centered_image(screen, stim_path)
        pygame.display.flip()
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()

        t0 = pygame.time.get_ticks()
        saves.log_joy_frame(t0, "color_practice_extra", 0.0, 0.0, "stim_onset")
        cfg.joy_response = None
        cfg.key_response = None
        correct_dir = cfg.expected_dir_for_color(color)
        selected_dir: str | None = None

        while True:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "color_practice_extra", state.x_raw, state.y_raw, "")
            if state.quit:
                pygame.quit(); raise SystemExit
            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_image(screen, stim_path)
                pygame.display.flip()
                t0 = pygame.time.get_ticks()
                saves.log_joy_frame(t0, "color_practice_extra", 0.0, 0.0, "stim_onset")
                _flush_input()
            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "color_practice_extra", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                result = 1 if selected_dir == correct_dir else 0
                reaction_time = pygame.time.get_ticks() - t0
                break
            pygame.time.delay(1)

        _flush_input()
        update_save(
            "color_practice_extra", "practice", f"X_in_{color}",
            correct_dir, "", correct_dir, selected_dir or "", result, int(reaction_time), str(stim_path),
        )
        show_feedback(screen, result)
        pygame.display.flip()
        pygame.time.delay(cfg.FB_DURATION)

        if trial_index < 20:
            _show_isi(screen)
        else:
            screen.fill(cfg.BLACK_RGB)
            pygame.display.flip()
            _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen


def color_practice(screen: pygame.Surface) -> pygame.Surface:
    """
    Run color practice: present X_[COLOR].png, wait for joystick response,
    judge correctness by mapping color->direction, show feedback, and save.
    """
    event_handler = EventHandler()

    count = int(cfg.COLOR_PRACTICE_COUNT)
    sequence = _build_sequence(count)
    block_started = False
    results: list[int] = []

    for trial_index, (color, stim_path) in enumerate(sequence, start=1):
        if trial_index == 1:
            _show_isi(screen)

        _show_centered_image(screen, stim_path)
        pygame.display.flip()
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()

        t0 = pygame.time.get_ticks()
        saves.log_joy_frame(t0, "color_practice", 0.0, 0.0, "stim_onset")

        cfg.joy_response = None
        cfg.key_response = None

        result = "timeout"
        reaction_time = 0
        selected_dir: str | None = None
        correct_dir = cfg.expected_dir_for_color(color)

        while True:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "color_practice", state.x_raw, state.y_raw, "")

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_image(screen, stim_path)
                pygame.display.flip()
                t0 = pygame.time.get_ticks()
                saves.log_joy_frame(t0, "color_practice", 0.0, 0.0, "stim_onset")
                _flush_input()

            elapsed = pygame.time.get_ticks() - t0

            # Accept first joystick direction
            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "color_practice", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                result = 1 if selected_dir == correct_dir else 0
                results.append(result)
                reaction_time = elapsed
                break

            pygame.time.delay(1)

        _flush_input()

        logger.info(
            "TRIAL_RESULT | block=color_practice | stim=%s | color=%s | joy=%s | correct_dir=%s | result=%s | rt_ms=%d",
            stim_path.name,
            color,
            selected_dir if selected_dir is not None else "None",
            correct_dir,
            result,
            reaction_time,
        )

        # Save record (keyboard fields left empty; normalization fills NA)
        update_save(
            "color_practice",
            "practice",
            f"X_in_{color}",
            correct_dir,
            "",
            correct_dir,
            selected_dir or "",
            result,
            int(reaction_time),
            str(stim_path),
        )

        # Feedback
        show_feedback(screen, result)
        pygame.display.flip()
        pygame.time.delay(cfg.FB_DURATION)

        if trial_index < len(sequence):
            _show_isi(screen)
        else:
            screen.fill(cfg.BLACK_RGB)
            pygame.display.flip()
            _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    last20 = results[-20:] if len(results) >= 20 else results
    if last20 and (sum(last20) / len(last20) * 100) < 90.0:
        screen = _color_practice_extra(screen)
    return screen

from utils.paths import WORD_COLOR_STIMULI

_STROOP_CONGRUENT = [(w, c) for (w, c) in WORD_COLOR_STIMULI.keys() if w == c]
_STROOP_INCONGRUENT = [(w, c) for (w, c) in WORD_COLOR_STIMULI.keys() if w != c]


def _next_stroop_pair(prev_pair: tuple[str, str] | None) -> tuple[str, str, Path]:
    """Return the next stroop (word, color, path) using the 50/50 congruence rule.

    Steps:
    1. Flip a coin: 50% congruent, 50% incongruent.
    2. Build the candidate pool (4 or 12 pairs).
    3. Filter out any pair that repeats the previous word OR ink color.
    4. Pick uniformly at random from the survivors.
    """
    pool = _STROOP_CONGRUENT if random.random() < 0.5 else _STROOP_INCONGRUENT
    if prev_pair is not None:
        candidates = [p for p in pool if p[0] != prev_pair[0] and p[1] != prev_pair[1]]
    else:
        candidates = pool
    word, color = random.choice(candidates)
    return word, color, WORD_COLOR_STIMULI[(word, color)]


def stroop_practice(screen: pygame.Surface) -> pygame.Surface:
    """
    Stroop practice using WORD_in_COLOR stimuli.
    Correctness is judged by ink color (the part after '_').
    """
    event_handler = EventHandler()

    count = int(cfg.STROOP_PRACTICE_COUNT)
    block_started = False
    prev_pair: tuple[str, str] | None = None

    for trial_index in range(1, count + 1):
        word, color, stim_path = _next_stroop_pair(prev_pair)
        prev_pair = (word, color)
        if trial_index == 1:
            _show_isi(screen)

        _show_centered_image(screen, stim_path)
        pygame.display.flip()
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()

        t0 = pygame.time.get_ticks()
        saves.log_joy_frame(t0, "stroop_practice", 0.0, 0.0, "stim_onset")
        cfg.joy_response = None
        cfg.key_response = None

        result = "timeout"
        reaction_time = 0
        selected_dir: str | None = None
        correct_dir = cfg.expected_dir_for_color(color)

        while True:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "stroop_practice", state.x_raw, state.y_raw, "")

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_image(screen, stim_path)
                pygame.display.flip()
                t0 = pygame.time.get_ticks()
                saves.log_joy_frame(t0, "stroop_practice", 0.0, 0.0, "stim_onset")
                _flush_input()

            elapsed = pygame.time.get_ticks() - t0

            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "stroop_practice", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                result = 1 if selected_dir == correct_dir else 0
                reaction_time = elapsed
                break

            pygame.time.delay(1)

        _flush_input()

        logger.info(
            "TRIAL_RESULT | block=stroop_practice | stim=%s | word=%s | color=%s | joy=%s | correct_dir=%s | result=%s | rt_ms=%d",
            stim_path.name,
            word,
            color,
            selected_dir if selected_dir is not None else "None",
            correct_dir,
            result,
            reaction_time,
        )

        update_save(
            "stroop_practice",
            "practice",
            f"{word}_in_{color}",
            correct_dir,
            "",
            correct_dir,
            selected_dir or "",
            result,
            int(reaction_time),
            str(stim_path),
            word=word,
            ink=color,
        )

        show_feedback(screen, result)
        pygame.display.flip()
        pygame.time.delay(cfg.FB_DURATION)

        if trial_index < count:
            _show_isi(screen)
        else:
            screen.fill(cfg.BLACK_RGB)
            pygame.display.flip()
            _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen


def _show_interval_feedback(screen: pygame.Surface, correct_cnt: int, total_cnt: int, goal: str | None, is_last: bool = False) -> None:
    """Show end-of-interval status with a live ITI countdown.

    Displays correct trial count centered, and a bottom-line countdown
    "the next round begins in XX s." that ticks every second for
    cfg.ITI_COUNTDOWN seconds. Handles quit and fullscreen toggle.
    """
    try:
        cfg.FB_SCREEN_DURATION = 0
    except Exception:
        pass

    event_handler = EventHandler()

    def draw(remaining_sec: int) -> None:
        screen.fill(cfg.BLACK_RGB)
        font_normal = pygame.font.SysFont(None, int(cfg.FONT_LARGE))
        cnt_text = f"Ensayos correctos: {correct_cnt}"
        total_text = f"Ensayos completados: {total_cnt}"
        cnt_surf = font_normal.render(cnt_text, True, cfg.COCO_RGB)
        total_surf = font_normal.render(total_text, True, cfg.COCO_RGB)
        secondary_alpha = int(255 * 0.3) # 30% opacity for secondary text
        if goal == "S":
            total_surf.set_alpha(255)
            cnt_surf.set_alpha(secondary_alpha)
            primary_surf, secondary_surf = total_surf, cnt_surf
        elif goal == "A":
            cnt_surf.set_alpha(255)
            total_surf.set_alpha(secondary_alpha)
            primary_surf, secondary_surf = cnt_surf, total_surf
        else:
            primary_surf, secondary_surf = cnt_surf, total_surf
        center = screen.get_rect().center
        primary_rect = primary_surf.get_rect(center=(center[0], center[1] - 30))
        screen.blit(primary_surf, primary_rect)
        secondary_rect = secondary_surf.get_rect(center=(center[0], center[1] + 30))
        screen.blit(secondary_surf, secondary_rect)
        bottom_msg = (f"este bloque termina en {remaining_sec} s." if is_last else f"la siguiente ronda comienza en {remaining_sec} s.")
        bottom_surf = font_normal.render(bottom_msg, True, cfg.COCO_RGB)
        br = bottom_surf.get_rect()
        br.midbottom = (center[0], screen.get_height() - 40)
        screen.blit(bottom_surf, br)
        pygame.display.flip()

    total_ms = max(0, int(getattr(cfg, 'ITI_COUNTDOWN', 0)) * 1000)
    start_ms = pygame.time.get_ticks()
    last_shown = None

    while True:
        now = pygame.time.get_ticks()
        elapsed = now - start_ms
        remaining_ms = max(0, total_ms - elapsed)
        remaining_sec = max(0, (remaining_ms + 999) // 1000)  # ceil to 5..1

        if last_shown != remaining_sec and remaining_sec > 0:
            draw(int(remaining_sec))
            last_shown = remaining_sec

        state = event_handler.poll()
        if state.quit:
            pygame.quit()
            raise SystemExit
        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            last_shown = None

        if remaining_ms <= 0:
            break

        pygame.time.delay(20)
def interval_practice(screen: pygame.Surface) -> pygame.Surface:
    """Interval-based practice: as many trials as possible within duration."""
    event_handler = EventHandler()

    # Block start time on first stimulus flip
    block_started = False

    total_intervals = int(cfg.INTERVAL_PRACTICE_COUNT)
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
        _show_isi(screen)
        _show_centered_image(screen, stim_path)
        pygame.display.flip()
        if not block_started:
            cfg._start_time = datetime.datetime.now().isoformat()
            block_started = True
        _flush_input()
        stim_t0 = pygame.time.get_ticks()
        saves.log_joy_frame(stim_t0, "interval_practice", 0.0, 0.0, "stim_onset")
        cfg.joy_response = None
        cfg.key_response = None

        while pygame.time.get_ticks() - interval_t0 < duration:
            state = event_handler.poll()
            saves.log_joy_frame(pygame.time.get_ticks(), "interval_practice", state.x_raw, state.y_raw, "")

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _show_centered_image(screen, stim_path)
                pygame.display.flip()
                stim_t0 = pygame.time.get_ticks()
                saves.log_joy_frame(stim_t0, "interval_practice", 0.0, 0.0, "stim_onset")
                _flush_input()

            if cfg.joy_response is not None:
                saves.log_joy_frame(pygame.time.get_ticks(), "interval_practice", state.x_raw, state.y_raw, "response_registered")
                selected_dir = cfg.joy_response
                correct_dir = cfg.expected_dir_for_color(color)
                result = 1 if selected_dir == correct_dir else 0
                rt = pygame.time.get_ticks() - stim_t0

                total_cnt += 1
                if result == 1:
                    correct_cnt += 1

                update_save(
                    "interval_practice",
                    "practice",
                    f"{word}_in_{color}",
                    correct_dir,
                    "",
                    correct_dir,
                    selected_dir or "",
                    result,
                    int(rt),
                    str(stim_path),
                    word=word,
                    ink=color,
                    interval_index=interval_idx + 1,
                    trial_in_interval=total_cnt,
                )

                # next stimulus (avoid same word and same color)
                prev_pair = (word, color)
                word, color, stim_path = _next_stroop_pair(prev_pair)
                _show_isi(screen)
                _show_centered_image(screen, stim_path)
                pygame.display.flip()
                stim_t0 = pygame.time.get_ticks()
                saves.log_joy_frame(stim_t0, "interval_practice", 0.0, 0.0, "stim_onset")
                _flush_input()
                cfg.joy_response = None
                cfg.key_response = None

            pygame.time.delay(1)

        # interval feedback screen
        _show_interval_feedback(
            screen,
            correct_cnt,
            total_cnt,
            None,
            is_last=(interval_idx == total_intervals - 1),
        )
        pygame.time.delay(int(cfg.FB_SCREEN_DURATION))
        _flush_input()

    saves.flush_joy_buffer()
    finalize_block_end_time()
    return screen
