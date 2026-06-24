# ./src/core/saves.py
"""
Utilities for saving trial-level experiment results to CSV files.

This module handles creation of participant-specific result files and appends one row per completed trial using a fixed column schema.
"""


from pathlib import Path
import csv
import datetime

import utils.config as cfg
from utils.paths import RESULTS_DIR
from utils.logger import get_logger

logger = get_logger("./src/core/saves")    # create logger


COLUMNS = [
    "task",
    "participant_id",       # participant id (input at the start of task)
    "language",             # English / Espanol / NA (derived from PID[0])
    "location",             # USA / MEX / NA (derived from PID[0])
    "group",                # Pilot / Ctrl / Pat / NA (derived from GROUP)
    "group_det",            # Pilot / Control / CD / Stroke / Tumor / Other / NA
    "session",              # s1-s9
    "dominant_hand",        # participant's dominant hand
    "hand_used",            # participant's used hand for task
    "mode",                 # full or demo
    "mapping",              # 1
    "trial",                # number of trials (starting from 1)
    "block",                # "practice" or "test"
    "block_type",           # practice or experimental
    "condition",            # left or right
    "difficulty",           # easy or hard
    "match",                # goal if hard, miss if easy
    "player_name",          # EW / FI / DC (derived from video filename)
    "key_correct",          # Correct answer: d or k
    "key_response",         # User's answer: d or k
    "joy_correct",          # Correct answer: left or right
    "joy_response",         # User's answer: left or right
    "correct",              # 1 = user correct,  0 = user wrong
    "reaction_time",        # reaction time
    "stimulus_path",        # file path (name) to the stimulus
    # Unique variables for task
    "cumulative_accuracy",  # cumulative accuracy up to this trial
    
    "start_time",          # start time
    "end_time",            # end time
]

JOY_COLUMNS = [
    "participant_id", "block", "block_type", "trial",
    "timestamp_ms", "axis_x", "axis_y", "angle", "direction", "video_name",
]


def create_joystick_log() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    filename = f"{cfg.PID}_SOC_joystick_{datetime.datetime.now().strftime('%Y_%m_%d')}.csv"
    csv_path = RESULTS_DIR / filename
    version = 1
    while csv_path.exists():
        version += 1
        filename = f"{cfg.PID}_SOC_joystick_{datetime.datetime.now().strftime('%Y_%m_%d')}_v{version:02d}.csv"
        csv_path = RESULTS_DIR / filename
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(JOY_COLUMNS)
    cfg.JOY_LOG_FILE = filename


def _language_from_pid(pid: str | None) -> str:
    """Derive language from first char of PID.

    - U/u -> "English"
    - M/m -> "Espanol"
    - Otherwise -> "NA"
    """
    if not pid:
        return "NA"
    first = str(pid)[0]
    if first in ("U", "u"):
        return "English"
    if first in ("M", "m"):
        return "Espanol"
    return "NA"


def _location_from_pid(pid: str | None) -> str:
    """Derive location from first char of PID: U/u -> USA, M/m -> MEX, else NA."""
    if not pid:
        return "NA"
    first = str(pid)[0]
    if first in ("U", "u"):
        return "USA"
    if first in ("M", "m"):
        return "MEX"
    return "NA"


def _player_name_from_pathname(pathname: str | None) -> str:
    """Derive player code from the first two letters of the video filename."""
    if not pathname:
        return "NA"
    prefix = Path(str(pathname)).name[:2].upper()
    return prefix if prefix in {"EW", "FI", "DC"} else "NA"


def _match_from_difficulty(difficulty: str | None) -> str:
    """Map difficulty labels to match labels used by SOC stimuli metadata."""
    value = (difficulty or "").strip().lower()
    if value == "hard":
        return "goal"
    if value == "easy":
        return "miss"
    return "NA"


def _group_label(group_value: str | int | None) -> str:
    """Return abbreviated group label from numeric GROUP input."""
    key = str(group_value).strip() if group_value is not None else ""
    return {
        "1": "Pilot",
        "2": "Ctrl",
        "3": "Pat",
        "4": "Pat",
        "5": "Pat",
        "6": "Pat",
    }.get(key, "NA")


