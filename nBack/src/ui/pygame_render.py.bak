# ./src/core/pygame_render.py
"""
Pygame setup utilities.

This module initializes the Pygame display, manages fullscreen toggling, renders basic text elements, and collects PID and MAPPING.
"""


from __future__ import annotations
from typing import Tuple, Optional
import pygame
from pathlib import Path

import utils.config as cfg
import utils.paths as paths
from utils.logger import get_logger


logger = get_logger("./src/ui/pygame_render")


def init_display() -> pygame.Surface:
    """
    Initialize the pygame display window.

    :return: Initialized pygame display surface
    :rtype: pygame.Surface
    """

    flags = pygame.FULLSCREEN if cfg._is_fullscreen else 0
    screen = pygame.display.set_mode(
        (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), flags, vsync=1
    )
    pygame.display.set_caption("Nback")
    return screen


def toggle_full_screen(screen: pygame.Surface) -> pygame.Surface:
    """
    Toggle between full-screen and windowed display modes.
    
    :param screen: Current pygame display surface
    :type screen: pygame.Surface

    :return: New pygame display surface after toggling fullscreen state (window -> fullscreen; fullscreen -> window)
    :rtype: pygame.Surface
    """

    cfg._is_fullscreen = not cfg._is_fullscreen
    flags = pygame.FULLSCREEN if cfg._is_fullscreen else 0

    # Reset display mode (recommended way in Pygame to toggle fullscreen)
    screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), flags, vsync=1)

    if cfg._is_fullscreen:
        logger.info(f"[toggle_full_screen] Entered fullscreen")
    else:
        logger.info(f"[toggle_full_screen] Quitted fullscreen: {cfg.SCREEN_WIDTH} x {cfg.SCREEN_HEIGHT}")
        
    return screen


def _render_centered_text(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str, y: int,
    color: Tuple[int, int, int]
) -> None:
    """
    Render a single line of text horizontally centered on the screen.
    
    :param screen: Target pygame display surface
    :type screen: pygame.Surface

    :param font: Font used to render the text
    :type font: pygame.font.Font

    :param text: Text string to be rendered
    :type text: str

    :param y: Vertical pixel coordinate for the text center
    :type y: int

    :param color: RGB color tuple used to render the text
    :type color: Tuple[int, int, int]
    """

    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(screen.get_rect().centerx, y))
    screen.blit(surf, rect.topleft)


def _play_admin_image(screen: pygame.Surface, img_path: Path) -> pygame.Surface:
    """Show one admin page and return a static snapshot surface."""
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    pygame.event.clear()
    return screen.copy()


def _wait_for_left_or_right(
    screen: pygame.Surface,
    img_path: Path,
) -> tuple[pygame.Surface, str]:
    """Show admin image and wait until left(L) or right(R) is selected."""
    from utils.event_handler import EventHandler

    event_handler = EventHandler()
    admin_bg = _play_admin_image(screen, img_path)

    while True:
        screen.blit(admin_bg, (0, 0))
        pygame.display.flip()

        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            admin_bg = _play_admin_image(screen, img_path)
            continue

        if state.mapping_1:
            return screen, "left"

        if state.mapping_2:
            return screen, "right"

        pygame.time.delay(10)


def _wait_for_key_raw_pygame(
    screen: pygame.Surface,
    img_path: Path,
    target_key: int,
) -> pygame.Surface:
    """Wait until target key is pressed using raw pygame events."""
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _play_admin_image(screen, img_path)
                continue

            if event.key == target_key:
                return screen

        pygame.time.delay(10)


def _await_one_of_keys(screen: pygame.Surface, img_path: Path, valid_keys: list[int]) -> int:
    """Show img_path and wait until one of valid_keys is pressed. Returns the key code."""
    _play_admin_image(screen, img_path)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _play_admin_image(screen, img_path)
                continue
            if event.key in valid_keys:
                return event.key
        pygame.time.delay(10)


