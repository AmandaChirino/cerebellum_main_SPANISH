# ./src/ui/pygame_render.py
"""
Pygame setup utilities.

This module initializes the Pygame display, manages fullscreen toggling,
renders basic text elements, collects PID + mapping, and runs the admin phase.
"""

from __future__ import annotations
from typing import Tuple, Optional
from pathlib import Path
import pygame

import utils.config as cfg
import utils.paths as paths
from utils.event_handler import EventHandler
from utils.logger import get_logger

logger = get_logger("./src/ui/pygame_render")


def _safe_delay(ms: int = 10) -> None:
    """pygame.time.delay wrapper that ignores KeyboardInterrupt from OS signals."""
    try:
        pygame.time.delay(ms)
    except KeyboardInterrupt:
        pass


def init_display() -> pygame.Surface:
    """Initialize the pygame display window."""
    if cfg._is_fullscreen:
        screen_info = pygame.display.Info()
        cfg.SCREEN_W = screen_info.current_w
        cfg.SCREEN_H = screen_info.current_h
        screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H), pygame.FULLSCREEN, vsync=1)
    else:
        screen = pygame.display.set_mode((cfg.SCREEN_W, cfg.SCREEN_H), 0, vsync=1)
    pygame.display.set_caption("GSS")
    return screen


def toggle_full_screen(screen: pygame.Surface) -> pygame.Surface:
    """Toggle between full-screen and windowed display modes."""
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
    pygame.display.set_caption("GSS")
    return screen


def _render_centered_text(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    y: int,
    color: Tuple[int, int, int],
) -> None:
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(screen.get_rect().centerx, y))
    screen.blit(surf, rect.topleft)


def _play_admin_image(screen: pygame.Surface, img_path: Path) -> pygame.Surface:
    """Show one admin page and return a copied background for overlay rendering."""
    place_image(screen=screen, img_path=img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    pygame.event.clear()
    return screen.copy()


def _wait_for_key_raw_pygame(
    screen: pygame.Surface,
    img_path: Path,
    target_key: int,
) -> pygame.Surface:
    """Wait until target key is pressed on the current admin page."""
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
        _safe_delay()


def get_participant_id(screen: pygame.Surface) -> pygame.Surface:
    """
    Display Admin page and collect participant ID.

    After confirming with Enter, compute mapping and flip to Admin_next.
    """
    font = pygame.font.SysFont(None, cfg.FONT_SMALL)
    input_text = ""
    admin_bg = _play_admin_image(screen, getattr(paths, 'Admin'))

    while True:
        screen.blit(admin_bg, (0, 0))
        _render_centered_text(screen, font, input_text, screen.get_rect().centery + 20, cfg.COCO_RGB)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                screen = toggle_full_screen(screen)
                admin_bg = _play_admin_image(screen, getattr(paths, 'Admin'))
                continue

            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if input_text.strip():
                    cfg.PID = input_text.strip()
                    _compute_mapping()
                    _play_admin_image(screen, getattr(paths, 'Admin_Next'))
                    pygame.display.flip()
                    pygame.event.clear()
                    return screen
                else:
                    continue

            if event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
                continue

            # Accept visible characters
            if event.unicode:
                input_text += "".join(ch for ch in event.unicode if ch.isprintable())

        _safe_delay()


def _compute_mapping():
    """Set MAPPING from PID suffix (odd->1 / even->2). Default to 1 for non-numeric PID."""
    try:
        pid_int = int(cfg.PID[-1])
    except (TypeError, ValueError):
        logger.warning(f"Invalid PID suffix for mapping: {cfg.PID!r}. Fallback MAPPING=1.")
        cfg.MAPPING = 1
        return
    cfg.MAPPING = 1 if (pid_int % 2 == 1) else 2


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
        place_image(screen, p, fit_mode='contain', max_fraction=0.9)
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
        return 'L' if val == 'left' else 'R'

    # Ensure we start from Admin_next
    current_name = 'Admin_next'
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
                    current_name = f'Admin_{d}'
                    _show(current_name); continue
                if _is_enter(event.key):
                    if cfg.GROUP is None:
                        logger.warning('[admin] GROUP not selected; press 1-6 to choose.'); continue
                    current_name = f'Admin_{cfg.GROUP}_Next'
                    _show(current_name); break
        else:
            _safe_delay(); continue
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
                    current_name = f'Admin_{cfg.GROUP}_{d}'
                    _show(current_name); continue
                if _is_enter(event.key):
                    if cfg.SESSION is None:
                        logger.warning('[admin] SESSION not selected; press 1-6 to choose.'); continue
                    current_name = f'Admin_{cfg.GROUP}_{cfg.SESSION}_Next'
                    _show(current_name); break
        else:
            _safe_delay(); continue
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
                    cfg.DH = 'left' if event.key == pygame.K_l else 'right'
                    current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}"
                    _show(current_name); continue
                if _is_enter(event.key):
                    if not cfg.DH:
                        logger.warning('[admin] DH not selected; press L/R to choose.'); continue
                    current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}_Next"
                    _show(current_name); break
        else:
            _safe_delay(); continue
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
                    cfg.UH = 'left' if event.key == pygame.K_l else 'right'
                    current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}_{_hand_letter(cfg.UH)}"
                    _show(current_name); continue
                if _is_enter(event.key):
                    if not cfg.UH:
                        logger.warning('[admin] UH not selected; press L/R to choose.'); continue
                    please_name = 'Admin_Please_L' if cfg.UH == 'left' else 'Admin_Please_R'
                    _show(please_name)
                    screen = _wait_for_key_raw_pygame(screen, getattr(paths, please_name), pygame.K_SPACE)
                    pygame.event.clear()
                    return screen
        else:
            _safe_delay(); continue


