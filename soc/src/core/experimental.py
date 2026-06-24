# ./src/core/experimental.py
"""
Experimental block execution for the soccer prediction task.

Presents 60 pre-sequenced video trials per block, collects left/right
responses, and logs results. No feedback is shown to participants.
"""

from __future__ import annotations
import datetime
import pygame

import utils.config as cfg
import utils.paths as paths
from utils.logger import get_logger
from utils.event_handler import EventHandler
from ui.pygame_render import toggle_full_screen, place_image, draw_direction_hints
from ui.video import play_video, show_frozen_frame
from core.saves import update_save, update_joystick_log

logger = get_logger("./src/core/experimental")


def _flush_input() -> None:
    pygame.event.clear()


def _show_fixation(screen: pygame.Surface) -> None:
    sw, sh = screen.get_size()
    frac = cfg.FIXATION_CROSS_SIZE / min(sw, sh)
    place_image(screen, paths.FIXATION_CROSS, fit_mode="contain", max_fraction=frac)
    draw_direction_hints(screen)
    pygame.display.flip()


def run_block(
    screen: pygame.Surface,
    block_label: str,
    trials: list[dict],
    event_handler: EventHandler,
) -> tuple[pygame.Surface, str, str]:
    """
    Run one experimental block (no feedback).

    Each trial:
        fixation → video → frozen frame + guide overlay → response → save

    :param screen: Active pygame display surface.
    :param block_label: Block identifier written to results CSV (e.g. 'b1').
    :param trials: Trial dicts from build_trials() filtered to the target block number.
    :param event_handler: Centralized input handler.
    :return: (screen, accuracy_pct_str, avg_rt_sec_str)
    """
    curr_trials = 0
    acc_counter = 0
    sum_rt = 0
    rt_count = 0
    joystick_present = pygame.joystick.get_count() > 0
    accuracy_str = "0.00"

    for trial in trials:
        filename = f"{trial['video_name']}.mp4"
        video_path = paths.VIDEOS / filename
        correct_direction = trial['condition']  # 'left' or 'right'

        # Fixation
        _show_fixation(screen)
        _flush_input()
        pygame.time.delay(cfg.FIXATION_CROSS)
        # Ignore any key/joystick activity performed during fixation.
        _flush_input()

        starting = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Response window starts at first visible video frame and lasts up to 3s total.
        first_visible_tick: int | None = None
        response_deadline: int | None = None
        response: str | None = None
        correct = 0
        rt: int | None = None
        response_emitted = False

        def _poll_and_capture(current_screen: pygame.Surface) -> tuple[pygame.Surface, bool]:
            nonlocal first_visible_tick, response_deadline, response, correct, rt, response_emitted

            state = event_handler.poll()
            import math as _math
            _ax = event_handler.last_axis_x
            _ay = event_handler.last_axis_y
            if abs(_ax) < cfg.DZ_X and abs(_ay) < cfg.DZ_Y:
                _ang = 0.0
                _dir = "rest"
            else:
                _ang = (_math.degrees(_math.atan2(_ax, -_ay)) + 360) % 360
                _dir = "left" if 180 <= _ang < 360 else "right"
            if hasattr(cfg, 'JOY_LOG_FILE') and cfg.JOY_LOG_FILE:
                update_joystick_log(
                    block=block_label,
                    block_type="experimental",
                    trial=curr_trials + 1,
                    timestamp_ms=pygame.time.get_ticks(),
                    axis_x=_ax, axis_y=_ay, angle=_ang, direction=_dir,
                    video_name=trial['video_name'],
                )

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                current_screen = toggle_full_screen(current_screen)
                pygame.event.clear()

            if first_visible_tick is None:
                first_visible_tick = pygame.time.get_ticks()
                response_deadline = first_visible_tick + cfg.MAX_RESPOND_TIME

            if response is None and first_visible_tick is not None:
                elapsed = min(pygame.time.get_ticks() - first_visible_tick, cfg.MAX_RESPOND_TIME)
                if state.option_1:
                    response = "left"
                    correct = 1 if correct_direction == "left" else 0
                    rt = elapsed
                    response_emitted = True
                elif state.option_2:
                    response = "right"
                    correct = 1 if correct_direction == "right" else 0
                    rt = elapsed
                    response_emitted = True

            return current_screen, not response_emitted

        # Play the full video until a response is emitted or EOF is reached.
        last_frame, screen = play_video(screen, video_path, on_frame=_poll_and_capture)

        # Fallback anchor if no video frame could be shown.
        if first_visible_tick is None:
            first_visible_tick = pygame.time.get_ticks()
            response_deadline = first_visible_tick + cfg.MAX_RESPOND_TIME

        # Freeze only if no response was emitted during the video.
        while response is None and response_deadline is not None and pygame.time.get_ticks() < response_deadline:
            show_frozen_frame(screen, last_frame)
            screen, keep_playing = _poll_and_capture(screen)
            pygame.time.delay(5)
            if not keep_playing:
                break

        _flush_input()
        acc_counter += correct
        if rt is not None:
            sum_rt += rt
            rt_count += 1
        curr_trials += 1
        accuracy_str = f"{(acc_counter / curr_trials) * 100:.2f}" if curr_trials > 0 else "0.00"

        # Format response columns for save
        if joystick_present:
            key_corr, key_resp = "NA", "NA"
            joy_corr = correct_direction
            joy_resp = response if response else "NA"
        else:
            key_corr = "d" if correct_direction == "left" else "k"
            key_resp = ("d" if response == "left" else "k") if response else "NA"
            joy_corr, joy_resp = "NA", "NA"

        update_save(
            block=block_label,
            type="experimental",
            starttime=starting,
            endtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            condition=trial['condition'],
            correct=correct,
            reaction_time=rt if response is not None else None,
            key_corr=key_corr,
            key_resp=key_resp,
            joy_corr=joy_corr,
            joy_resp=joy_resp,
            accuracy=accuracy_str,
            pathname=filename,
            difficulty=trial["difficulty"],
        )

        logger.info(
            "BLOCK | block=%s | video=%s | direction=%s | response=%s | correct=%s | rt=%s ms",
            block_label, trial['video_name'], correct_direction, response, correct, (rt if rt is not None else "NA"),
        )

    avg_rt_str = f"{(sum_rt / rt_count) / 1000:.2f}" if rt_count > 0 else "0.00"
    return screen, accuracy_str, avg_rt_str
