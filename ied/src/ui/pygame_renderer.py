# ./src/ui/pygame_renderer.py
"""
Pygame rendering utilities.

This module centralizes all pygame display-related functionality.
"""

from __future__ import annotations

from typing import Tuple, Optional
from pathlib import Path
import pygame

import utils.config as cfg
import utils.paths as paths
from utils.logger import get_logger
from utils.event_handler import EventHandler


logger = get_logger("./src/ui/pygame_renderer")


def init_display() -> pygame.Surface:
    """Initialize display window. Start in full-screen mode."""
    flags = pygame.FULLSCREEN if cfg._is_fullscreen else 0
    screen = pygame.display.set_mode(
        (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), flags, vsync=1
    )
    pygame.display.set_caption("IED")
    return screen


def toggle_full_screen(screen: pygame.Surface) -> pygame.Surface:
    """Toggle between full-screen and windowed mode, and return the new screen object."""
    cfg._is_fullscreen = not cfg._is_fullscreen
    flags = pygame.FULLSCREEN if cfg._is_fullscreen else 0
    screen = pygame.display.set_mode(
        (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), flags, vsync=1
    )
    if cfg._is_fullscreen:
        logger.info("Entered fullscreen")
    else:
        logger.info(f"Quitted fullscreen: {cfg.SCREEN_WIDTH} x {cfg.SCREEN_HEIGHT}")
    return screen


def _render_centered_text(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    y: int,
    color: Tuple[int, int, int],
) -> None:
    """Render a line of text centered at the given y coordinate."""
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(screen.get_rect().centerx, y))
    screen.blit(surf, rect.topleft)


def _play_admin_image(screen: pygame.Surface, img_path: Path) -> pygame.Surface:
    """
    Show one admin page directly.

    Returns a screen snapshot used as static background for overlay rendering.
    """
    place_image(screen, img_path, max_fraction=0.9)
    pygame.display.flip()
    pygame.event.clear()
    return screen.copy()


def _get_admin_image(name: str) -> Path | None:
    """Resolve dynamic admin image variable from utils.paths by variable name.

    Returns None if the variable does not exist.
    """
    try:
        return getattr(paths, name)
    except Exception:
        logger.error(f"Admin image not found for variable '{name}'")
        return None


def _wait_for_left_or_right(
    screen: pygame.Surface,
    event_handler: EventHandler,
    img_path: Path,
) -> tuple[pygame.Surface, str]:
    """
    Show admin image and wait until L or R is pressed.
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

        if state.left_hand:
            return screen, "left"

        if state.right_hand:
            return screen, "right"

        pygame.time.delay(10)


def _wait_for_key_raw_pygame(
    screen: pygame.Surface,
    img_path: Path,
    target_key: int,
) -> pygame.Surface:
    """
    Wait until target key is pressed using raw pygame events (no EventHandler).
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
    Compute mapping from PID suffix.

    Rule:
    - Last char is an even digit -> mapping 2
    - Last char is an odd digit OR not a digit -> mapping 1
    """
    if not pid:
        return 1
    last_char = pid[-1]
    if not last_char.isdigit():
        return 1
    return 2 if int(last_char) % 2 == 0 else 1


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
    Show Admin and collect participant ID via keyboard input.
    """
    font = pygame.font.SysFont(None, cfg.FONT_SIZE)
    input_text = ""
    # Admin page filename has changed: Admin_1.png -> Admin.png
    # Bound by utils.paths as variable `Admin`.
    admin_bg = _play_admin_image(screen, paths.Admin)

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
                admin_bg = _play_admin_image(screen, paths.Admin)
                continue

            if event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
                continue

            if event.key == pygame.K_RETURN:
                if input_text.strip():
                    cfg.PID = input_text.strip()
                    cfg.MAPPING = _compute_mapping_from_pid(cfg.PID)
                    # Flip to Admin_Next and continue with the new admin flow.
                    admin_next = _get_admin_image("Admin_Next")
                    if admin_next is not None:
                        _play_admin_image(screen, admin_next)
                    screen = _run_admin_flow_after_pid(screen)
                    return screen
                continue

            if event.unicode:
                input_text += "".join(ch for ch in event.unicode if ch.isprintable())

        pygame.time.delay(10)


