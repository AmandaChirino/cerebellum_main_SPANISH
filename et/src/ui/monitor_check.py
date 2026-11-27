# ./src/ui/monitor_check.py
"""
Monitor check utilities.

This module detects the measures of the monitor in use, compares them with the saved reference,
and logs the system information at the start of the session.
"""


from __future__ import annotations
import json
import platform
import pygame

import utils.config as cfg
import utils.paths as paths
from utils.logger import get_logger


logger = get_logger("./src/ui/monitor_check")

# Measures that must match the reference (the OS is saved but not compared)
_COMPARED_KEYS = ("screen_w", "screen_h", "refresh_hz", "display_index", "n_displays")


def _os_version() -> str:
    """Return the operating system version."""
    if platform.system() == "Darwin":
        return platform.mac_ver()[0]
    return platform.version()


def detect_monitor(screen: pygame.Surface) -> dict:
    """
    Detect the measures of the monitor and the software in use.

    :param screen: Current display surface
    :return: Dict with the detected measures (refresh_hz is None when pygame does not expose it)
    """
    # The refresh rate is only exposed by some pygame builds
    get_hz = getattr(pygame.display, "get_current_refresh_rate", None)
    refresh_hz = get_hz() if get_hz else None
    width, height = screen.get_size()

    return {
        "screen_w": width,
        "screen_h": height,
        "refresh_hz": refresh_hz or None,
        "display_index": cfg.DISPLAY_INDEX,
        "n_displays": pygame.display.get_num_displays(),
        "os": platform.system(),
        "os_version": _os_version(),
        "pygame_version": pygame.version.ver,
        "sdl_version": ".".join(str(n) for n in pygame.get_sdl_version()),
    }


def log_system_info(screen: pygame.Surface) -> None:
    """Write the system and display information to the log."""
    m = detect_monitor(screen)
    logger.info("SYSTEM | os=%s %s | pygame=%s | sdl=%s", m["os"], m["os_version"], m["pygame_version"], m["sdl_version"])
    # Desktop sizes can be fewer than the connected monitors when a desktop is mirrored
    logger.info(
        "DISPLAYS | n_displays=%d | desktop_sizes=%s | index_used=%d | window=%dx%d | refresh_hz=%s",
        m["n_displays"], pygame.display.get_desktop_sizes(), m["display_index"],
        m["screen_w"], m["screen_h"], m["refresh_hz"] if m["refresh_hz"] else "n/a",
    )


def _load_reference() -> dict | None:
    """Load the saved monitor reference, or None if it is missing or unreadable."""
    try:
        with paths.MONITOR_REFERENCE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _save_reference(measures: dict) -> None:
    """Save the monitor measures as the new reference."""
    paths.MONITOR_REFERENCE.parent.mkdir(parents=True, exist_ok=True)
    with paths.MONITOR_REFERENCE.open("w", encoding="utf-8") as f:
        json.dump(measures, f, indent=2)


def _describe(m: dict) -> str:
    """Format the monitor measures as one line of text."""
    hz = f"{m.get('refresh_hz')} Hz" if m.get("refresh_hz") else "refresh rate n/a"
    return f"{m.get('screen_w')} x {m.get('screen_h')} px | {hz} | display {m.get('display_index')} of {m.get('n_displays')}"


def _show_message(screen: pygame.Surface, lines: list[str]) -> None:
    """Show centered large text on a black screen."""
    font = pygame.font.SysFont(None, int(screen.get_height() * 0.06))
    line_h = font.get_linesize()
    top = (screen.get_height() - line_h * len(lines)) // 2

    screen.fill(cfg.BLACK_RGB)
    for i, line in enumerate(lines):
        if not line:
            continue
        surf = font.render(line, True, cfg.WHITE_RGB)
        screen.blit(surf, surf.get_rect(midtop=(screen.get_width() // 2, top + i * line_h)))
    pygame.display.flip()


def _wait_key(valid_keys: tuple[int, ...]) -> int:
    """Wait until one of valid_keys is pressed and return it."""
    pygame.event.clear()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            if event.type == pygame.KEYDOWN and event.key in valid_keys:
                return event.key
        pygame.time.delay(10)


def show_mouse_notice(screen: pygame.Surface) -> None:
    """Remind the experimenter to keep the mouse on the display that shows the task; SPACE continues."""
    _show_message(screen, [
        "Before starting",
        "",
        "Move the mouse to the main display",
        "(the one showing this screen)",
        "Do not click",
        "",
        "Press SPACE to continue",
    ])
    _wait_key((pygame.K_SPACE,))


def check_monitor(screen: pygame.Surface) -> None:
    """
    Compare the current monitor with the saved reference and warn on screen if they differ.

    - No reference: save it and show the registered measures (SPACE continues).
    - Same measures: continue without showing anything.
    - Different measures: show both and let the experimenter exit (ESC), continue (SPACE) or update the reference (R).

    :param screen: Current display surface
    """
    current = detect_monitor(screen)
    reference = _load_reference()

    if reference is None:
        _save_reference(current)
        logger.info("Monitor reference created: %s", _describe(current))
        _show_message(screen, ["Monitor registered", "", _describe(current), "", "Press SPACE to continue"])
        _wait_key((pygame.K_SPACE,))
        return

    if all(reference.get(k) == current[k] for k in _COMPARED_KEYS):
        return

    logger.warning("Monitor differs from reference | before: %s | now: %s", _describe(reference), _describe(current))
    _show_message(screen, [
        "The monitor does not match the reference",
        "",
        "Before:",
        _describe(reference),
        "Now:",
        _describe(current),
        "",
        "ESC: exit",
        "SPACE: continue anyway",
        "R: update the reference",
    ])
    key = _wait_key((pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_r))

    if key == pygame.K_ESCAPE:
        pygame.quit()
        raise SystemExit
    if key == pygame.K_r:
        _save_reference(current)
        logger.info("Monitor reference updated: %s", _describe(current))
