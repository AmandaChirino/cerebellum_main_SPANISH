from __future__ import annotations
import cv2
import pygame
import math
import time
import numpy as np
import re

import utils.config as cfg
import ui.pygame_render as render

# Slider geometry; fractions are relative to the screen height
SLIDER_BAR_THICKNESS = 20   # bar thickness in pixels
SLIDER_BAR_OPACITY = 0.3    # bar opacity while the participant is moving
SLIDER_IDLE_AFTER_S = 10.0  # seconds without mouse movement before the bar flashes
SLIDER_MARK_HEIGHT = 0.04   # height of the end/center marks
SLIDER_MARK_WIDTH = 20      # width of the end/center marks in pixels
SLIDER_DOT_DIAMETER = 0.025 # diameter of the tracker dot
SLIDER_DOT_BORDER = 2       # border of the tracker dot in pixels
SLIDER_LABEL_OFFSET = 0.08  # distance of the labels above the bar
SLIDER_FONT_SIZE = 0.04     # label font size
# Accepted range for playback_ratio (real duration / expected duration of the video)
PLAYBACK_RATIO_MIN = 0.95
PLAYBACK_RATIO_MAX = 1.05
# Seconds before each frame deadline where the wait switches from sleeping to checking the clock
FRAME_SPIN_MARGIN_S = 0.002
# Empty band in the base image (stim_instruction.png, 1600x900) where the stimulus image goes,
# as fractions of the base image height: below the instruction text, above "Press SPACE to continue."
STIM_AREA_TOP = 420 / 900
STIM_AREA_BOTTOM = 848 / 900
STIM_AREA_MAX_WIDTH = 0.8   # max stimulus width as a fraction of the screen width
STIM_AREA_PADDING = 25      # pixels of space kept between the stimulus image and the text
SLIDER_LABELS =("Negative emotion", "Neutral", "Positive emotion")

_label_font: pygame.font.Font | None = None
_label_font_size: int = 0


def _draw_slider(screen: pygame.Surface, x: float, idle_time: float = 0.0) -> None:
    """
    Draw a horizontal slider overlay in the middle of the screen.

    :param screen: Current display surface
    :param x: Normalised slider position in [-1, 1]
    :param idle_time: Seconds since the last mouse movement
    """
    global _label_font, _label_font_size

    w, h = screen.get_size()
    cx, cy = w // 2, h // 2
    half = cfg.SLIDER_HALF_LENGTH * h

    # Font is rebuilt only when the screen height changes the size
    font_size = int(SLIDER_FONT_SIZE * h)
    if _label_font is None or font_size != _label_font_size:
        _label_font = pygame.font.SysFont(None, font_size)
        _label_font_size = font_size

    # Bar opacity: constant while moving, oscillating once idle
    if idle_time > SLIDER_IDLE_AFTER_S:
        opacity = min(1.0, max(0.0, 0.5 * math.sin(idle_time * 10) + 0.5))
    else:
        opacity = SLIDER_BAR_OPACITY

    # Horizontal bar centered on the screen
    bar_w = int(2 * half)
    bar_surf = pygame.Surface((bar_w, SLIDER_BAR_THICKNESS), pygame.SRCALPHA)
    bar_surf.fill((*pygame.Color(cfg.COCO_RGB)[:3], int(255 * opacity)))
    screen.blit(bar_surf, bar_surf.get_rect(center=(cx, cy)))

    # Marks at both ends and at the center, with their labels above the bar
    mark_h = int(SLIDER_MARK_HEIGHT * h)
    label_y = cy - SLIDER_LABEL_OFFSET * h
    marker_xs = (cx - half, cx, cx + half)  # left, center, right
    for mx, label in zip(marker_xs, SLIDER_LABELS):
        mark_rect = pygame.Rect(0, 0, SLIDER_MARK_WIDTH, mark_h)
        mark_rect.center = (int(mx), cy)
        pygame.draw.rect(screen, cfg.COCO_RGB, mark_rect)

        # Two-word labels are split into two lines, the block centered on label_y
        lines = label.split() if len(label.split()) == 2 else [label]
        surfs = [_label_font.render(line, True, cfg.COCO_RGB) for line in lines]
        top = label_y - sum(s.get_height() for s in surfs) / 2
        for surf in surfs:
            screen.blit(surf, surf.get_rect(midtop=(int(mx), int(top))))
            top += surf.get_height()

    # Tracker dot follows the mouse position
    dot_x = int(cx + x * half)
    dot_r = int(SLIDER_DOT_DIAMETER * h / 2)
    pygame.draw.circle(screen, cfg.RED_RGB, (dot_x, cy), dot_r)
    pygame.draw.circle(screen, cfg.COCO_RGB, (dot_x, cy), dot_r, SLIDER_DOT_BORDER)