def record_language_group_session(screen: pygame.Surface) -> pygame.Surface:
    """Handle Language → Group → Session admin screens and store values to cfg."""
    # Language
    lang_key = _await_one_of_keys(screen, paths.ADMIN_LAN, [pygame.K_1, pygame.K_2])
    if lang_key == pygame.K_1:
        cfg.LANGUAGE = "spanish"
        _play_admin_image(screen, paths.ADMIN_LAN_SPANISH)
        screen = _wait_for_key_raw_pygame(screen, paths.ADMIN_LAN_SPANISH, pygame.K_RETURN)
    else:
        cfg.LANGUAGE = "english"
        _play_admin_image(screen, paths.ADMIN_LAN_ENGLISH)
        screen = _wait_for_key_raw_pygame(screen, paths.ADMIN_LAN_ENGLISH, pygame.K_RETURN)
    # Group
    grp_map = {
        pygame.K_1: ("pilot",   paths.ADMIN_GRP_1),
        pygame.K_2: ("control", paths.ADMIN_GRP_2),
        pygame.K_3: ("cd",      paths.ADMIN_GRP_3),
        pygame.K_4: ("stroke",  paths.ADMIN_GRP_4),
        pygame.K_5: ("tumor",   paths.ADMIN_GRP_5),
        pygame.K_6: ("other",   paths.ADMIN_GRP_6),
    }
    grp_key = _await_one_of_keys(screen, paths.ADMIN_GRP, list(grp_map))
    cfg.GROUP, grp_confirm = grp_map[grp_key]
    _play_admin_image(screen, grp_confirm)
    screen = _wait_for_key_raw_pygame(screen, grp_confirm, pygame.K_RETURN)
    # Session
    ses_map = {
        pygame.K_1: ("s1", paths.ADMIN_SESSION_1),
        pygame.K_2: ("s2", paths.ADMIN_SESSION_2),
        pygame.K_3: ("s3", paths.ADMIN_SESSION_3),
        pygame.K_4: ("s4", paths.ADMIN_SESSION_4),
        pygame.K_5: ("s5", paths.ADMIN_SESSION_5),
        pygame.K_6: ("s6", paths.ADMIN_SESSION_6),
        pygame.K_7: ("s7", paths.ADMIN_SESSION_7),
        pygame.K_8: ("s8", paths.ADMIN_SESSION_8),
        pygame.K_9: ("s9", paths.ADMIN_SESSION_9),
    }
    ses_key = _await_one_of_keys(screen, paths.ADMIN_SESSION, list(ses_map))
    cfg.SESSION, ses_confirm = ses_map[ses_key]
    _play_admin_image(screen, ses_confirm)
    screen = _wait_for_key_raw_pygame(screen, ses_confirm, pygame.K_RETURN)
    return screen


def get_participant_id(screen: pygame.Surface) -> pygame.Surface:
    """
    Show ADMIN_1 and collect participant ID from keyboard input.
    """
    font = pygame.font.SysFont(None, cfg.FONT_SIZE)
    input_text = ""
    admin_bg = _play_admin_image(screen, paths.ADMIN_1)

    while True:
        screen.blit(admin_bg, (0, 0))
        _render_centered_text(
            screen,
            font,
            input_text,
            screen.get_rect().centery + 20,
            cfg.SILVER_RGB,
        )

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                admin_bg = _play_admin_image(screen, paths.ADMIN_1)
                continue

            if event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
                continue

            if event.key == pygame.K_RETURN:
                if input_text.strip():
                    cfg.PID = input_text.strip()
                    screen = record_language_group_session(screen)
                    return screen
                continue

            if event.unicode:
                input_text += "".join(ch for ch in event.unicode if ch.isprintable())

        pygame.time.delay(10)


def record_hands(screen: pygame.Surface) -> pygame.Surface:
    """
    Play admin pages and record dominant hand + hand used.
    """
    screen, dominant_hand = _wait_for_left_or_right(screen, paths.ADMIN_2)
    cfg.dominant_hand = dominant_hand

    if dominant_hand == "left":
        screen, hand_used = _wait_for_left_or_right(screen, paths.ADMIN_L)
        cfg.hand_used = hand_used

        if hand_used == "left":
            confirm_img = paths.ADMIN_LL
            please_img = paths.ADMIN_PLEASE_L
        else:
            confirm_img = paths.ADMIN_LR
            please_img = paths.ADMIN_PLEASE_R
    else:
        screen, hand_used = _wait_for_left_or_right(screen, paths.ADMIN_R)
        cfg.hand_used = hand_used

        if hand_used == "left":
            confirm_img = paths.ADMIN_RL
            please_img = paths.ADMIN_PLEASE_L
        else:
            confirm_img = paths.ADMIN_RR
            please_img = paths.ADMIN_PLEASE_R

    _play_admin_image(screen, confirm_img)
    screen = _wait_for_key_raw_pygame(screen, confirm_img, pygame.K_RETURN)

    _play_admin_image(screen, please_img)
    screen = _wait_for_key_raw_pygame(screen, please_img, pygame.K_SPACE)

    return screen


