# ./src/ui/pygame_render.py
"""
Pygame setup utilities + Admin flow.

- Initializes the Pygame display and toggles fullscreen.
- Renders images/text helpers used across the app.
- Collects PID and runs the Admin flow (Group → Session → DH → HU).

Notes:
- Admin assets are bound dynamically in utils.paths; variable names match filenames.
  Example: resources/admin/Admin_Next.png -> paths.Admin_Next
- Keyboard constants: use pygame.K_l / pygame.K_r (not K_L/K_R).
"""

from __future__ import annotations
from typing import Tuple, Optional
from pathlib import Path
import pygame

import utils.config as cfg
import utils.paths as paths
from utils.logger import get_logger

logger = get_logger("./src/ui/pygame_render")


# ------------------ Display ------------------

def init_display() -> pygame.Surface:
    flags = pygame.FULLSCREEN if cfg._is_fullscreen else 0
    screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), flags, vsync=1)
    pygame.display.set_caption("Nback")
    return screen


def toggle_full_screen(screen: pygame.Surface) -> pygame.Surface:
    cfg._is_fullscreen = not cfg._is_fullscreen
    flags = pygame.FULLSCREEN if cfg._is_fullscreen else 0
    screen = pygame.display.set_mode((cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), flags, vsync=1)
    if cfg._is_fullscreen:
        logger.info("[toggle_full_screen] Entered fullscreen")
    else:
        logger.info(f"[toggle_full_screen] Quitted fullscreen: {cfg.SCREEN_WIDTH} x {cfg.SCREEN_HEIGHT}")
    return screen


# ------------------ Basic Rendering ------------------

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


def place_image(
    screen: pygame.Surface,
    img_path: Path,
    center: Optional[Tuple[float, float]] = None,
    resize: Optional[Tuple[int, int]] = None,
    overlay: bool = False,
    fit_mode: str = "cover",
    max_fraction: float = 1.0,
) -> None:
    # Geometry
    screen_w, screen_h = screen.get_size()
    if center is None:
        center = (screen_w / 2, screen_h / 2)

    if len(center) != 2:
        logger.error("[place_image] Invalid input: 'center' must be a 2-element tuple.")
        return

    target_cx, target_cy = center
    if not (0 <= target_cx <= screen_w and 0 <= target_cy <= screen_h):
        logger.error(f"[place_image] Invalid input: center out of bounds: {center}")
        return

    if resize is not None:
        if len(resize) != 2:
            logger.error("[place_image] Invalid input: 'resize' must be a 2-element tuple.")
            return
        try:
            target_w = int(resize[0])
            target_h = int(resize[1])
        except (TypeError, ValueError):
            logger.error(f"[place_image] Invalid input: 'resize' must be numeric: {resize}")
            return
        if target_w <= 0 or target_h <= 0:
            logger.error(f"[place_image] Invalid input: 'resize' must be positive: {resize}")
            return

    if not img_path.exists():
        logger.error(f"[place_image] Image file not found -> {img_path}")
        return

    try:
        img = pygame.image.load(str(img_path)).convert_alpha()
    except Exception as e:
        logger.error(f"[place_image] Failed to load image -> {img_path} | {e}")
        return

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

    img = pygame.transform.smoothscale(img, (target_w, target_h))

    if not overlay:
        screen.fill(cfg.BLACK_RGB)

    img_rect = img.get_rect(center=(target_cx, target_cy))
    screen.blit(img, img_rect)


def show_feedback(screen: pygame.Surface, status: str) -> None:
    screen_w, screen_h = screen.get_size()
    center = (screen_w / 2, screen_h * 0.62)

    if status == "correct":
        place_image(screen, Path(paths.FB_CORRECT), center=center, resize=(cfg.FB_W, cfg.FB_H), overlay=True)
        return
    if status == "incorrect":
        place_image(screen, Path(paths.FB_INCORRECT), center=center, resize=(cfg.FB_W, cfg.FB_H), overlay=True)
        return
    if status == "timeout":
        font = pygame.font.SysFont(None, cfg.FONT_SIZE)
        text_surf = font.render("Muy lento!", True, cfg.YELLOW_RGB)
        text_rect = text_surf.get_rect(center=center)
        screen.blit(text_surf, text_rect)
        return
    logger.error(f"[show_feedback] Invalid status: {status}")