def find_condition(path: str) -> str:
    pattern = r'(stimuli/context)'
    match = re.search(pattern, path, re.IGNORECASE)
    if match:
        print(match.group().lower())
        return "context"
    else:
        return "baseline" 

def place_stim_img(screen: pygame.Surface, base_path: str, stim_path: str, event_handler=None) -> pygame.Surface:
    """
    Draw a base image over the whole screen, then the stimulus image on top of it
    in the bottom half of the screen.

    :param screen: Current display surface
    :param base_path: Path to the base (background) image, stretched to fill the screen
    :param stim_path: Path to the stimulus image, drawn at its original size (not scaled),
        centered in the bottom half of the screen
    :param event_handler: EventHandler instance for handling events
    """
    screen_rect = screen.get_rect()

    # Base image: fit within the screen without cropping (letterboxed/pillarboxed)
    render.place_image(screen, base_path, fit_mode="contain")

    # Find where the base image's empty band landed on screen. place_image scales the base
    # to contain within the screen (keeping aspect ratio) and centers it, so apply the same transform.
    base_w, base_h = pygame.image.load(str(base_path)).get_size()
    base_scale = min(screen_rect.width / base_w, screen_rect.height / base_h)
    base_top = (screen_rect.height - base_h * base_scale) / 2
    base_left = (screen_rect.width - base_w * base_scale) / 2
    area_top = base_top + STIM_AREA_TOP * base_h * base_scale + STIM_AREA_PADDING
    area_bottom = base_top + STIM_AREA_BOTTOM * base_h * base_scale - STIM_AREA_PADDING
    area_w = min(screen_rect.width * STIM_AREA_MAX_WIDTH, base_w * base_scale)
    area_h = area_bottom - area_top

    # Stimulus image: scaled to fit the band (aspect ratio kept), centered in it
    stim_img = pygame.image.load(str(stim_path)).convert_alpha()
    stim_scale = min(area_w / stim_img.get_width(), area_h / stim_img.get_height())
    stim_size = (int(stim_img.get_width() * stim_scale), int(stim_img.get_height() * stim_scale))
    stim_img = pygame.transform.smoothscale(stim_img, stim_size)
    stim_rect = stim_img.get_rect(center=(base_left + base_w * base_scale / 2, (area_top + area_bottom) / 2))
    screen.blit(stim_img, stim_rect)
    pygame.display.flip()

    return render._wait_for_next_page(screen, event_handler)

def _hide_cursor() -> None:
    """Hide the cursor; the visible/hidden toggle and the blank cursor cover cases where macOS shows it again."""
    pygame.mouse.set_visible(True)
    pygame.mouse.set_cursor((8, 8), (0, 0), (0,) * 8, (0,) * 8)
    pygame.mouse.set_visible(False)


def _wait_until(deadline: float) -> None:
    """Wait until time.perf_counter() reaches deadline: sleep first, then check the clock for the last moments."""
    sleep_s = deadline - time.perf_counter() - FRAME_SPIN_MARGIN_S
    if sleep_s > 0:
        time.sleep(sleep_s)
    while time.perf_counter() < deadline:
        pass


