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
from utils.event_handler import EventHandler
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
        (cfg.SCREEN_W, cfg.SCREEN_H), flags, vsync=1
    )
    pygame.display.set_caption("CCS")
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
    screen = pygame.display.set_mode(
        (cfg.SCREEN_W, cfg.SCREEN_H), flags, vsync=1
    )
    pygame.display.set_caption("CCS")

    if cfg._is_fullscreen:
        logger.info(f"[toggle_full_screen] Entered fullscreen")
    else:
        logger.info(f"[toggle_full_screen] Quitted fullscreen: {cfg.SCREEN_W} x {cfg.SCREEN_H}")
        
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
    """
    Show one admin page and return a copied background for overlay rendering.
    """
    place_image(screen=screen, img_path=img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    pygame.event.clear()
    return screen.copy()


def _wait_for_left_or_right(
    screen: pygame.Surface,
    img_path: Path,
) -> tuple[pygame.Surface, str]:
    """
    Show an admin page and wait until L(left) or R(right) is pressed.
    """
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

        if state.is_left:
            return screen, "left"

        if state.is_right:
            return screen, "right"

        pygame.time.delay(10)


def _wait_for_key_raw_pygame(
    screen: pygame.Surface,
    img_path: Path,
    target_key: int,
) -> pygame.Surface:
    """
    Wait until target key is pressed on the current admin page.
    """
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


def get_participant_id(screen: pygame.Surface) -> pygame.Surface:
    """
    Display Admin page and collect participant ID, then run Admin phase.
    """
    font = pygame.font.SysFont(None, cfg.FONT_SMALL)
    input_text = ""
    event_handler = EventHandler()
    admin_bg = _play_admin_image(screen, paths.Admin)

    while True:
        screen.blit(admin_bg, (0, 0))
        _render_centered_text(screen, font, input_text, screen.get_rect().centery + 20, cfg.COCO_RGB)

        pygame.display.flip()

        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            admin_bg = _play_admin_image(screen, paths.Admin)

        elif state.confirm and input_text.strip():
            cfg.PID = input_text.strip()
            _compute_mapping()
            from pathlib import Path as _P
            # Flip to Admin_Next and enter Admin phases
            _play_admin_image(screen, paths.Admin_Next)
            screen = _run_admin_phase(screen)
            return screen

        elif state.backspace:
            input_text = input_text[:-1]

        elif state.text_input:
            input_text += "".join(ch for ch in state.text_input if ch.isprintable())


def _compute_mapping():
    """Set MAPPING from PID suffix (odd->1 / even->2). Default to 1 for non-numeric PID."""
    try:
        pid_int = int(cfg.PID[-1])
    except (TypeError, ValueError):
        logger.warning(f"Invalid PID suffix for mapping: {cfg.PID!r}. Fallback MAPPING=1.")
        cfg.MAPPING = 1
        return

    cfg.MAPPING = 1 if (pid_int % 2 == 1) else 2


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
    - Clears the screen with cfg.BLACK_RGB to avoid black borders.
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
    - If False, fills the screen with cfg.BLACK_RGB before blitting (default behavior).

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

    # Default parameters
    if center is None:
        center = (screen_w / 2, screen_h / 2)

    # Validate parameter shape
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

    # Resolve resize target
    if resize is None:
        # Scale while preserving aspect ratio.
        # - cover: fill the screen (may crop)
        # - contain: fit fully inside screen (no crop)
        img_w, img_h = img.get_size()
        if fit_mode == "contain":
            scale = min(screen_w * max_fraction / img_w, screen_h * max_fraction / img_h)
        else:
            scale = max(screen_w * max_fraction / img_w, screen_h * max_fraction / img_h)
        target_w = int(img_w * scale)
        target_h = int(img_h * scale)
    else:
        if len(resize) != 2:
            logger.error("[place_image] Invalid input: 'resize' must be a 2-element tuple.")
            return
        target_w, target_h = resize
        try:
            target_w = int(target_w)
            target_h = int(target_h)
        except (TypeError, ValueError):
            logger.error(f"[place_image] Invalid input: 'resize' must be numeric: resize={resize}")
            return
        if target_w <= 0 or target_h <= 0:
            logger.error(f"[place_image] Invalid input: 'resize' must be positive: resize=({target_w}, {target_h})")
            return

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
    center = (screen_w / 2, screen_h * 0.68)

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
        font = pygame.font.SysFont(None, cfg.FONT_SMALL)
        text_surf = font.render("Timeout!", True, cfg.YELLOW_RGB)
        text_rect = text_surf.get_rect(center=center)
        screen.blit(text_surf, text_rect)
        return

    logger.error(f"[show_feedback] Invalid status: {status}")


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
    pass

def _get_admin_asset(name: str) -> Path:
    try:
        return getattr(paths, name)
    except AttributeError:
        logger.error(f"[admin] Missing admin asset: {name}")
        raise


def _run_admin_phase(screen: pygame.Surface) -> pygame.Surface:
    """
    New Admin phase: Group -> Session -> DH -> HU, using Admin_* assets.
    Keys: 1-6 for numbers, L/R for hands, Enter to confirm, Space to continue on Please page.
    """
    # Stage 0: show Admin_Next
    current_name = 'Admin_Next'
    _play_admin_image(screen, _get_admin_asset(current_name))

    # Utility: map key to digit string '1'..'6'
    digit_map = {
        pygame.K_1: '1', pygame.K_2: '2', pygame.K_3: '3',
        pygame.K_4: '4', pygame.K_5: '5', pygame.K_6: '6',
    }

    # ---------- Stage 1: GROUP ----------
    cfg.GROUP = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key in digit_map:
                cfg.GROUP = digit_map[event.key]
                current_name = f"Admin_{cfg.GROUP}"
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key == pygame.K_RETURN:
                if not cfg.GROUP:
                    logger.warning("[admin] Enter pressed before selecting group.")
                    continue
                current_name = f"Admin_{cfg.GROUP}_Next"
                _play_admin_image(screen, _get_admin_asset(current_name))
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # ---------- Stage 2: SESSION ----------
    cfg.SESSION = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key in digit_map:
                cfg.SESSION = digit_map[event.key]
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}"
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key == pygame.K_RETURN:
                if not cfg.SESSION:
                    logger.warning("[admin] Enter pressed before selecting session.")
                    continue
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_Next"
                _play_admin_image(screen, _get_admin_asset(current_name))
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # ---------- Stage 3: DH (dominant hand) ----------
    cfg.DH = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key == pygame.K_l:
                cfg.DH = 'left'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_L"
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key == pygame.K_r:
                cfg.DH = 'right'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_R"
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key == pygame.K_RETURN:
                if not cfg.DH:
                    logger.warning("[admin] Enter pressed before selecting DH.")
                    continue
                suffix = 'L' if cfg.DH == 'left' else 'R'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{suffix}_Next"
                _play_admin_image(screen, _get_admin_asset(current_name))
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # ---------- Stage 4: HU (hand used) ----------
    cfg.UH = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key == pygame.K_l:
                cfg.UH = 'left'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{'L' if cfg.DH=='left' else 'R'}_L"
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key == pygame.K_r:
                cfg.UH = 'right'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{'L' if cfg.DH=='left' else 'R'}_R"
                _play_admin_image(screen, _get_admin_asset(current_name))
                continue
            if event.key == pygame.K_RETURN:
                if not cfg.UH:
                    logger.warning("[admin] Enter pressed before selecting HU.")
                    continue
                please = 'Admin_Please_L' if cfg.UH == 'left' else 'Admin_Please_R'
                _play_admin_image(screen, _get_admin_asset(please))
                screen = _wait_for_key_raw_pygame(screen, _get_admin_asset(please), pygame.K_SPACE)
                return screen
        else:
            pygame.time.delay(10)
            continue
        # no break here; continue loop until return

    return screen