def _run_admin_flow_after_pid(screen: pygame.Surface) -> pygame.Surface:
    """Run the four-stage admin flow after PID is recorded.

    Stages:
      1) GROUP: digits 1-6. Flip Admin_X. Enter -> Admin_X_Next.
      2) SESSION: digits 1-6. Flip Admin_X_Y. Enter -> Admin_X_Y_Next.
      3) DH: L/R only. Store cfg.dominant_hand = left/right. Flip Admin_X_Y_L/R. Enter -> Admin_X_Y_L/R_Next.
      4) HU: L/R only. Store cfg.hand_used = left/right. Flip Admin_X_Y_L/R_L/R. Enter -> Admin_Please_L/R.
         Wait SPACE to proceed to instructions.
    """
    # Stage 1: GROUP
    current_group: str | None = None
    current_img_name = "Admin_Next"

    def _flip_by_name(name: str) -> None:
        path = _get_admin_image(name)
        if path is not None:
            _play_admin_image(screen, path)

    _flip_by_name(current_img_name)

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
                _flip_by_name(current_img_name)
                continue

            # Digits 1-6 set GROUP and flip to Admin_X
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                current_group = chr(event.key)
                cfg.GROUP = current_group
                current_img_name = f"Admin_{current_group}"
                _flip_by_name(current_img_name)
                continue

            # ENTER ends Stage 1 only if GROUP is chosen
            if event.key == pygame.K_RETURN:
                if current_group is None:
                    logger.warning("[Admin] GROUP not selected yet; ignoring ENTER.")
                    continue
                current_img_name = f"Admin_{current_group}_Next"
                _flip_by_name(current_img_name)
                break
        else:
            pygame.time.delay(10)
            continue
        break  # break outer while when stage finished

    # Stage 2: SESSION
    current_session: str | None = None
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
                _flip_by_name(current_img_name)
                continue

            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                current_session = chr(event.key)
                cfg.SESSION = current_session
                # Replace _Next with _<session>
                base = f"Admin_{current_group}"
                current_img_name = f"{base}_{current_session}"
                _flip_by_name(current_img_name)
                continue

            if event.key == pygame.K_RETURN:
                if current_session is None:
                    logger.warning("[Admin] SESSION not selected yet; ignoring ENTER.")
                    continue
                current_img_name = f"Admin_{current_group}_{current_session}_Next"
                _flip_by_name(current_img_name)
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # Stage 3: Dominant Hand (DH)
    current_dh: str | None = None  # "L" or "R"
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
                _flip_by_name(current_img_name)
                continue

            if event.key == pygame.K_l:
                current_dh = "L"
                cfg.dominant_hand = "left"
                base = f"Admin_{current_group}_{current_session}"
                current_img_name = f"{base}_{current_dh}"
                _flip_by_name(current_img_name)
                continue

            if event.key == pygame.K_r:
                current_dh = "R"
                cfg.dominant_hand = "right"
                base = f"Admin_{current_group}_{current_session}"
                current_img_name = f"{base}_{current_dh}"
                _flip_by_name(current_img_name)
                continue

            if event.key == pygame.K_RETURN:
                if current_dh is None:
                    logger.warning("[Admin] DH not selected yet; ignoring ENTER.")
                    continue
                current_img_name = f"Admin_{current_group}_{current_session}_{current_dh}_Next"
                _flip_by_name(current_img_name)
                break
        else:
            pygame.time.delay(10)
            continue
        break

    # Stage 4: Hand Used (HU)
    current_hu: str | None = None  # "L" or "R"
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
                _flip_by_name(current_img_name)
                continue

            if event.key == pygame.K_l:
                current_hu = "L"
                cfg.hand_used = "left"
                base = f"Admin_{current_group}_{current_session}_{current_dh}"
                current_img_name = f"{base}_{current_hu}"
                _flip_by_name(current_img_name)
                continue

            if event.key == pygame.K_r:
                current_hu = "R"
                cfg.hand_used = "right"
                base = f"Admin_{current_group}_{current_session}_{current_dh}"
                current_img_name = f"{base}_{current_hu}"
                _flip_by_name(current_img_name)
                continue

            if event.key == pygame.K_RETURN:
                if current_hu is None:
                    logger.warning("[Admin] HU not selected yet; ignoring ENTER.")
                    continue
                # On ENTER, show Admin_Please_L or Admin_Please_R (no *_Next variant).
                please_name = "Admin_Please_L" if cfg.hand_used == "left" else "Admin_Please_R"
                _flip_by_name(please_name)
                # Wait for SPACE to proceed to instructions
                screen = _wait_for_key_raw_pygame(screen, _get_admin_image(please_name), pygame.K_SPACE)
                return screen

        else:
            pygame.time.delay(10)
            continue

    return screen