def show_feedback_timed(
    screen: pygame.Surface,
    status: str,
    max_duration_ms: int,
    background_surface: pygame.Surface | None = None,
) -> None:
    screen_w, screen_h = screen.get_size()
    center = (screen_w / 2, screen_h * 0.64)

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
        feedback_surface = font.render("Muy lento!", True, cfg.YELLOW_RGB)
        feedback_rect = feedback_surface.get_rect(center=center)
    else:
        logger.error(f"[show_feedback_timed] Invalid status: {status}")
        return

    start_time = pygame.time.get_ticks()
    while (pygame.time.get_ticks() - start_time) < max_duration_ms:
        if background_surface:
            screen.blit(background_surface, (0, 0))
        screen.blit(feedback_surface, feedback_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
        pygame.time.delay(5)


def draw_fixation_cross(screen: pygame.Surface) -> None:
    screen_w, screen_h = screen.get_size()
    cx, cy = screen_w // 2, screen_h // 2
    half = cfg.CROSS_SIZE // 2
    width = 4
    pygame.draw.line(screen, cfg.WHITE_RGB, (cx - half, cy), (cx + half, cy), width)
    pygame.draw.line(screen, cfg.WHITE_RGB, (cx, cy - half), (cx, cy + half), width)


# ------------------ Admin helpers ------------------

def _play_admin_image(screen: pygame.Surface, img_path: Path) -> pygame.Surface:
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
    pygame.display.flip()
    pygame.event.clear()
    return screen.copy()


def _wait_for_key(screen: pygame.Surface, current_img: Path, predicate) -> Optional[int]:
    """Generic loop: pump events until predicate(key) returns True. Returns the key or None (never)."""
    bg = _play_admin_image(screen, current_img)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                bg = _play_admin_image(screen, current_img)
                continue
            if predicate(event.key):
                return event.key
        pygame.time.delay(10)


def _key_to_digit_1_6(key: int) -> Optional[int]:
    if key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
        return key - pygame.K_0
    return None


def _compute_mapping(pid: str) -> None:
    """Compute mapping from PID if needed. Kept as a placeholder to preserve API."""
    # Intentionally no-op (existing behavior preserved if mapping logic is external)
    return None


# ------------------ Admin flow (PID → Group → Session → DH → HU) ------------------

def get_participant_id(screen: pygame.Surface) -> pygame.Surface:
    """Collect PID on Admin, then flip to Admin_Next and run the Admin flow."""
    font = pygame.font.SysFont(None, cfg.FONT_SIZE)
    input_text = ""
    admin_img = getattr(paths, "Admin")
    admin_bg = _play_admin_image(screen, admin_img)

    while True:
        screen.blit(admin_bg, (0, 0))
        _render_centered_text(screen, font, input_text, screen.get_rect().centery + 20, cfg.SILVER_RGB)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                admin_bg = _play_admin_image(screen, admin_img)
                continue
            if event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]; continue
            if event.key == pygame.K_RETURN:
                if input_text.strip():
                    cfg.PID = input_text.strip()
                    _compute_mapping(cfg.PID)
                    # Flip to Admin_Next and proceed to the rest of Admin flow
                    next_img = getattr(paths, "Admin_Next")
                    _play_admin_image(screen, next_img)
                    screen = _run_admin_flow_from_admin_next(screen)
                    return screen
                continue
            if event.unicode:
                input_text += "".join(ch for ch in event.unicode if ch.isprintable())
        pygame.time.delay(10)


def _run_admin_flow_from_admin_next(screen: pygame.Surface) -> pygame.Surface:
    # Stage 1: GROUP on Admin_Next
    current_name = "Admin_Next"
    current_img = getattr(paths, current_name)
    _play_admin_image(screen, current_img)

    group: Optional[int] = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                _play_admin_image(screen, getattr(paths, current_name)); continue
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                group = event.key - pygame.K_0
                current_name = f"Admin_{group}"
                _play_admin_image(screen, getattr(paths, current_name))
                continue
            if event.key == pygame.K_RETURN:
                if group is None:
                    logger.warning("[admin] GROUP not selected yet; press 1-6 to choose.")
                    continue
                current_name = f"Admin_{group}_Next"
                _play_admin_image(screen, getattr(paths, current_name))
                cfg.GROUP = group
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # Stage 2: SESSION on Admin_{X}_Next
    session: Optional[int] = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                _play_admin_image(screen, getattr(paths, current_name)); continue
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                session = event.key - pygame.K_0
                current_name = f"Admin_{cfg.GROUP}_{session}"
                _play_admin_image(screen, getattr(paths, current_name))
                continue
            if event.key == pygame.K_RETURN:
                if session is None:
                    continue  # silently ignore until chosen
                current_name = f"Admin_{cfg.GROUP}_{session}_Next"
                _play_admin_image(screen, getattr(paths, current_name))
                cfg.SESSION = session
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # Stage 3: DH on Admin_{X}_{Y}_Next (L/R)
    dh: Optional[str] = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                _play_admin_image(screen, getattr(paths, current_name)); continue
            if event.key == pygame.K_l:
                dh = "left"
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_L"
                _play_admin_image(screen, getattr(paths, current_name))
                continue
            if event.key == pygame.K_r:
                dh = "right"
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_R"
                _play_admin_image(screen, getattr(paths, current_name))
                continue
            if event.key == pygame.K_RETURN:
                if dh is None:
                    continue
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{'L' if dh=='left' else 'R'}_Next"
                _play_admin_image(screen, getattr(paths, current_name))
                cfg.dominant_hand = dh
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # Stage 4: HU on Admin_{X}_{Y}_{L/R}_Next (L/R) then Admin_Please_L/R (SPACE)
    hu: Optional[str] = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                _play_admin_image(screen, getattr(paths, current_name)); continue
            if event.key == pygame.K_l:
                hu = "left"
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{'L' if cfg.dominant_hand=='left' else 'R'}_L"
                _play_admin_image(screen, getattr(paths, current_name))
                continue
            if event.key == pygame.K_r:
                hu = "right"
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{'L' if cfg.dominant_hand=='left' else 'R'}_R"
                _play_admin_image(screen, getattr(paths, current_name))
                continue
            if event.key == pygame.K_RETURN:
                if hu is None:
                    continue
                please_name = "Admin_Please_L" if hu == "left" else "Admin_Please_R"
                please_img = getattr(paths, please_name)
                _play_admin_image(screen, please_img)
                cfg.hand_used = hu
                # Wait for SPACE to continue into instructions
                while True:
                    for evt in pygame.event.get():
                        if evt.type == pygame.QUIT:
                            pygame.quit(); raise SystemExit
                        if evt.type == pygame.KEYDOWN:
                            if evt.key == pygame.K_ESCAPE:
                                pygame.event.clear(); screen = toggle_full_screen(screen); pygame.event.clear()
                                _play_admin_image(screen, please_img)
                                continue
                            if evt.key == pygame.K_SPACE:
                                return screen
                    pygame.time.delay(10)
        pygame.time.delay(10)


# ------------------ Beep (no-op placeholder) ------------------
_BEEP_SOUND: pygame.mixer.Sound | None = None

def _play_beep() -> None:
    return None