def place_image(
    screen: pygame.Surface,
    img_path: Path,
    center: Optional[Tuple[float, float]] = None,
    resize: Optional[Tuple[int, int]] = None,
    overlay: bool = False,
    fit_mode: str = "cover",
    max_fraction: float = 1.0,
) -> None:
    """
    Load an image from disk, resize it, and blit it onto the screen at a given center position.

    The function:
    - Loads an image with alpha channel support.
    - Resizes the image to the target size.
    - Clears the screen with cfg.GRAY_RGB to avoid black borders.
    - Places the image centered at the target location.

    Parameter rules:
    - center:
        - If None, defaults to the screen center.
        - Must be a 2-tuple (x, y) within screen bounds.
    - resize:
        - If None, defaults to the screen size.
        - Must be a 2-tuple (width, height) with positive values.

    Visual settings (overlay:
    - If True, blits onto the existing screen content (overlay mode).
    - If False, fills the screen with cfg.GRAY_RGB before blitting (default behavior).

    :param screen: Active pygame display surface
    :type screen: pygame.Surface

    :param img_path: Path to the image file
    :type img_path: Path

    :param center: Center position (x, y) for placing the image
    :type center: Optional[Tuple[float, float]]

    :param resize: Target resize size (width, height)
    :type resize: Optional[Tuple[int, int]]

    :param overlay: Activate overlay mode (default = False)
    :type overlay: bool

    :return: None
    """

    # Get screen geometry
    screen_w, screen_h = screen.get_size()

    # Default center
    if center is None:
        center = (screen_w / 2, screen_h / 2)

    # Validate center shape
    if len(center) != 2:
        logger.error("[place_image] Invalid input: 'center' must be a 2-element tuple.")
        return

    target_cx, target_cy = center

    # Validate center range
    if not (0 <= target_cx <= screen_w and 0 <= target_cy <= screen_h):
        logger.error(
            f"[place_image] Invalid input: 'center' out of bounds: center={center}, screen=({screen_w}, {screen_h})"
        )
        return

    # Validate explicit resize
    if resize is not None:
        if len(resize) != 2:
            logger.error("[place_image] Invalid input: 'resize' must be a 2-element tuple.")
            return
        try:
            target_w = int(resize[0])
            target_h = int(resize[1])
        except (TypeError, ValueError):
            logger.error(f"[place_image] Invalid input: 'resize' must be numeric: resize={resize}")
            return
        if target_w <= 0 or target_h <= 0:
            logger.error(f"[place_image] Invalid input: 'resize' must be positive: resize=({target_w}, {target_h})")
            return

    # Check image file existence
    if not img_path.exists():
        logger.error(f"[place_image] Image file not found -> {img_path}")
        return

    # Load image with alpha support
    try:
        img = pygame.image.load(str(img_path)).convert_alpha()
    except Exception as e:
        logger.error(f"[place_image] Failed to load image -> {img_path} | {e}")
        return

    # Compute resize target
    if resize is None:
        img_w, img_h = img.get_size()
        max_w = screen_w * max_fraction
        max_h = screen_h * max_fraction
        if fit_mode == "contain":
            scale = min(max_w / img_w, max_h / img_h)
        else:
            scale = max(max_w / img_w, max_h / img_h)
        target_w = int(img_w * scale)
        target_h = int(img_h * scale)

    # Resize image
    img = pygame.transform.smoothscale(img, (target_w, target_h))

    # Activate overlay mode
    if not overlay:
        screen.fill(cfg.BLACK_RGB)

    # Blit image at target center
    img_rect = img.get_rect(center=(target_cx, target_cy))
    screen.blit(img, img_rect)


def show_feedback(screen: pygame.Surface, status: str) -> None:
    """
    Show feedback based on response status.

    Feedback is rendered as an overlay on the current stimulus screen

    Parameter rules:
    - status:
        - "correct": show cfg.FB_CORRECT image centered in the lower-middle area
        - "incorrect": show cfg.FB_INCORRECT image centered in the lower-middle area
        - "timeout": show yellow "Timeout!" text centered in the lower-middle area

    Visual settings:
    - Image resize: cfg.FB_W x cfg.FB_H
    - Timeout text color: cfg.YELLOW_RGB

    :param screen: Active pygame display surface
    :type screen: pygame.Surface

    :param status: Feedback status string ("correct", "incorrect", "timeout")
    :type status: str

    :return: None
    """
    screen_w, screen_h = screen.get_size()
    # Lower-middle placement (centered, slightly below midline)
    center = (screen_w / 2, screen_h * 0.62)

    if status == "correct":
        place_image(
            screen=screen,
            img_path=Path(paths.FB_CORRECT),
            center=center,
            resize=(cfg.FB_W, cfg.FB_H),
            overlay=True,
        )
        return

    if status == "incorrect":
        place_image(
            screen=screen,
            img_path=Path(paths.FB_INCORRECT),
            center=center,
            resize=(cfg.FB_W, cfg.FB_H),
            overlay=True,
        )
        return

    if status == "timeout":
        font = pygame.font.SysFont(None, cfg.FONT_SIZE)
        text_surf = font.render("Timeout!", True, cfg.YELLOW_RGB)
        text_rect = text_surf.get_rect(center=center)
        screen.blit(text_surf, text_rect)
        return

    logger.error(f"[show_feedback] Invalid status: {status}")