def play_video(
    screen: pygame.Surface,
    video_path: str,
    mouse_cord_dot=None,
    event_handler=None,
    block: str = "",
    video_name: str = "",
    logger=None,
) -> tuple[pygame.Surface, list, list, list, dict]:
    """
    Play a video file frame-by-frame with optional slider overlay and event handling.

    :param screen: Current display surface
    :param video_path: Path to the video file
    :param mouse_cord_dot: MouseCordDot instance for slider tracking (optional)
    :param event_handler: EventHandler for quit/fullscreen events (optional)
    :param block: Block name for per-frame logging (optional)
    :param video_name: Video filename for per-frame logging (optional)
    :param logger: Logger instance (optional)
    :return: Active display surface (may change on fullscreen toggle), x positions, y positions,
        frame numbers, and a playback dict (time_ms, n_samples, video_fps, video_frames_expected,
        duration_expected_s, duration_actual_s, playback_ratio)
    """
    from ui.pygame_render import toggle_full_screen

    capture = cv2.VideoCapture(video_path)
    fps = capture.get(cv2.CAP_PROP_FPS) or 60

    ms = []
    time_ms = []  # real milliseconds since the video started, one per sample
    x_pos = []
    y_pos = []
    _hide_cursor()
    if mouse_cord_dot is not None:
        mouse_cord_dot.set_pos((0.0, 0.0))
        pygame.event.clear(pygame.MOUSEMOTION)

    start_ticks = time.perf_counter()
    frame_num = 0
    frame_index = 0
    last_mouse_pos = pygame.mouse.get_pos()
    last_move_time = start_ticks

    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            break
        width, height = screen.get_size()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = np.rot90(frame_rgb)
        surface = pygame.surfarray.make_surface(frame_rgb)
        surface = pygame.transform.scale(surface, (int(width*.9), int(height*.9)))
        screen_rect = screen.get_rect()
        center_x, center_y = screen_rect.center
        surface_rect = surface.get_rect(center=(center_x, center_y))
        screen.blit(surface, surface_rect)

        x, y = 0.0, 0.0
        if mouse_cord_dot is not None:
            x, y = mouse_cord_dot.clamp(limit=1.0)
            mouse_pos = pygame.mouse.get_pos()
            now = time.perf_counter()
            if mouse_pos != last_mouse_pos:
                last_mouse_pos = mouse_pos
                last_move_time = now
            # The bar flashes once the mouse has been idle long enough
            idle_time = now - last_move_time
            _draw_slider(screen, x, idle_time=idle_time)

        pygame.display.flip()
        elapsed_time = time.perf_counter() - start_ticks
        frame_num = int(round(elapsed_time * fps))

        if logger is not None:
            logger.debug(
                "FRAME | block=%s | video=%s | ticks=%.3f | frame=%d | x=%.4f | y=%.4f",
                block,
                video_name,
                elapsed_time,
                frame_num,
                x,
                y,

            )
        x_pos = np.append(x_pos, x)
        y_pos = np.append(y_pos, y)
        ms = np.append(ms, frame_index)  # index of the frame shown, not estimated from the clock
        time_ms.append(elapsed_time * 1000)

        if event_handler is not None:
            state = event_handler.poll()
            if state.quit:
                capture.release()
                pygame.quit()
                raise SystemExit
            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                _hide_cursor()
                pygame.event.clear()
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    capture.release()
                    return screen
        # Frame i ends at start + (i + 1) / fps; a late frame makes the next ones wait less, no frame is skipped
        _wait_until(start_ticks + (frame_index + 1) / fps)
        frame_index += 1

    # Playback speed check: real duration against the duration the video should last
    duration_actual_s = time.perf_counter() - start_ticks
    video_fps = capture.get(cv2.CAP_PROP_FPS)
    video_frames_expected = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    capture.release()

    duration_expected_s = None
    playback_ratio = None
    if video_fps > 0 and video_frames_expected > 0:
        duration_expected_s = video_frames_expected / video_fps
        playback_ratio = duration_actual_s / duration_expected_s
        if logger is not None and not (PLAYBACK_RATIO_MIN <= playback_ratio <= PLAYBACK_RATIO_MAX):
            logger.warning(
                "PLAYBACK | video=%s | playback_ratio=%.3f outside %.2f-%.2f",
                video_name, playback_ratio, PLAYBACK_RATIO_MIN, PLAYBACK_RATIO_MAX,
            )

    playback = {
        "time_ms": time_ms,
        "n_samples": len(x_pos),
        "video_fps": video_fps or None,
        "video_frames_expected": video_frames_expected or None,
        "duration_expected_s": duration_expected_s,
        "duration_actual_s": duration_actual_s,
        "playback_ratio": playback_ratio,
    }
    return (screen, x_pos, y_pos, ms, playback)
