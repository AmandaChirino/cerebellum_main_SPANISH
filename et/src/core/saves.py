# ./src/core/saves.py
"""
Utilities for saving trial-level experiment results to CSV files.

This module handles creation of participant-specific result files and appends one row per completed trial using a fixed column schema.
"""


from pathlib import Path
import csv
import datetime
import json
import pygame

import utils.config as cfg
from ui.monitor_check import detect_monitor
from utils.paths import RESULTS_DIR
from utils.logger import get_logger


logger = get_logger("./src/core/saves")    # create logger

NA_STR = "NA"


COLUMNS = [
    "task",
    "participant_id",       # participant id (input at the start of task)
    "language",
    "location",
    "group",
    "group_det",
    "session",
    "dominant_hand",        # participant's dominant hand
    "hand_used",            # participant's less affected hand
    "mode",
    "mapping",
    "trial",                # number of trials (starting from 1)
    "block",                # "practice" or "test"
    "block_type",
    "condition",            # full_visible
    "key_correct",
    "key_response", 
    "joy_correct",
    "joy_response",
    "correct",              # "correct" / "incorrect" / "timeout"
    "stimulus",             # video filename without directory or extension
    "stimulus_path",        # file path (name) to the stimulus
    "start_time",           # global start time
    "end_time",             # global end time
    "frame_from_time",     # video frame number estimated from the elapsed time, one per sample
    "time_ms",              # real ms since the video started, one per sample
    "x_pos",
    "y_pos",
    "screen_w",             # real screen width in pixels
    "screen_h",             # real screen height in pixels
    "refresh_hz",           # monitor refresh rate (empty if pygame does not expose it)
    "display_index",        # display where the window opened
    "n_displays",           # number of connected displays
    "os",
    "os_version",
    "pygame_version",
    "sdl_version",
    "video_fps",            # frames per second of the video
    "n_samples",            # video frames actually read
    "video_frames_expected",
    "duration_expected_s",
    "duration_actual_s",
    "playback_ratio",       # duration_actual_s / duration_expected_s
]

def create_save() -> None:
    """
    Create a new results CSV for the current participant, writing the header row if the file does not exist.

    File path rules:
    - Output directory: RESULTS_DIR
    - File name pattern: "cfg.{cfg.PID}_template_results.csv" (TODO: replace "template" with actual project name)

    Side effects:
    - Creates a CSV file if missing.
    - Writes a single header row using COLUMNS.

    :return: None
    """
    RESULTS_DIR.mkdir(exist_ok=True)
    filename = f"{cfg.PID}_ET_results_{datetime.datetime.now().strftime('%Y_%m_%d')}.csv"
    csv_path = RESULTS_DIR / filename

    version = 1
    while csv_path.exists():
        version += 1
        filename = f"{cfg.PID}_ET_results_{datetime.datetime.now().strftime('%Y_%m_%d')}_v{version:02d}.csv"
        csv_path = RESULTS_DIR / filename
    
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
    
    logger.info(f"Results file created at {csv_path}")
    cfg.RESULTS_FILE = filename
    _wide_columns.clear()


def _list_cell(values, decimals: int | None = None) -> str:
    """Serialise a sequence of numbers as a JSON list (e.g. "[0.1, 0.25]") so it fits in one CSV cell."""
    if decimals is None:
        return json.dumps([int(v) for v in values])
    return json.dumps([round(float(v), decimals) for v in values])


def _round_or_none(value, decimals: int):
    """Round a number, keeping None (empty cell) when the value is missing."""
    return None if value is None else round(float(value), decimals)


def _language_from_pid(pid: str | None) -> str:
    """Match 2D's shared PID rule: U/u -> English, M/m -> Spanish, otherwise NA."""
    if not pid:
        return NA_STR
    first = str(pid)[0]
    if first in ("U", "u"):
        return "English"
    if first in ("M", "m"):
        return "Spanish"
    return NA_STR


def _location_from_pid(pid: str | None) -> str:
    """Derive location from PID: U/u -> USA, M/m -> MEX, otherwise NA."""
    if not pid:
        return NA_STR
    first = str(pid)[0]
    if first in ("U", "u"):
        return "USA"
    if first in ("M", "m"):
        return "MEX"
    return NA_STR


def _group_label(group) -> str:
    """Return the shared abbreviated group label."""
    try:
        value = int(group)
    except (TypeError, ValueError):
        return NA_STR
    if value == 1:
        return "Pilot"
    if value == 2:
        return "Ctrl"
    if 3 <= value <= 6:
        return "Pat"
    return NA_STR


def _group_det_label(group) -> str:
    """Return the detailed label for the selected admin group."""
    labels = {1: "Pilot", 2: "Control", 3: "CD", 4: "Stroke", 5: "Tumor", 6: "Other"}
    try:
        return labels.get(int(group), NA_STR)
    except (TypeError, ValueError):
        return NA_STR


# Columns of the second results file: one (name, values) pair per video column
_wide_columns: list[tuple[str, list[float]]] = []


