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

    if cfg._is_fullscreen:
        screen_info = pygame.display.Info()
        cfg.SCREEN_W = screen_info.current_w
        cfg.SCREEN_H = screen_info.current_h
        screen = pygame.display.set_mode(
            (cfg.SCREEN_W, cfg.SCREEN_H), pygame.FULLSCREEN, vsync=1
        )
    else:
        screen = pygame.display.set_mode(
            (cfg.SCREEN_W, cfg.SCREEN_H), 0, vsync=1
        )
    pygame.display.set_caption("CCC")
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

    if cfg._is_fullscreen:
        screen_info = pygame.display.Info()
        cfg.SCREEN_W = screen_info.current_w
        cfg.SCREEN_H = screen_info.current_h
        screen = pygame.display.set_mode(
            (cfg.SCREEN_W, cfg.SCREEN_H), pygame.FULLSCREEN, vsync=1
        )
        logger.info(f"[toggle_full_screen] Entered fullscreen: {cfg.SCREEN_W} x {cfg.SCREEN_H}")
    else:
        screen = pygame.display.set_mode(
            (cfg.SCREEN_W, cfg.SCREEN_H), 0, vsync=1
        )
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
    Display Admin page and collect participant ID.

    After confirming with Enter, compute mapping and flip to Admin_next.
    """
    font = pygame.font.SysFont(None, cfg.FONT_SMALL)
    input_text = ""
    event_handler = EventHandler()
    admin_bg = _play_admin_image(screen, getattr(paths, "Admin"))

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
            admin_bg = _play_admin_image(screen, getattr(paths, "Admin"))

        elif state.confirm and input_text.strip():
            cfg.PID = input_text.strip()
            _compute_mapping()
            _play_admin_image(screen, getattr(paths, "Admin_Next"))
            pygame.display.flip()
            pygame.event.clear()
            return screen

        elif state.backspace:
            input_text = input_text[:-1]

        elif state.text_input:
            input_text += "".join(ch for ch in state.text_input if ch.isprintable())


def _compute_mapping():
    """
    Set MAPPING (1..8) from PID using the rule:
    - Extract the substring after the last '-' or '_' and try to parse it as an integer.
    - If it's an integer: mapping = n % 8 (with 0 mapped to 8).
    - If parsing fails: default mapping = 1.
    Examples:
      PID 'abc-17'  -> 17 % 8 = 1 => mapping 1
      PID 'abc17'   -> 17 % 8 = 1 => mapping 1
      PID 'foo_bar_8' -> 8 % 8 = 0 => mapping 8
      PID 'foo_bar8'  -> 8 % 8 = 0 => mapping 8
      PID 'xyz' or 'abc-NaN' -> mapping 1
    """
    import re

    pid = (cfg.PID or "").strip()
    if not pid:
        cfg.MAPPING = 1
        return

    # Capture trailing digits, with an optional '-' or '_' separator.
    # e.g., 'abc-12' / 'abc_12' / 'abc12' -> '12'
    m = re.search(r"[-_]?(\d+)$", pid)
    if not m:
        cfg.MAPPING = 1
        return

    try:
        n = int(m.group(1))
    except ValueError:
        cfg.MAPPING = 1
        return

    value = n % 8
    cfg.MAPPING = 8 if value == 0 else value


def admin(screen: pygame.Surface) -> pygame.Surface:
    """
    Admin phase: record GROUP (1-6), SESSION (1-6), DH (L/R), UH (L/R).

    Page flow:
      - After PID confirm: Admin_next
      - Group:            Admin_X (flip per 1..6), Enter -> Admin_X_Next
      - Session:          Admin_X_Y (flip per 1..6), Enter -> Admin_X_Y_Next
      - DH:               Admin_X_Y_L/R (flip per L/R), Enter -> Admin_X_Y_L/R_Next
      - UH:               Admin_X_Y_L/R_L/R (flip per L/R), Enter -> Admin_Please_L/R
      - Please:           Space -> return to start instructions
    """
    def _show(name: str) -> None:
        p = getattr(paths, name, None)
        if p is None:
            logger.error(f"[admin] Missing admin asset: {name}")
            return
        place_image(screen, p, fit_mode="contain", max_fraction=0.9)
        pygame.display.flip()
        pygame.event.clear()

    def _toggle_and_redraw(current_name: str) -> str:
        pygame.event.clear()
        _ = toggle_full_screen(screen)
        pygame.event.clear()
        _show(current_name)
        return current_name

    def _digit_from_key(k: int) -> int | None:
        mapping = {
            pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3,
            pygame.K_4: 4, pygame.K_5: 5, pygame.K_6: 6,
            pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3,
            pygame.K_KP4: 4, pygame.K_KP5: 5, pygame.K_KP6: 6,
        }
        return mapping.get(k)

    def _is_enter(k: int) -> bool:
        return k in (pygame.K_RETURN, pygame.K_KP_ENTER)

    def _hand_letter(val: str) -> str:
        return "L" if val == "left" else "R"

    # Ensure we start from Admin_next
    current_name = "Admin_next"
    _show(current_name)

    # Phase 1: GROUP
    cfg.GROUP = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_name = _toggle_and_redraw(current_name); continue
                d = _digit_from_key(event.key)
                if d is not None:
                    cfg.GROUP = d
                    current_name = f"Admin_{d}"
                    _show(current_name); continue
                if _is_enter(event.key):
                    if cfg.GROUP is None:
                        logger.warning("[admin] GROUP not selected; press 1-6 to choose."); continue
                    current_name = f"Admin_{cfg.GROUP}_Next"
                    _show(current_name); break
        else:
            pygame.time.delay(10); continue
        break

    # Phase 2: SESSION
    cfg.SESSION = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_name = _toggle_and_redraw(current_name); continue
                d = _digit_from_key(event.key)
                if d is not None:
                    cfg.SESSION = d
                    current_name = f"Admin_{cfg.GROUP}_{d}"
                    _show(current_name); continue
                if _is_enter(event.key):
                    if cfg.SESSION is None:
                        logger.warning("[admin] SESSION not selected; press 1-6 to choose."); continue
                    current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_Next"
                    _show(current_name); break
        else:
            pygame.time.delay(10); continue
        break

    # Phase 3: DH (dominant hand)
    cfg.DH = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_name = _toggle_and_redraw(current_name); continue
                if event.key in (pygame.K_l, pygame.K_r):
                    cfg.DH = "left" if event.key == pygame.K_l else "right"
                    current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}"
                    _show(current_name); continue
                if _is_enter(event.key):
                    if not cfg.DH:
                        logger.warning("[admin] DH not selected; press L/R to choose."); continue
                    current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}_Next"
                    _show(current_name); break
        else:
            pygame.time.delay(10); continue
        break

    # Phase 4: UH (hand used)
    cfg.UH = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    current_name = _toggle_and_redraw(current_name); continue
                if event.key in (pygame.K_l, pygame.K_r):
                    cfg.UH = "left" if event.key == pygame.K_l else "right"
                    current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}_{_hand_letter(cfg.UH)}"
                    _show(current_name); continue
                if _is_enter(event.key):
                    if not cfg.UH:
                        logger.warning("[admin] UH not selected; press L/R to choose."); continue
                    please_name = "Admin_Please_L" if cfg.UH == "left" else "Admin_Please_R"
                    _show(please_name)
                    screen = _wait_for_key_raw_pygame(screen, getattr(paths, please_name), pygame.K_SPACE)
                    pygame.event.clear()
                    return screen
        else:
            pygame.time.delay(10); continue


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
    - max_fraction:
        - Fraction of screen to use as the scaling target (default 1.0 = full screen).
        - Set to 0.9 for a 5% margin on each side (matching CCS get_scaled_stimulus).

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

    :param max_fraction: Fraction of screen used as scaling target (default = 1.0)
    :type max_fraction: float

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
        # - contain: fit fully inside max_fraction of screen (no crop)
        img_w, img_h = img.get_size()
        max_w = screen_w * max_fraction
        max_h = screen_h * max_fraction
        if fit_mode == "contain":
            scale = min(max_w / img_w, max_h / img_h)
        else:
            scale = max(screen_w / img_w, screen_h / img_h)
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
        font = pygame.font.SysFont(None, cfg.FONT_TOO_LATE)
        text_surf = font.render("Muy lento!", True, cfg.YELLOW_RGB)
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
