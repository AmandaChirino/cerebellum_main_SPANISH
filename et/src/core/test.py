# ./src/core/test.py
"""
Test block execution logic using pygame.

For each trial: show fixation cross, then play the video while tracking mouse
coordinates every frame via a slider overlay. No post-video response is collected.
"""


# TODO: Modify block design based on needs

from __future__ import annotations
from pathlib import Path
import pandas as pd
import pygame
import random
import re
import datetime

import utils.config as cfg
import utils.paths as path
from utils.logger import get_logger
from utils.paths import RESOURCES_DIR
from utils.event_handler import EventHandler
from core.mouseCordDot import MouseCordDot
from core.saves import update_save
from core.stimulus import(
    play_video,
    place_stim_img
)


logger = get_logger("./src/core/test")


def preview_image_path(video: str) -> Path:
    """Path of the image shown before a video: same name with .jpg, in the frames folder."""
    return path.BASELINE_IMG / re.sub(r'^stimuli/baseline/(.+)\.mp4$', r'\1.jpg', video)


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def run_test(
    screen: pygame.Surface,
    block: str,
    csv_path: Path,
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run a test block: each video in csv_path exactly once, randomized order.

    For each trial:
    - Show fixation cross for cfg.FIXATION_CROSS ms
    - Play the video frame-by-frame with a slider overlay
    - Track mouse x position every frame via MouseCordDot
    - Log per-frame coordinates; save one trial-level row at the end

    :param screen: Current display surface
    :type screen: pygame.Surface

    :param block: Name of the block
    :type block: str

    :param csv_path: Path to the stimPaths CSV (columns: video, pre_snapshot)
    :type csv_path: pathlib.Path

    :param event_handler: Centralized event handler instance
    :type event_handler: EventHandler

    :return: Active display surface after the block (may be updated by fullscreen toggle)
    :rtype: pygame.Surface
    """
    df = pd.read_csv(csv_path)
    video_list = df["video"].tolist()

    shuffled = random.sample(video_list, k=len(video_list))

    for video in shuffled:

        place_stim_img(screen, base_path=path.TEST_INSTRUCTIONS, stim_path=preview_image_path(video), event_handler=event_handler)

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
            str(RESOURCES_DIR / video),
            mouse_cord_dot=mouse_cord_dot,
            event_handler=event_handler,
            block=block,
            video_name=video,
            logger=logger,
        )

        _flush_input()

        # Trial-level save
        logger.info("TRIAL_END | block=%s | video=%s", block, video)

        update_save (
            block="test",
            type="experimental",
            starttime=starting,
            endtime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            correct=1,
            #condition=find_condition(video),
            x_pos=x_pos,
            y_pos=y_pos,
            frame_from_time=ms,
            stimulus_path=video,
            key_corr= "NA", #(correct_response if not joystick_present else "NA"),
            key_resp= "NA", #key_resp,
            joy_corr= "NA", #(joy_correct_response if joystick_present else "NA"),
            joy_resp= "NA", #joy_resp,
            playback=playback,
        )
    return screen
