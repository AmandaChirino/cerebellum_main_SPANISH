# ./src/core/pygame_render.py
"""
Pygame setup utilities.

This module initializes the Pygame display, manages fullscreen toggling, renders basic text elements, and collects PID and VERSION.
"""


from __future__ import annotations
from typing import Tuple, Optional
import pygame
from pathlib import Path
import re
from utils.event_handler import EventHandler

import utils.config as cfg
import utils.paths as paths
from utils.logger import get_logger
from utils.paths import FB_CORRECT, FB_INCORRECT


logger = get_logger("./src/ui/pygame_render")


def init_display() -> pygame.Surface:
    """
    Initialize the pygame display window.

    :return: Initialized pygame display surface
    :rtype: pygame.Surface
    """

    flags = pygame.FULLSCREEN if cfg._is_fullscreen else 0
    screen = pygame.display.set_mode(
        (cfg.SCREEN_WIDTH, cfg.SCREEN_HEIGHT), flags, vsync=1,
    )
    pygame.display.set_caption("SD")
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
    Show ADMIN_1 page and collect participant ID via keyboard input.
    """
    font = pygame.font.SysFont(None, cfg.FONT_SMALL)
    input_text = ""
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
                    _play_admin_image(screen, paths.Admin_Next)
                    return screen
                continue

            if event.unicode:
                input_text += "".join(ch for ch in event.unicode if ch.isprintable())

        pygame.time.delay(10)

def _play_admin_image(screen: pygame.Surface, img_path: Path) -> pygame.Surface:
    """
    Show one admin page and return a snapshot used as static background.
    """
    place_image(screen, img_path, fit_mode="contain", max_fraction=0.9)
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

def _compute_mapping_from_pid(pid: str) -> int:
    """
    Determine MAPPING based on the last character of Participant ID:
    - If the last character is an odd digit -> MAPPING = 1
    - Otherwise (even digit / non-digit / empty) -> MAPPING = 2
    """
    if not pid:
        return 2
    last = pid[-1]
    if last.isdigit():
        return 1 if (int(last) % 2 == 1) else 2
    return 2

def _compute_mode_from_pid(pid: str) -> str:
    """
    Determine MODE based on the contents of Participant ID:
    - If string contains "demo" -> DEMO
    - Otherwise (empty or "actual") -> ACTUAL
    """
    pattern = r'(demo)'
    match = re.search(pattern, pid, re.IGNORECASE)
    if match:
        print(match.group().lower())
        return "demo"
    else:
        return "full"

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
        screen.fill(cfg.GRAY_RGB)

    # Blit image at target center
    img_rect = img.get_rect(center=(target_cx, target_cy))
    screen.blit(img, img_rect)


def show_feedback(screen: pygame.Surface, status: bool) -> None:
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

    if status == 1:
        place_image(
            screen=screen,
            img_path=Path(FB_CORRECT),
            center=center,
            resize=(cfg.FB_W, cfg.FB_H),
            overlay=True,
        )
        return

    if status == 0:
        place_image(
            screen=screen,
            img_path=Path(FB_INCORRECT),
            center=center,
            resize=(cfg.FB_W, cfg.FB_H),
            overlay=True,
        )
        return

    if status == "timeout":
        font = pygame.font.SysFont(None, cfg.FONT_SIZE)
        text_surf = font.render("Too late!", True, cfg.YELLOW_RGB)
        text_rect = text_surf.get_rect(center=center)
        screen.blit(text_surf, text_rect)
        return

    logger.error(f"[show_feedback] Invalid status: {status}")

def block_results(
        screen: pygame.Surface,
        accuracy: str,
        avg_RT: str,
        block: int,
        event_handler: EventHandler,
        ) -> pygame.Surface:
    """
    Display the Participant's block results; Space to continue; ESC to toggle fullscreen; 5 sec timeout

    Visual settings:
    - Background: cfg.GRAY_RGB
    - Text color: cfg.BLACK_RGB
    - Font: cfg.FONT_SIZE
    
    :param screen: Active pygame display surface
    :type screen: pygame.Surface

    :return: pygame.Surface
    """
    start_ms = pygame.time.get_ticks()
    font = pygame.font.SysFont(None, cfg.FONT_SIZE)

    def draw():
        screen.fill(cfg.BLACK_RGB)
        place_image(screen, paths.RESOURCES_DIR/"BlankSpace.png")
        screen_rect = screen.get_rect()

        _render_centered_text(
            screen, font,
            f"Block {block} Completed! Performance:",
            screen_rect.centery - 75,
            cfg.COCO_RGB,
        )

        _render_centered_text(
            screen, font,  f"Accuracy: {accuracy}%", screen_rect.centery - 20, cfg.COCO_RGB
        )
        _render_centered_text(
            screen, font, f"Average Speed: {avg_RT} s", screen_rect.centery + 20, cfg.COCO_RGB
        )
        pygame.display.flip()
    draw()

    logger.info(f"Accuracy: {accuracy:.3}% , Average Speed: {avg_RT:.3} s")

    while True:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()

        elapsed = pygame.time.get_ticks() - start_ms
        
        if elapsed >= 10000:
            logger.info(f"Timeout, end task")
            return screen
        
        if state.next_page and elapsed >= cfg.MIN_READING_TIME:
            return screen

        pygame.time.delay(10)

def run_admin_flow(screen: pygame.Surface) -> pygame.Surface:
    """Implement four-phase Admin flow per spec: GROUP -> SESSION -> DH -> HU.
    Pages are dynamically resolved from resources/admin by composing names like
    Admin, Admin_Next, Admin_3, Admin_3_Next, Admin_3_2, Admin_3_2_L, etc.
    """
    def _show(name: str) -> None:
        path = getattr(paths, name, None)
        if path is None:
            logger.error(f"[admin] Missing admin asset: {name}")
            return
        _play_admin_image(screen, path)

    def _toggle_if_esc(event: pygame.event.Event, current_name: str) -> str:
        if event.key == pygame.K_ESCAPE:
            pygame.event.clear()
            nonlocal_screen = toggle_full_screen(screen)
            # rebind outer screen reference
            globals()['screen'] = nonlocal_screen
            pygame.event.clear()
            _show(current_name)
            return current_name
        return current_name

    # Phase 1: GROUP selection on Admin_Next
    current_name = 'Admin_Next'
    _show(current_name)
    cfg.GROUP = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            current_name = _toggle_if_esc(event, current_name)
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                digit = pygame.key.name(event.key)
                cfg.GROUP = digit
                current_name = f'Admin_{digit}'
                _show(current_name)
            elif event.key == pygame.K_RETURN:
                if cfg.GROUP is None:
                    logger.warning('[admin] GROUP not selected yet.')
                else:
                    current_name = f'Admin_{cfg.GROUP}_Next'
                    _show(current_name)
                    break
        else:
            pygame.time.delay(10)
            continue
        break

    # Phase 2: SESSION selection on Admin_X_Next
    cfg.SESSION = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            current_name = _toggle_if_esc(event, current_name)
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                digit = pygame.key.name(event.key)
                cfg.SESSION = digit
                current_name = f'Admin_{cfg.GROUP}_{digit}'
                _show(current_name)
            elif event.key == pygame.K_RETURN:
                if cfg.SESSION is None:
                    logger.warning('[admin] SESSION not selected yet.')
                else:
                    current_name = f'Admin_{cfg.GROUP}_{cfg.SESSION}_Next'
                    _show(current_name)
                    break
        else:
            pygame.time.delay(10)
            continue
        break

    # Phase 3: DH (dominant hand), inputs L/R
    cfg.DH = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            current_name = _toggle_if_esc(event, current_name)
            if event.key == pygame.K_l:
                cfg.DH = 'left'
                current_name = f'Admin_{cfg.GROUP}_{cfg.SESSION}_L'
                _show(current_name)
            elif event.key == pygame.K_r:
                cfg.DH = 'right'
                current_name = f'Admin_{cfg.GROUP}_{cfg.SESSION}_R'
                _show(current_name)
            elif event.key == pygame.K_RETURN:
                if cfg.DH is None:
                    logger.warning('[admin] DH not selected yet.')
                else:
                    hand_tag = 'L' if cfg.DH == 'left' else 'R'
                    current_name = f'Admin_{cfg.GROUP}_{cfg.SESSION}_{hand_tag}_Next'
                    _show(current_name)
                    break
        else:
            pygame.time.delay(10)
            continue
        break

    # Phase 4: HU (hand used), inputs L/R then ENTER => Admin_Please_L/R and wait SPACE
    cfg.UH = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            current_name = _toggle_if_esc(event, current_name)
            if event.key == pygame.K_l:
                cfg.UH = 'left'
                current_name = f'Admin_{cfg.GROUP}_{cfg.SESSION}_' + ('L' if cfg.DH=='left' else 'R') + '_L'
                _show(current_name)
            elif event.key == pygame.K_r:
                cfg.UH = 'right'
                current_name = f'Admin_{cfg.GROUP}_{cfg.SESSION}_' + ('L' if cfg.DH=='left' else 'R') + '_R'
                _show(current_name)
            elif event.key == pygame.K_RETURN:
                if cfg.UH is None:
                    logger.warning('[admin] HU not selected yet.')
                else:
                    please = 'Admin_Please_L' if cfg.UH == 'left' else 'Admin_Please_R'
                    _show(please)
                    _wait_for_key_raw_pygame(screen, getattr(paths, please), pygame.K_SPACE)
                    return screen
        else:
            pygame.time.delay(10)
            continue
        # continue loop until ENTER processed

    return screen