def _group_det_label(group_value: str | int | None) -> str:
    """Return detailed group label from numeric GROUP input."""
    key = str(group_value).strip() if group_value is not None else ""
    return {
        "1": "Pilot",
        "2": "Control",
        "3": "CD",
        "4": "Stroke",
        "5": "Tumor",
        "6": "Other",
    }.get(key, "NA")

def create_save() -> None:
    """
    Create a new results CSV for the current participant, writing the header row if the file does not exist.

    File path rules:
    - Output directory: RESULTS_DIR
    - File name pattern: "cfg.{cfg.PID}_semantic_decision_results.csv"

    Side effects:
    - Creates a CSV file if missing.
    - Writes a single header row using COLUMNS.

    :return: None
    """

    # Ensure results directory exists
    RESULTS_DIR.mkdir(exist_ok=True)

    filename = f"{cfg.PID}_SOC_results_{datetime.datetime.now().strftime('%Y_%m_%d')}.csv"
    csv_path = RESULTS_DIR / filename

    version = 1
    while csv_path.exists():
        version += 1
        filename = f"{cfg.PID}_SOC_results_{datetime.datetime.now().strftime('%Y_%m_%d')}_v{version:02d}.csv"
        csv_path = RESULTS_DIR / filename

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)

    logger.info(f"Results file created at {csv_path}")
    cfg.RESULTS_FILE = filename


# TODO: Modify saved items based on needs

def update_save(
        correct: bool,
    reaction_time: int | None,
        starttime: datetime,
        endtime: datetime,
        type: str,
        block: str,
        condition: str,
        key_corr: str,
        key_resp: str,
        joy_corr: str,
        joy_resp: str,
        accuracy: float,
        difficulty: str,
        pathname: str,
    ) -> None:
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

    :param correct: Whether the response is correct, incorrect, or timeout
    :type correct: str

    :param reaction_time: Reaction time for this trial (ms), or None for timeout
    :type reaction_time: int | None

    :param stimulus_path: Path (name) to the stimulus file presented on this trial
    :type stimulus_path: str

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

    # Prepare one record
    record = {
        "task": cfg.TASK,
        "participant_id": cfg.PID,
        "language": _language_from_pid(cfg.PID),
        "location": _location_from_pid(cfg.PID),
        "group": _group_label(cfg.GROUP),
        "group_det": _group_det_label(cfg.GROUP),
        "session": cfg.SESSION or "",
        "dominant_hand": cfg.DH,
        "hand_used": cfg.UH,
        "mode": cfg.MODE,
        "mapping": cfg.MAPPING,
        "trial": next_trial_number,
        "block": block,
        "block_type": type,
        "condition": condition,
        "difficulty": difficulty,
        "match": _match_from_difficulty(difficulty),
        "player_name": _player_name_from_pathname(pathname),
        "key_correct": key_corr,
        "key_response": key_resp, 
        "joy_correct": joy_corr,
        "joy_response": joy_resp,
        "correct": correct,
        "reaction_time": reaction_time,
        "stimulus_path": pathname,
        "cumulative_accuracy": accuracy,
        "start_time": starttime,
        "end_time": endtime,
    }


    # Write record in fixed column order
    write_header = not has_header
    with csv_path.open("a", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({k: record.get(k, "") for k in COLUMNS})
    
    logger.info(f"Results file updated")


def update_joystick_log(
    block: str, block_type: str, trial: int,
    timestamp_ms: int, axis_x: float, axis_y: float,
    angle: float, direction: str, video_name: str,
) -> None:
    csv_path = RESULTS_DIR / cfg.JOY_LOG_FILE
    record = {
        "participant_id": cfg.PID,
        "block": block,
        "block_type": block_type,
        "trial": trial,
        "timestamp_ms": timestamp_ms,
        "axis_x": round(axis_x, 4),
        "axis_y": round(axis_y, 4),
        "angle": round(angle, 2),
        "direction": direction,
        "video_name": video_name,
    }
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=JOY_COLUMNS)
        w.writerow(record)