def _compute_centers(size: Tuple[int, int]) -> dict[str, tuple[int, int]]:
    """
    Measure the center of screen
    Locate the center for 4 blocks
    """
    w, h = size
    cx, cy = w / 2, h / 2
    top = (int(cx), int(cy - h * 0.25))
    bottom = (int(cx), int(cy + h * 0.25))
    left = (int(cx - w * 0.25), int(cy))
    right = (int(cx + w * 0.25), int(cy))

    return {
        "top": top,
        "bottom": bottom,
        "left": left,
        "right": right,
    }


def _rect_from_center(center: tuple[int, int]) -> pygame.Rect:
    """Place the 4 blocks based on their located centers."""
    x, y = center
    return pygame.Rect(int(x - cfg.RECT_W / 2), int(y - cfg.RECT_H / 2), cfg.RECT_W, cfg.RECT_H)


def draw_blocks(screen: pygame.Surface) -> None:
    """
    Fill the background
    Draw the 4 blocks (filled)
    """
    screen.fill(cfg.BLACK_RGB)
    centers = _compute_centers(screen.get_size())
    for c in centers.values():
        pygame.draw.rect(
            screen,
            cfg.COCO_RGB,
            _rect_from_center(c),
            width=cfg.BORDER_PX,
            border_radius=20,
        )


def show_ied_ui(screen: pygame.Surface) -> None:
    """Display UI."""
    draw_blocks(screen)


def _load_image(path: Path) -> pygame.Surface | None:
    if not path.exists():
        logger.error(f"place_image: file not found -> {path}")
        return None
    try:
        return pygame.image.load(str(path)).convert_alpha()
    except Exception as e:
        logger.error(f"place_image: failed to load image -> {path} | {e}")
        return None


def place_image(
    screen: pygame.Surface,
    img_path: Path,
    center: Optional[Tuple[float, float]] = None,
    resize: Optional[Tuple[int, int]] = None,
    max_fraction: float = 1.0,
) -> None:
    """
    Load an image from disk, resize it, and blit it onto the screen at a given center position.
    """
    img = _load_image(Path(img_path))
    if img is None:
        return None

    w, h = screen.get_size()

    if resize is not None:
        img = pygame.transform.smoothscale(img, resize)
    else:
        orig_w, orig_h = img.get_size()
        if orig_w > 0 and orig_h > 0:
            scale = min(w * max_fraction / orig_w, h * max_fraction / orig_h)
            new_size = (max(1, int(orig_w * scale)), max(1, int(orig_h * scale)))
            if new_size != (orig_w, orig_h):
                img = pygame.transform.smoothscale(img, new_size)

    if center is None:
        center = (int(w / 2), int(h / 2))

    screen.fill(cfg.BLACK_RGB)
    img_rect = img.get_rect(center=center)
    screen.blit(img, img_rect)


def place_single_image(screen: pygame.Surface, img_path: Path, ind: int) -> None:
    """
    Place stimulus image on assigned position
        - 1: top
        - 2: bottom
        - 3: left
        - 4: right
    """
    img = _load_image(Path(img_path))
    if img is None:
        return None

    # Resize image (max_W = RECT_W - 50 / max_H = RECT_H - 50)
    orig_w, orig_h = img.get_size()
    max_w, max_h = cfg.RECT_W - 50, cfg.RECT_H - 50
    if orig_w <= 0 or orig_h <= 0:
        logger.error(f"place_image: invalid image size -> {img_path} ({orig_w}x{orig_h})")
        return None

    scale = min(max_w / orig_w, max_h / orig_h)
    new_size = (max(1, int(orig_w * scale)), max(1, int(orig_h * scale)))
    if new_size != (orig_w, orig_h):
        img = pygame.transform.smoothscale(img, new_size)

    centers = _compute_centers(screen.get_size())
    key_map = {1: "top", 2: "bottom", 3: "left", 4: "right"}
    key = key_map.get(ind)
    if key is None:
        logger.error(f"place_image: invalid position code ind={ind} (expect 1 / 2 / 3 / 4)")
        return None

    center = centers[key]
    img_rect = img.get_rect(center=center)
    screen.blit(img, img_rect)