def draw_fixation_cross(screen: pygame.Surface) -> None:
    """
    Draw a fixation cross at the center of the screen.
    
    :param screen: Active pygame display surface
    :type screen: pygame.Surface
    
    :return: None
    """
    screen_w, screen_h = screen.get_size()
    center_x, center_y = screen_w // 2, screen_h // 2
    
    # Cross size from config
    cross_size = cfg.CROSS_SIZE
    half_size = cross_size // 2
    
    # Line thickness: thicker for better visibility
    line_width = 4
    
    # Draw horizontal line
    pygame.draw.line(
        screen,
        cfg.WHITE_RGB,
        (center_x - half_size, center_y),
        (center_x + half_size, center_y),
        line_width
    )
    
    # Draw vertical line
    pygame.draw.line(
        screen,
        cfg.WHITE_RGB,
        (center_x, center_y - half_size),
        (center_x, center_y + half_size),
        line_width
    )


def show_feedback_timed(screen: pygame.Surface, status: str, max_duration_ms: int, background_surface: pygame.Surface = None) -> None:
    """
    Display feedback overlay for a controlled duration with optional background preservation.

    Args:
        screen: pygame display surface to draw onto.
        status: feedback type ("correct", "incorrect", "timeout").
        max_duration_ms: maximum duration to show feedback in milliseconds.
        background_surface: optional surface to maintain as background during feedback display.

    Behavior:
        - Renders feedback overlay on top of current screen contents or provided background.
        - Maintains display for exactly max_duration_ms with continuous event polling.
        - Returns immediately after duration expires, allowing precise timing control.
        - If background_surface is provided, redraws it periodically to maintain consistency.
    """
    screen_w, screen_h = screen.get_size()
    center = (screen_w / 2, screen_h * 0.64)

    # Prepare feedback surface
    if status == "correct":
        feedback_img = pygame.image.load(str(paths.FB_CORRECT)).convert_alpha()
        feedback_surface = pygame.transform.smoothscale(feedback_img, (cfg.FB_W, cfg.FB_H))
        feedback_rect = feedback_surface.get_rect(center=center)
    elif status == "incorrect":
        feedback_img = pygame.image.load(str(paths.FB_INCORRECT)).convert_alpha()
        feedback_surface = pygame.transform.smoothscale(feedback_img, (cfg.FB_W, cfg.FB_H))
        feedback_rect = feedback_surface.get_rect(center=center)
    elif status == "timeout":
        font = pygame.font.SysFont(None, cfg.FONT_SIZE)
        feedback_surface = font.render("Timeout!", True, cfg.YELLOW_RGB)
        feedback_rect = feedback_surface.get_rect(center=center)
    else:
        logger.error(f"[show_feedback_timed] Invalid status: {status}")
        return

    start_time = pygame.time.get_ticks()
    
    # Display feedback with timing control
    while (pygame.time.get_ticks() - start_time) < max_duration_ms:
        # Redraw background if provided to maintain visual consistency
        if background_surface:
            screen.blit(background_surface, (0, 0))
        
        # Overlay feedback on current screen contents
        screen.blit(feedback_surface, feedback_rect)
        pygame.display.flip()
        
        # Handle any pending events to maintain system responsiveness
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
        
        # Brief delay to prevent excessive CPU usage
        pygame.time.delay(5)


# Cache for beep sound (lazy init)
_BEEP_SOUND: pygame.mixer.Sound | None = None

def _play_beep() -> None:
    """
    Play the response beep sound once (non-blocking).

    :return: None
    """
    # global _BEEP_SOUND

    # # Ensure mixer is ready (won't re-init if already initialized)
    # if not pygame.mixer.get_init():
    #     pygame.mixer.init()

    # if _BEEP_SOUND is None:
    #     _BEEP_SOUND = pygame.mixer.Sound(str(BEEP))

    # _BEEP_SOUND.play()

    return None
