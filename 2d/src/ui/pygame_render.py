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
from utils.stimuli_conditions import mapping_from_pid
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

    flags = pygame.FULLSCREEN if cfg._is_fullscreen else 0
    screen = pygame.display.set_mode(
        (cfg.SCREEN_W, cfg.SCREEN_H), flags, vsync=1
    )
    pygame.display.set_caption("2d")
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


def _compute_mapping_from_pid(pid: str | None) -> int:
    """
    Compute MAPPING from PID suffix.
    - Even trailing digit (or no digits): mapping 2
    - Odd trailing digit: mapping 1
    """
    return mapping_from_pid(pid)


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
    Show Admin.png page and collect participant ID via keyboard input.

    Behavior change per spec:
    - Use Admin.png (variable `Admin`) instead of legacy `ADMIN_1`.
    - After PID is confirmed with [Enter], compute mapping using existing rule
      and immediately flip to `Admin_next` before continuing the admin flow
      (group ? session ? DH ? UH).
    """
    def _admin_img(name: str) -> Path:
        img = getattr(paths, name, None)
        if img is None:
            logger.warning(f"[get_participant_id] Missing admin image var: {name}")
            return paths.ADMIN_DIR / f"{name}.png"
        return img

    font = pygame.font.SysFont(None, cfg.FONT_SMALL)
    input_text = ""
    admin_bg = _play_admin_image(screen, _admin_img("Admin"))

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
                admin_bg = _play_admin_image(screen, _admin_img("Admin"))
                continue

            if event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
                continue

            if event.key == pygame.K_RETURN:
                if input_text.strip():
                    # Keep PID and mapping logic intact
                    cfg.PID = input_text.strip()
                    cfg.MAPPING = _compute_mapping_from_pid(cfg.PID)

                    # Flip to Admin_next then continue admin phases
                    _play_admin_image(screen, _admin_img("Admin_next"))
                    screen = _run_admin_phases(screen)
                    return screen
                continue

            if event.unicode:
                input_text += "".join(ch for ch in event.unicode if ch.isprintable())

        pygame.time.delay(10)



def _compute_mapping() -> None:
    """
    Backward-compatible wrapper for existing callers.
    """
    cfg.MAPPING = _compute_mapping_from_pid(cfg.PID)



# record_hands has been fully removed per new admin spec.


def _run_admin_phases(screen: pygame.Surface) -> pygame.Surface:
    """
    Admin phases replicated to match reference behavior:
    1) GROUP: digits 1-6; Enter -> Admin_{G}_Next; digits redraw Admin_{G}
    2) SESSION: digits 1-6; Enter -> Admin_{G}_{S}_Next; digits redraw Admin_{G}_{S}
    3) DH: L/R; Enter -> Admin_{G}_{S}_{L|R}_Next; L/R redraw Admin_{G}_{S}_{L|R}
    4) UH: L/R; Enter -> Admin_Please_L/Admin_Please_R; Space to continue
    """
    def _admin_img(name: str) -> Path:
        img = getattr(paths, name, None)
        if img is None:
            logger.warning(f"[_run_admin_phases] Missing admin image var: {name}")
            return paths.ADMIN_DIR / f"{name}.png"
        return img

    def _repaint(name: str):
        place_image(screen, _admin_img(name), fit_mode="contain", max_fraction=0.9)
        pygame.display.flip()

    def _toggle_if_escape(current: str) -> str:
        pygame.event.clear()
        nonlocal screen
        screen = toggle_full_screen(screen)
        pygame.event.clear()
        _repaint(current)
        return current

    def _is_enter(k: int) -> bool:
        return k in (pygame.K_RETURN, pygame.K_KP_ENTER)

    def _hand_letter(val: str | None) -> str:
        return 'L' if val == 'left' else 'R'

    # Phase 1: GROUP on Admin_next
    current_name = "Admin_next"
    _repaint(current_name)

    cfg.GROUP = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                current_name = _toggle_if_escape(current_name); continue
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                d = chr(event.key)
                cfg.GROUP = d
                current_name = f"Admin_{cfg.GROUP}"
                _repaint(current_name); continue
            if _is_enter(event.key):
                if cfg.GROUP is None:
                    logger.warning('[admin] GROUP not selected; press 1-6 before Enter.'); continue
                current_name = f"Admin_{cfg.GROUP}_Next"
                _repaint(current_name); break
        else:
            pygame.time.delay(10); continue
        break

    # Phase 2: SESSION on Admin_{G}_Next
    cfg.SESSION = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                current_name = _toggle_if_escape(current_name); continue
            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6):
                d = chr(event.key)
                cfg.SESSION = d
                current_name = f"Admin_{cfg.GROUP}_{d}"
                _repaint(current_name); continue
            if _is_enter(event.key):
                if cfg.SESSION is None:
                    logger.warning('[admin] SESSION not selected; press 1-6 before Enter.'); continue
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_Next"
                _repaint(current_name); break
        else:
            pygame.time.delay(10); continue
        break

    # Phase 3: DH on Admin_{G}_{S}_Next
    cfg.DH = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                current_name = _toggle_if_escape(current_name); continue
            if event.key == pygame.K_l:
                cfg.DH = 'left'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}"
                _repaint(current_name); continue
            if event.key == pygame.K_r:
                cfg.DH = 'right'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}"
                _repaint(current_name); continue
            if _is_enter(event.key):
                if not cfg.DH:
                    logger.warning('[admin] DH not selected; press L/R before Enter.'); continue
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}_Next"
                _repaint(current_name); break
        else:
            pygame.time.delay(10); continue
        break

    # Phase 4: UH on Admin_{G}_{S}_{D}_Next
    cfg.UH = None
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                current_name = _toggle_if_escape(current_name); continue
            if event.key == pygame.K_l:
                cfg.UH = 'left'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}_{_hand_letter(cfg.UH)}"
                _repaint(current_name); continue
            if event.key == pygame.K_r:
                cfg.UH = 'right'
                current_name = f"Admin_{cfg.GROUP}_{cfg.SESSION}_{_hand_letter(cfg.DH)}_{_hand_letter(cfg.UH)}"
                _repaint(current_name); continue
            if _is_enter(event.key):
                if not cfg.UH:
                    logger.warning('[admin] UH not selected; press L/R before Enter.'); continue
                please_name = 'Admin_Please_L' if cfg.UH == 'left' else 'Admin_Please_R'
                _repaint(please_name)
                # Wait for [Space]
                while True:
                    ev = pygame.event.wait()
                    if ev.type == pygame.QUIT:
                        pygame.quit(); raise SystemExit
                    if ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE:
                            screen = toggle_full_screen(screen); _repaint(please_name); continue
                        if ev.key == pygame.K_SPACE:
                            return screen
        else:
            pygame.time.delay(10); continue

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


def place_mapping_background(screen: pygame.Surface) -> None:
    """
    Draw mapping image as background using contain-fit scaling, then center it.

    Scale rule follows:
    ratio = min(mapping_width / screen_width, mapping_height / screen_height)
    target_size = (mapping_width / ratio, mapping_height / ratio)
    """
    mapping_img_path = paths.load_mapping_image()
    if not mapping_img_path.exists():
        logger.error(f"[place_mapping_background] Mapping image not found -> {mapping_img_path}")
        return

    try:
        img = pygame.image.load(str(mapping_img_path)).convert_alpha()
    except Exception as e:
        logger.error(f"[place_mapping_background] Failed to load mapping image -> {mapping_img_path} | {e}")
        return

    screen_w, screen_h = screen.get_size()
    map_w, map_h = img.get_size()

    if map_w <= 0 or map_h <= 0:
        logger.error(f"[place_mapping_background] Invalid mapping image size -> {(map_w, map_h)}")
        return

    ratio = min(map_w / screen_w, map_h / screen_h)
    if ratio <= 0:
        logger.error(f"[place_mapping_background] Invalid ratio -> {ratio}")
        return

    target_w = int(map_w / ratio)
    target_h = int(map_h / ratio)
    scaled = pygame.transform.smoothscale(img, (target_w, target_h))

    screen.fill(cfg.BLACK_RGB)
    rect = scaled.get_rect(center=(screen_w // 2, screen_h // 2))
    screen.blit(scaled, rect)


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
        text_surf = font.render("Muy lento", True, cfg.YELLOW_RGB)
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
