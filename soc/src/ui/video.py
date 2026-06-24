# ./src/ui/video.py
"""
Video playback and overlay utilities for the soccer prediction task.

Requires opencv-python:
    pip install opencv-python
"""

import pygame
from typing import Callable
import utils.config as cfg
import utils.paths as paths
from utils.logger import get_logger
from ui.pygame_render import draw_direction_hints

logger = get_logger("./src/ui/video")

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    _CV2_AVAILABLE = False
    logger.error("cv2 not found. Install with: pip install opencv-python")




def play_video(
    screen: pygame.Surface,
    video_path,
    on_frame: Callable[[pygame.Surface], tuple[pygame.Surface, bool]] | None = None,
) -> tuple[pygame.Surface | None, pygame.Surface]:
    """
    Play a full video file from frame 0 until EOF.

    Returns the last frame rendered as a Surface (already scaled to screen size),
    or None if playback could not start. The caller uses this to freeze-display
    the last frame during the response window. If provided, on_frame is called
    after each rendered frame and must return the updated screen surface plus a
    boolean indicating whether playback should continue.

    :param screen: Active pygame display surface.
    :param video_path: Path-like pointing to the .mp4 file.
    :param on_frame: Optional callback invoked after each rendered frame.
    :return: (last rendered frame or None, active screen surface)
    """
    if not _CV2_AVAILABLE:
        logger.error("Skipping video playback — cv2 not installed.")
        return None, screen

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error("Could not open video: %s", video_path)
        return None, screen

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_ms = int(1000 / fps)
    last_surf: pygame.Surface | None = None

    while cap.isOpened():
        t0 = pygame.time.get_ticks()
        ret, frame = cap.read()
        if not ret:
            break

        sw, sh = screen.get_size()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        fh, fw = frame_rgb.shape[:2]
        surf = pygame.image.frombuffer(frame_rgb.tobytes(), (fw, fh), 'RGB')
        surf = pygame.transform.scale(surf, (sw, sh))
        screen.blit(surf, (0, 0))
        draw_direction_hints(screen)
        pygame.display.flip()
        last_surf = surf

        if on_frame is not None:
            screen, keep_playing = on_frame(screen)
            if not keep_playing:
                break

        pygame.event.pump()

        elapsed = pygame.time.get_ticks() - t0
        pygame.time.delay(max(1, frame_ms - elapsed))

    cap.release()
    return last_surf, screen


def show_frozen_frame(
    screen: pygame.Surface,
    last_frame: pygame.Surface | None,
) -> None:
    """
    Blit the frozen video frame onto screen and flip.
    Falls back to black if last_frame is None.
    """
    if last_frame is not None:
        scaled = pygame.transform.scale(last_frame, screen.get_size())
        screen.blit(scaled, (0, 0))
    else:
        screen.fill(cfg.BLACK_RGB)
    draw_direction_hints(screen)
    pygame.display.flip()
