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
from utils.paths import BEEP, FB_CORRECT, FB_INCORRECT
from utils.event_handler import EventHandler


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
        screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H), pygame.FULLSCREEN, vsync=1)
    else:
        screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H), 0, vsync=1)
    pygame.display.set_caption("TASK")
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
        screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H), pygame.FULLSCREEN, vsync=1)
        logger.info(f"[toggle_full_screen] Entered fullscreen: {cfg.SCREEN_W} x {cfg.SCREEN_H}")
    else:
        screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H), 0, vsync=1)
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
    Show one admin page and return a snapshot used as static background.
    """
    place_image(screen, img_path)
    pygame.display.flip()
    pygame.event.clear()
    return screen.copy()


def _wait_for_left_or_right(
    screen: pygame.Surface,
    event_handler: EventHandler,
    img_path: Path,
) -> tuple[pygame.Surface, str]:
    """
    Show admin page and wait until left or right key is selected.
    """
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
    Wait for one target key using raw pygame events.
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


def _compute_mapping_from_pid(pid: str) -> int:
    """
    Compute MAPPING from PID suffix.
    - Even digit: mapping 2
    - Odd digit or non-digit suffix: mapping 1
    """
    if not pid:
        return 1
    last_char = pid[-1]
    if not last_char.isdigit():
        return 1
    return 2 if int(last_char) % 2 == 0 else 1


def get_participant_id(screen: pygame.Surface) -> pygame.Surface:
    """
    Show ADMIN_1 page and collect participant ID via keyboard input.
    """
    font = pygame.font.SysFont(None, cfg.FONT_SMALL)
    input_text = ""
    # Admin PID page updated: use Admin.png instead of Admin_1.png
    admin_bg = _play_admin_image(screen, getattr(paths, "Admin"))

    while True:
        screen.blit(admin_bg, (0, 0))
        _render_centered_text(screen, font, input_text, screen.get_rect().centery + 20, cfg.COCO_RGB)
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
                admin_bg = _play_admin_image(screen, getattr(paths, "Admin"))
                continue

            if event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
                continue

            if event.key == pygame.K_RETURN:
                if input_text.strip():
                    cfg.PID = input_text.strip()
                    cfg.MAPPING = _compute_mapping_from_pid(cfg.PID)
                    # After PID saved and mapping computed, flip to Admin_Next
                    try:
                        next_img = getattr(paths, "Admin_Next")
                    except Exception:
                        next_img = paths.ADMIN_DIR / "Admin_Next.png"
                    _play_admin_image(screen, next_img)
                    return screen
                continue

            if event.unicode:
                input_text += "".join(ch for ch in event.unicode if ch.isprintable())

        pygame.time.delay(10)


def _compute_mapping() -> None:
    """
    Backward-compatible wrapper for existing callers.
    """
    cfg.MAPPING = _compute_mapping_from_pid(cfg.PID or "")


def _resolve_admin_img(name: str) -> Path:
    """Resolve an Admin image by variable name, falling back to direct file path.
    Keeps exact case (e.g., Admin_Next)."""
    img = getattr(paths, name, None)
    if img is None:
        img = paths.ADMIN_DIR / f"{name}.png"
    return img


def run_admin_flow(screen: pygame.Surface) -> pygame.Surface:
    """
    Admin phase flow:
    1) Group selection (1-6) starting from Admin_Next; ENTER to confirm -> Admin_X_Next
    2) Session selection (1-6) from Admin_X_Next; ENTER to confirm -> Admin_X_Y_Next
    3) Dominant hand (L/R) from Admin_X_Y_Next; ENTER to confirm -> Admin_X_Y_L|R_Next
    4) Hand used (L/R); ENTER to confirm -> Admin_Please_L|R; SPACE to proceed
    """

    # ---------- Phase 1: GROUP ----------
    current_name = "Admin_Next"
    admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))

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
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                cfg.GROUP = int(pygame.key.name(event.key))
                current_name = f"Admin_{cfg.GROUP}"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key == pygame.K_RETURN:
                if cfg.GROUP is None:
                    logger.warning("[admin] GROUP not selected; press 1-6 before ENTER")
                    continue
                current_name = f"Admin_{cfg.GROUP}_Next"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # ---------- Phase 2: SESSION ----------
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
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                cfg.SESSION = int(pygame.key.name(event.key))
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key == pygame.K_RETURN:
                if cfg.SESSION is None:
                    logger.warning("[admin] SESSION not selected; press 1-6 before ENTER")
                    continue
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_Next"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # ---------- Phase 3: Dominant Hand (DH) ----------
    dh_code: str | None = None  # "L" / "R"
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
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key == pygame.K_l:
                cfg.DH = "left"
                dh_code = "L"
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_L"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key == pygame.K_r:
                cfg.DH = "right"
                dh_code = "R"
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_R"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key == pygame.K_RETURN:
                if dh_code is None:
                    logger.warning("[admin] Dominant hand not selected; press L/R before ENTER")
                    continue
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{dh_code}_Next"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # ---------- Phase 4: Hand Used (HU) ----------
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
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key == pygame.K_l:
                cfg.UH = "left"
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{dh_code}_L"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key == pygame.K_r:
                cfg.UH = "right"
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{dh_code}_R"
                admin_bg = _play_admin_image(screen, _resolve_admin_img(current_name))
                continue

            if event.key == pygame.K_RETURN:
                if cfg.UH is None:
                    logger.warning("[admin] Hand used not selected; press L/R before ENTER")
                    continue
                please_img = _resolve_admin_img("Admin_Please_L" if cfg.UH == "left" else "Admin_Please_R")
                _play_admin_image(screen, please_img)
                # Space to proceed into instructions
                screen = _wait_for_key_raw_pygame(screen, please_img, pygame.K_SPACE)
                return screen

        pygame.time.delay(10)


def place_image(
    screen: pygame.Surface,
    img_path: Path,
    center: Optional[Tuple[float, float]] = None,
    resize: Optional[Tuple[int, int]] = None,
    overlay: bool = False,
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
    if resize is None:
        resize = (screen_w, screen_h)

    # Validate parameter shape
    if len(center) != 2 or len(resize) != 2:
        logger.error("[place_image] Invalid input: 'center' and 'resize' must be 2-element tuples.")
        return

    target_cx, target_cy = center
    target_w, target_h = resize

    # Validate center range
    if not (0 <= target_cx <= screen_w and 0 <= target_cy <= screen_h):
        logger.error(
            f"[place_image] Invalid input: 'center' out of bounds: center={center}, screen=({screen_w}, {screen_h})"
        )
        return

    # Validate resize values
    try:
        target_w = int(target_w)
        target_h = int(target_h)
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
            img_path=Path(FB_CORRECT),
            center=center,
            resize=(cfg.FB_W, cfg.FB_H),
            overlay=True,
        )
        return

    if status == "incorrect":
        place_image(
            screen=screen,
            img_path=Path(FB_INCORRECT),
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