def place_side_by_side_images(screen: pygame.Surface, shape_img_path: Path, line_img_path: Path, ind: int) -> None:
    """
    Place two stimulus images (shape + line) on the assigned position.
    Place shape on the left, line on the right.
    """
    paths = {"shape": shape_img_path, "line": line_img_path}
    images = {}

    for key, path in paths.items():
        img = _load_image(Path(path))
        if img is None:
            return None

        orig_w, orig_h = img.get_size()
        max_w, max_h = cfg.RECT_W - 50, cfg.RECT_H - 50
        if orig_w <= 0 or orig_h <= 0:
            logger.error(f"place_image: invalid image size -> {path} ({orig_w}x{orig_h})")
            return None

        scale = min(max_w / orig_w, max_h / orig_h)
        new_size = (max(1, int(orig_w * scale)), max(1, int(orig_h * scale)))
        if new_size != (orig_w, orig_h):
            img = pygame.transform.smoothscale(img, new_size)

        images[key] = img

    centers = _compute_centers(screen.get_size())
    key_map = {1: "top", 2: "bottom", 3: "left", 4: "right"}
    key = key_map.get(ind)
    if key is None:
        logger.error(f"place_image: invalid position code ind={ind} (expect 1 / 2 / 3 / 4)")
        return None

    center = centers[key]
    offset_x = cfg.RECT_W * 0.25
    cx, cy = center

    shape_center = (int(cx - offset_x), int(cy))
    line_center = (int(cx + offset_x), int(cy))

    screen.blit(images["shape"], images["shape"].get_rect(center=shape_center))
    screen.blit(images["line"], images["line"].get_rect(center=line_center))


def place_overlapped_images(screen: pygame.Surface, shape_img_path: Path, line_img_path: Path, ind: int) -> None:
    """
    Place two stimulus images (shape + line) on the assigned position.
    Place shape behind line.
    """
    paths = {"shape": shape_img_path, "line": line_img_path}
    images = {}

    for key, path in paths.items():
        img = _load_image(Path(path))
        if img is None:
            return None

        orig_w, orig_h = img.get_size()
        max_w, max_h = cfg.RECT_W - 50, cfg.RECT_H - 50
        if orig_w <= 0 or orig_h <= 0:
            logger.error(f"place_image: invalid image size -> {path} ({orig_w}x{orig_h})")
            return None

        scale = min(max_w / orig_w, max_h / orig_h)
        new_size = (max(1, int(orig_w * scale)), max(1, int(orig_h * scale)))
        if new_size != (orig_w, orig_h):
            img = pygame.transform.smoothscale(img, new_size)

        images[key] = img

    centers = _compute_centers(screen.get_size())
    key_map = {1: "top", 2: "bottom", 3: "left", 4: "right"}
    key = key_map.get(ind)
    if key is None:
        logger.error(f"place_image: invalid position code ind={ind} (expect 1 / 2 / 3 / 4)")
        return None

    center = centers[key]
    screen.blit(images["shape"], images["shape"].get_rect(center=center))
    screen.blit(images["line"], images["line"].get_rect(center=center))


def show_feedback(screen: pygame.Surface, correct: bool) -> None:
    """
    Show feedback at the center of the screen.
    """
    img_path = paths.FB_CORRECT if correct else paths.FB_INCORRECT
    img = _load_image(Path(img_path))
    if img is None:
        return None

    orig_w, orig_h = img.get_size()
    max_w, max_h = cfg.RECT_W - 50, cfg.RECT_H - 50
    if orig_w <= 0 or orig_h <= 0:
        logger.error(f"show_feedback: invalid image size -> {img_path} ({orig_w}x{orig_h})")
        return None

    scale = min(max_w / orig_w, max_h / orig_h)
    new_size = (max(1, int(orig_w * scale)), max(1, int(orig_h * scale)))
    if new_size != (orig_w, orig_h):
        img = pygame.transform.smoothscale(img, new_size)

    w, h = screen.get_size()
    center = (int(w / 2), int(h / 2))
    img_rect = img.get_rect(center=center)
    screen.blit(img, img_rect)