def place_image(
    screen: pygame.Surface,
    img_path: Path,
    center: Optional[Tuple[float, float]] = None,
    resize: Optional[Tuple[int, int]] = None,
    overlay: bool = False,
    fit_mode: str = "cover",
    max_fraction: float = 0.9,
) -> None:
    """
    Load an image from disk, resize it, and blit it onto the screen at a given center position.

    - Loads an image with alpha channel support.
    - Resizes the image to either fill (cover) or fit (contain) the screen.
    - Clears the screen with cfg.BLACK_RGB unless overlay=True.
    """
    # Get screen geometry
    screen_w, screen_h = screen.get_size()

    # Default parameters
    if center is None:
        center = (screen_w / 2, screen_h / 2)

    # Validate center
    if len(center) != 2:
        logger.error("[place_image] Invalid input: 'center' must be a 2-element tuple.")
        return
    target_cx, target_cy = center
    if not (0 <= target_cx <= screen_w and 0 <= target_cy <= screen_h):
        logger.error(f"[place_image] Invalid input: 'center' out of bounds: center={center}, screen=({screen_w}, {screen_h})")
        return

    # Check existence
    if not img_path.exists():
        logger.error(f"[place_image] Image file not found -> {img_path}")
        return

    # Load image
    try:
        img = pygame.image.load(str(img_path)).convert_alpha()
    except Exception as e:
        logger.error(f"[place_image] Failed to load image -> {img_path} | {e}")
        return

    # Resolve resize target
    img_w, img_h = img.get_size()
    if resize is None:
        max_w = screen_w * max_fraction
        max_h = screen_h * max_fraction
        if fit_mode == "contain":
            scale = min(max_w / img_w, max_h / img_h)
        else:
            scale = max(screen_w / img_w, screen_h / img_h)
        target_w = max(1, int(img_w * scale))
        target_h = max(1, int(img_h * scale))
    else:
        if len(resize) != 2:
            logger.error("[place_image] Invalid input: 'resize' must be a 2-element tuple.")
            return
        try:
            target_w, target_h = int(resize[0]), int(resize[1])
        except (TypeError, ValueError):
            logger.error(f"[place_image] Invalid input: 'resize' must be numeric: resize={resize}")
            return
        if target_w <= 0 or target_h <= 0:
            logger.error(f"[place_image] Invalid input: 'resize' must be positive: resize=({target_w}, {target_h})")
            return

    # Resize and blit
    img = pygame.transform.smoothscale(img, (target_w, target_h))
    if not overlay:
        screen.fill(cfg.BLACK_RGB)
    img_rect = img.get_rect(center=(target_cx, target_cy))
    screen.blit(img, img_rect)


def show_feedback(screen: pygame.Surface, status: str) -> None:
    """Overlay feedback on the current screen for 'correct'/'incorrect'/'timeout'."""
    screen_w, screen_h = screen.get_size()
    center = (screen_w / 2, screen_h * 0.68)

    if status == "correct" or status == 1:
        place_image(screen, Path(paths.FB_CORRECT), center=center, resize=(cfg.FB_W, cfg.FB_H), overlay=True)
        return
    if status == "incorrect" or status == 0:
        place_image(screen, Path(paths.FB_INCORRECT), center=center, resize=(cfg.FB_W, cfg.FB_H), overlay=True)
        return
    if status == "timeout":
        font = pygame.font.SysFont(None, cfg.FONT_SMALL)
        text_surf = font.render("Timeout!", True, cfg.YELLOW_RGB)
        text_rect = text_surf.get_rect(center=center)
        screen.blit(text_surf, text_rect)
        return
    logger.error(f"[show_feedback] Invalid status: {status}")


# Beep placeholder (disabled)
_BEEP_SOUND: pygame.mixer.Sound | None = None

def _play_beep() -> None:
    pass
