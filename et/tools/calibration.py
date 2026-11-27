# ./tools/calibration.py
"""
Cursor travel calibration. Run it by hand when the computer, monitor or pointing device changes.

The task never imports this file. A known physical distance is marked on the pad with two pieces of tape;
the script counts how many pixels the cursor moves over that distance, so computers can be compared.

Tests (3 repetitions each, SPACE starts and ends every repetition):
- lento:  slide from mark to mark in about 3 seconds.
- rapido: same distance in half a second.
- borde:  push against the end of the bar for 3 seconds with the real task behaviour (MouseCordDot clamp).

Run from the emotional_tracking folder:  python tools/calibration.py
"""


from __future__ import annotations
import csv
import datetime
import re
import sys
import time
from pathlib import Path

# Make the task modules (utils, ui, core) importable when this file is run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pygame

import utils.config as cfg
import utils.paths as paths
import ui.monitor_check as monitor_check
from ui.monitor_check import _show_message, check_monitor, detect_monitor, log_system_info
from ui.pygame_render import init_display
from core.mouseCordDot import MouseCordDot
from core.stimulus import _draw_slider


LOOP_FPS = 25           # loop rate while measuring, similar to the task
N_REPETITIONS = 3
MAX_ATTEMPTS = 3
TESTS = ("lento", "rapido", "borde")

CALIBRATION_DIR = paths.RESULTS_DIR / "calibration"

COLUMNS = [
    "computer", "os", "os_version", "date", "screen_w", "screen_h", "display_index", "refresh_hz",
    "pygame_version", "sdl_version", "distance_cm", "test_type", "repetition",
    "px_net",           # net horizontal pixels moved (empty in borde)
    "duration_s",       # swipe duration from the first to the last motion event
    "px_per_cm",        # px_net / distance_cm (empty in borde)
    "motion_events",    # mouse motion events between the two SPACE presses
    "duration_total_s", # seconds between the two SPACE presses (empty in borde)
    "px_per_s",         # px_net / duration_s (empty in borde)
]

SERIES_COLUMNS = ["t_ms", "x", "x_raw", "motion_events_cum"]

INSTRUCTIONS = {
    "lento": [
        "Place your finger on the left mark on the pad.",
        "Press SPACE and slide to the right mark in about 3 seconds.",
        "Press SPACE again when finished.",
    ],
    "rapido": [
        "Place your finger on the left mark on the pad.",
        "Press SPACE and slide to the right mark in about half a second.",
        "Press SPACE again when finished.",
    ],
    "borde": [
        "Push toward one end of the bar, hold for 3 seconds, then return.",
        "Press SPACE to start and SPACE again when finished.",
    ],
}

_font: pygame.font.Font | None = None
_font_size: int = 0


def _quit() -> None:
    """Close pygame and exit; rows already measured stay in the results file."""
    pygame.quit()
    raise SystemExit


def _check_quit(event: pygame.event.Event) -> None:
    """Exit on window close or ESC."""
    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
        _quit()


def _ask(screen: pygame.Surface, prompt: str, parse) -> object:
    """Ask for a typed value on screen; parse returns the value or None when it is not valid."""
    text = ""
    message = "ENTER: confirm | ESC: quit"
    dirty = True
    while True:
        if dirty:
            _show_message(screen, [prompt, "", text + "_", "", message])
            dirty = False
        for event in pygame.event.get():
            _check_quit(event)
            if event.type != pygame.KEYDOWN:
                continue
            dirty = True
            if event.key == pygame.K_BACKSPACE:
                text = text[:-1]
                message = "ENTER: confirm | ESC: quit"
            elif event.key == pygame.K_RETURN:
                value = parse(text.strip())
                if value is not None:
                    return value
                message = "Invalid value"
            elif event.unicode and event.unicode.isprintable():
                text += event.unicode
                message = "ENTER: confirm | ESC: quit"
        pygame.time.delay(10)


def _parse_name(text: str) -> str | None:
    """Computer name safe for file names, or None if empty."""
    name = re.sub(r"[^A-Za-z0-9_-]", "_", text)
    return name or None