def _update_wide_save(stimulus_path: str, x_pos: list, y_pos: list) -> None:
    """
    Rewrite the second results file with one y/arousal and one x/valence column per video.

    Rows are the video frames in reading order (video_frame starts at 0); shorter videos are padded with empty cells.
    Arousal is y_pos and valence is x_pos.

    :param stimulus_path: Path (name) of the video; its file name without extension names the columns
    :param x_pos: x positions of the trial, one per video frame
    :param y_pos: y positions of the trial, one per video frame
    """
    video = Path(stimulus_path).stem
    _wide_columns.append((f"{video}_arousal_y", [float(v) for v in y_pos]))
    _wide_columns.append((f"{video}_valence_x", [float(v) for v in x_pos]))

    # Same name as the main results file, so the _vNN suffix matches
    filename = cfg.RESULTS_FILE.replace("_ET_results_", "_ET_wide_", 1)
    n_rows = max(len(values) for _, values in _wide_columns)

    with (RESULTS_DIR / filename).open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["video_frame"] + [name for name, _ in _wide_columns])
        for i in range(n_rows):
            writer.writerow([i] + [values[i] if i < len(values) else "" for _, values in _wide_columns])


# TODO: Modify saved items based on needs

def update_save(        
        correct: bool,
        stimulus_path: str,
        starttime: datetime,
        endtime: datetime,
        type: str,
        block: str,
        frame_from_time: list,
        x_pos: list,
        y_pos: list,
        key_corr: str,
        key_resp: str,
        joy_corr: str,
        joy_resp: str,
        playback: dict,) -> None:
    """
    Append one trial result to the participant's results CSV.

    Behavior:
    - Ensures the CSV exists (calls create_save() if missing).
    - Computes the next trial_number by counting existing data rows (excluding header if present).
    - Appends a single row using the fixed column order defined in COLUMNS.

    Field mapping:
    - participant_id: cfg.PID
    - version: cfg.VERSION
    - trial_number: auto-incremented starting from 1
    - start_time: cfg.START_TIME
    - end_time: current timestamp (ISO format)

    :param phase: Trial phase label (e.g., "practice" or "test")
    :type phase: str

    :param condition: Condition label (template may use "NA")
    :type condition: str

    :param difficulty: Difficulty label (template may use "NA")
    :type difficulty: str

    :param correct: Whether the response is correct, incorrect, or timeout
    :type correct: str

    :param reaction_time: Reaction time for this trial (unit determined by caller; typically ms)
    :type reaction_time: int

    :param stimulus_path: Path (name) to the stimulus file presented on this trial
    :type stimulus_path: str

    :param playback: Playback data returned by play_video (time_ms, n_samples, video_fps, expected/actual duration, playback_ratio)
    :type playback: dict

    :return: None
    """
    csv_path = RESULTS_DIR / cfg.RESULTS_FILE

    # Count existing trials (exclude header)
    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        rows = list(reader)
        has_header = bool(rows) and rows[0] == COLUMNS
        data_rows = rows[1:] if has_header else rows
        next_trial_number = len(data_rows) + 1

    # Monitor and software measures detected right now
    monitor = detect_monitor(pygame.display.get_surface())

    # Prepare one record
    record = {
        "task": cfg.TASK,
        "participant_id": cfg.PID,
        "language": _language_from_pid(cfg.PID),
        "location": _location_from_pid(cfg.PID),
        "group": _group_label(cfg.GROUP),
        "group_det": _group_det_label(cfg.GROUP),
        "session": cfg.SESSION or NA_STR,
        "dominant_hand": cfg.DH,
        "hand_used": cfg.UH,
        "mode": cfg.MODE,
        "mapping": cfg.stimulus_set,
        "trial": next_trial_number,
        "block": block,
        "block_type": type,
        "condition": "full_visible",
        "key_correct": key_corr,
        "key_response": key_resp, 
        "joy_correct": joy_corr,
        "joy_response": joy_resp,
        "correct": correct,
        "stimulus": Path(stimulus_path).stem,
        "stimulus_path": stimulus_path,
        "start_time": starttime,
        "end_time": endtime,
        "frame_from_time": _list_cell(frame_from_time),
        "time_ms": _list_cell(playback["time_ms"], decimals=1),
        "x_pos": _list_cell(x_pos, decimals=4),
        "y_pos": _list_cell(y_pos, decimals=4),
        "screen_w": monitor["screen_w"],
        "screen_h": monitor["screen_h"],
        "refresh_hz": monitor["refresh_hz"],
        "display_index": monitor["display_index"],
        "n_displays": monitor["n_displays"],
        "os": monitor["os"],
        "os_version": monitor["os_version"],
        "pygame_version": monitor["pygame_version"],
        "sdl_version": monitor["sdl_version"],
        "video_fps": _round_or_none(playback["video_fps"], 3),
        "n_samples": playback["n_samples"],
        "video_frames_expected": playback["video_frames_expected"],
        "duration_expected_s": _round_or_none(playback["duration_expected_s"], 3),
        "duration_actual_s": _round_or_none(playback["duration_actual_s"], 3),
        "playback_ratio": _round_or_none(playback["playback_ratio"], 4),
    }

    # Write record in fixed column order
    write_header = not has_header
    with csv_path.open("a", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({k: record.get(k, "") for k in COLUMNS})
    
    _update_wide_save(stimulus_path, x_pos, y_pos)
    logger.info(f"Results file updated")
