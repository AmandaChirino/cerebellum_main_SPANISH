# ./src/core/practice.py
"""
Practice block execution logic using pygame.

For each trial: show fixation cross, then play the video while tracking mouse
coordinates every frame via a slider overlay. No post-video response is collected.
"""


from __future__ import annotations
from pathlib import Path
import pygame
import random
import datetime

import utils.paths as path
import utils.config as cfg
from utils.logger import get_logger

from utils.event_handler import EventHandler
from core.mouseCordDot import MouseCordDot
from core.saves import update_save
from core.stimulus import(
    play_video,
    place_stim_img
)


logger = get_logger("./src/core/practice")


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def run_practice(
    screen: pygame.Surface,
    block: str,
    stimuli: list[Path],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run a practice block: each video in stimuli exactly once, randomized order.

    For each trial:
    - Show fixation cross for cfg.FIXATION_CROSS ms
    - Play the video frame-by-frame with a slider overlay
    - Track mouse x position every frame via MouseCordDot
    - Log per-frame coordinates; save one trial-level row at the end

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param block: Name of the block
    :type block: str

    :param stimuli: List of practice video paths
    :type stimuli: list[pathlib.Path]

    :param event_handler: Centralized event handler instance
    :type event_handler: EventHandler

    :return: Active display surface after the block (may be updated by fullscreen toggle)
    :rtype: pygame.Surface
    """
    
    shuffled = random.sample(stimuli, k=len(stimuli))

    for video_path in shuffled:
        starting = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Fixation cross
        screen.fill(cfg.BLACK_RGB)
        pygame.display.flip()
        _flush_input()
        pygame.time.delay(cfg.FIXATION_CROSS)

        mouse_cord_dot = MouseCordDot(screen)
        mouse_cord_dot.set_pos((0, 0))  # start slider at center
        pygame.mouse.set_visible(False)

        screen, x_pos, y_pos, ms, playback = play_video(
            screen,
            str(video_path),
            mouse_cord_dot=mouse_cord_dot,
            event_handler=event_handler,
            block=block,
            video_name=video_path.name,
            logger=logger,
        )

        _flush_input()

        # Trial-level save
        logger.info("TRIAL_END | block=%s | video=%s", block, video_path)

        update_save (
            block="practice",
            type="practice",
            starttime=starting,
            endtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            correct=1,
            #condition=find_condition(video_path),
            x_pos=x_pos,
            y_pos=y_pos,
            frame_from_time=ms,
            stimulus_path=video_path.name,
            key_corr= "NA", #(correct_response if not joystick_present else "NA"),
            key_resp= "NA", #key_resp,
            joy_corr= "NA", #(joy_correct_response if joystick_present else "NA"),
            joy_resp= "NA", #joy_resp,
            playback=playback,
        )
    return screen