def _parse_distance(text: str) -> float | None:
    """Distance in cm (comma or point as decimal separator), or None if not a positive number."""
    try:
        value = float(text.replace(",", "."))
    except ValueError:
        return None
    return value if value > 0 else None


def _draw_test_screen(screen: pygame.Surface, dot_x: float, lines: list[str]) -> None:
    """Draw the task bar with the dot at dot_x and text lines above it."""
    global _font, _font_size
    w, h = screen.get_size()
    size = int(h * 0.045)
    if _font is None or size != _font_size:
        _font = pygame.font.SysFont(None, size)
        _font_size = size

    screen.fill(cfg.BLACK_RGB)
    _draw_slider(screen, dot_x)
    for i, line in enumerate(lines):
        surf = _font.render(line, True, cfg.WHITE_RGB)
        screen.blit(surf, surf.get_rect(midtop=(w // 2, int(h * 0.06) + i * _font.get_linesize())))
    pygame.display.flip()


def _wait_space(screen: pygame.Surface, dot: MouseCordDot, lines: list[str]) -> float:
    """Show the instructions with the bar until SPACE is pressed and return its time."""
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            _check_quit(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return time.perf_counter()
        _draw_test_screen(screen, dot.get_pos()[0], lines)
        clock.tick(LOOP_FPS)


def _measure_swipe(
    screen: pygame.Surface, dot: MouseCordDot, lines: list[str]
) -> tuple[dict | None, str | None]:
    """
    Measure net horizontal pixels and motion duration between the first and last motion events.

    The cursor is placed near the left screen edge before the repetition, never during it. Placement
    events are cleared before SPACE starts the measure. MouseCordDot clamp is not applied.
    """
    width = screen.get_width()
    pygame.mouse.set_pos((5, screen.get_height() // 2))
    start_time = _wait_space(screen, dot, lines)
    pygame.event.clear(pygame.MOUSEMOTION)

    px_x = 0
    events = 0
    touched_edge = False
    first_motion_time = None
    last_motion_time = None
    first_motion_clock = None
    last_motion_clock = None
    clock = pygame.time.Clock()
    end_time = None
    while True:
        done = False
        for event in pygame.event.get():
            _check_quit(event)
            if event.type == pygame.MOUSEMOTION:
                event_time = getattr(event, "timestamp", None)
                if isinstance(event_time, (int, float)):
                    if first_motion_time is None:
                        first_motion_time = event_time
                    last_motion_time = event_time
                else:
                    event_clock = time.perf_counter()
                    if first_motion_clock is None:
                        first_motion_clock = event_clock
                    last_motion_clock = event_clock
                px_x += event.rel[0]
                events += 1
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                done = True
                end_time = time.perf_counter()
        mouse_x = pygame.mouse.get_pos()[0]
        touched_edge = touched_edge or mouse_x <= 0 or mouse_x >= width - 1
        if done:
            break
        _draw_test_screen(screen, dot.get_pos()[0], lines[:1] + ["Measuring... Press SPACE when finished"])
        clock.tick(LOOP_FPS)

    if touched_edge:
        return None, "edge"
    if events < 2:
        return None, "too_few_events"

    if first_motion_time is not None and last_motion_time is not None:
        duration_s = (last_motion_time - first_motion_time) / 1000
    elif first_motion_clock is not None and last_motion_clock is not None:
        duration_s = last_motion_clock - first_motion_clock
    else:
        return None, "too_few_events"
    if duration_s <= 0 or end_time is None:
        return None, "too_few_events"

    px_net = abs(px_x)
    duration_total_s = end_time - start_time
    return {
        "px_net": px_net,
        "duration_s": duration_s,
        "duration_total_s": duration_total_s,
        "px_per_s": px_net / duration_s,
        "motion_events": events,
    }, None


def _measure_edge(screen: pygame.Surface, dot: MouseCordDot, lines: list[str]) -> tuple[dict, list]:
    """
    Push against the end of the bar with the real task behaviour (MouseCordDot clamp each frame).

    Counts every mouse motion event, including the ones the clamp itself causes when it puts the
    cursor back. Returns the measures and the series (t_ms, x, x_raw, motion_events_cum).
    """
    dot.set_pos((0.0, 0.0))
    _wait_space(screen, dot, lines)
    pygame.event.clear(pygame.MOUSEMOTION)

    events = 0
    series = []
    clock = pygame.time.Clock()
    start = time.perf_counter()
    while True:
        done = False
        for event in pygame.event.get():
            _check_quit(event)
            if event.type == pygame.MOUSEMOTION:
                events += 1
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                done = True
        if done:
            break
        x_raw = dot.get_pos()[0]
        x = dot.clamp(limit=1.0)[0]
        series.append((round((time.perf_counter() - start) * 1000, 1), round(x, 4), round(x_raw, 4), events))
        _draw_test_screen(screen, x, lines[:1] + ["Measuring... Press SPACE when finished"])
        clock.tick(LOOP_FPS)
    duration_s = time.perf_counter() - start

    return {"duration_s": duration_s, "motion_events": events}, series


def _new_results_path(computer: str) -> Path:
    """Results file path for this computer and date; a _vNN suffix avoids overwriting."""
    CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.datetime.now().strftime("%Y_%m_%d")
    path = CALIBRATION_DIR / f"calibration_{computer}_{date}.csv"
    version = 1
    while path.exists():
        version += 1
        path = CALIBRATION_DIR / f"calibration_{computer}_{date}_v{version:02d}.csv"
    return path


def _append_row(path: Path, row: dict) -> None:
    """Append one repetition row, writing the header when the file is new."""
    new_file = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def _write_series(path: Path, series: list) -> None:
    """Save the x positions of one borde repetition."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SERIES_COLUMNS)
        writer.writerows(series)


def _mean(values: list[float]) -> float | None:
    """Average of values, or None when empty."""
    return sum(values) / len(values) if values else None


def _fmt(value: float | None) -> str:
    """One decimal, or n/d when missing."""
    return "n/a" if value is None else f"{value:.1f}"


def _show_summary(screen: pygame.Surface, rows: list[dict], results_path: Path) -> None:
    """Show the summary on screen and wait for any key."""
    def values(test: str, key: str) -> list[float]:
        return [r[key] for r in rows if r["test_type"] == test and r[key] not in ("", None)]

    slow_cm = _mean(values("lento", "px_per_cm"))
    fast_cm = _mean(values("rapido", "px_per_cm"))
    ratio = fast_cm / slow_cm if slow_cm and fast_cm is not None else None
    slow_px = _mean(values("lento", "px_net"))
    slow_duration = _mean(values("lento", "duration_s"))
    fast_duration = _mean(values("rapido", "duration_s"))
    edge_events = _mean(values("borde", "motion_events"))
    bar_px = 2 * cfg.SLIDER_HALF_LENGTH * screen.get_height()
    monitor = detect_monitor(screen)
    refresh_hz = monitor["refresh_hz"]

    _show_message(screen, [
        "Calibration complete",
        "",
        f"Screen: {screen.get_width()} x {screen.get_height()} px",
        f"Refresh: {refresh_hz or 'n/a'} Hz | Display: {monitor['display_index']}",
        f"Slow duration average: {_fmt(slow_duration)} s | Fast duration average: {_fmt(fast_duration)} s",
        f"Slow px/cm (average): {_fmt(slow_cm)}",
        f"Fast px/cm (average): {_fmt(fast_cm)}",
        f"Fast / slow ratio: {'n/a' if ratio is None else f'{ratio:.2f}'}",
        f"Slow net pixels (average): {_fmt(slow_px)} | Bar length: {bar_px:.0f} px",
        f"Edge-test mouse events (average): {_fmt(edge_events)}",
        "",
        f"File: {results_path.name}",
        "Press any key to close",
    ])
    pygame.event.clear()
    while True:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN):
                return
        pygame.time.delay(10)


def main() -> None:
    pygame.init()
    screen = init_display()
    original_show_message = monitor_check._show_message

    def show_monitor_message(surface: pygame.Surface, lines: list[str]) -> None:
        replacements = {
            "Monitor registrado": "Monitor registered",
            "Presiona ESPACIO para continuar": "Press SPACE to continue",
            "El monitor no coincide con la referencia": "Monitor differs from reference",
            "Antes:": "Before:",
            "Ahora:": "Now:",
            "ESC: salir": "ESC: quit",
            "ESPACIO: continuar de todas formas": "SPACE: continue anyway",
            "R: actualizar la referencia": "R: update reference",
            "refresco n/d": "refresh n/a",
        }
        translated = []
        for line in lines:
            for source, target in replacements.items():
                line = line.replace(source, target)
            line = line.replace("pantalla ", "display ").replace(" de ", " of ")
            translated.append(line)
        original_show_message(surface, translated)

    monitor_check._show_message = show_monitor_message
    try:
        check_monitor(screen)
    finally:
        monitor_check._show_message = original_show_message
    log_system_info(screen)
    pygame.mouse.set_visible(False)

    computer = _ask(screen, "Computer name:", _parse_name)
    distance_cm = _ask(screen, "Distance between the two pad marks (cm):", _parse_distance)

    monitor = detect_monitor(screen)
    results_path = _new_results_path(computer)
    common = {
        "computer": computer,
        "os": monitor["os"],
        "os_version": monitor["os_version"],
        "date": datetime.date.today().isoformat(),
        "screen_w": monitor["screen_w"],
        "screen_h": monitor["screen_h"],
        "display_index": monitor["display_index"],
        "refresh_hz": monitor["refresh_hz"],
        "pygame_version": monitor["pygame_version"],
        "sdl_version": monitor["sdl_version"],
        "distance_cm": distance_cm,
    }

    dot = MouseCordDot(screen)
    rows = []
    for test_number, test in enumerate(TESTS, start=1):
        for repetition in range(1, N_REPETITIONS + 1):
            test_label = {"lento": "SLOW", "rapido": "FAST", "borde": "EDGE"}[test]
            header = f"Test {test_number} of {len(TESTS)}: {test_label} - repetition {repetition} of {N_REPETITIONS}"
            lines = [header] + INSTRUCTIONS[test]

            if test == "borde":
                measures, series = _measure_edge(screen, dot, lines)
                series_path = results_path.with_name(f"{results_path.stem}_borde_rep{repetition}.csv")
                _write_series(series_path, series)
                px_net, px_per_cm = "", ""
                duration_total_s, px_per_s = "", ""
            else:
                measures = None
                failure_reason = None
                for attempt in range(1, MAX_ATTEMPTS + 1):
                    attempt_lines = [header]
                    if failure_reason == "edge":
                        attempt_lines.append("The cursor reached the screen edge. Please repeat.")
                    elif failure_reason == "too_few_events":
                        attempt_lines.append("Too few motion events to measure. Please repeat.")
                    if attempt > 1:
                        attempt_lines.append(f"Attempt {attempt} of {MAX_ATTEMPTS}")
                    attempt_lines += INSTRUCTIONS[test]
                    measures, failure_reason = _measure_swipe(screen, dot, attempt_lines)
                    if measures is not None:
                        break

                if measures is None:
                    if failure_reason == "edge":
                        failure_lines = [
                            "The cursor keeps reaching the screen edge.",
                            "The device moves too many pixels for this distance.",
                            "Run the script again with closer marks,",
                            "for example, half the current distance.",
                            "",
                            "Press ESC to exit. Existing results are kept.",
                        ]
                    else:
                        failure_lines = [
                            "This swipe could not be measured: fewer than two",
                            "motion events, or zero measured duration.",
                            "",
                            "Press ESC to exit. Existing results are kept.",
                        ]
                    _show_message(screen, failure_lines)
                    while True:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT or (
                                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                            ):
                                pygame.quit()
                                return
                        pygame.time.delay(10)
                px_net = measures["px_net"]
                px_per_cm = px_net / distance_cm
                duration_total_s = round(measures["duration_total_s"], 3)
                px_per_s = measures["px_per_s"]

            row = {
                **common,
                "test_type": test,
                "repetition": repetition,
                "px_net": px_net,
                "duration_s": round(measures["duration_s"], 3),
                "px_per_cm": px_per_cm,
                "motion_events": measures["motion_events"],
                "duration_total_s": duration_total_s,
                "px_per_s": px_per_s,
            }
            rows.append(row)
            _append_row(results_path, row)

    _show_summary(screen, rows, results_path)
    pygame.quit()


if __name__ == "__main__":
    main()
