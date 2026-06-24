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
    "task",                 # task name (abbreviation)
    "participant_id",       # participant ID (input at the start of task)
    "language",             # English / Espanol / NA (derived from first char of PID)
    "location",             # USA / MEX / NA (derived from PID[0])
    "group",                # group abbreviated (Pilot / Ctrl / Pat)
    "group_det",            # group detailed (Pilot / Control / CD / Stroke / Tumor / Other)
    "session",              # session (1..6)
    "dominant_hand",        # participant's dominant hand (left / right)
    "hand_used",            # hand used during task (left / right)
    "mode",                 # task mode (demo / full)
    "mapping",              # task mapping (1 / 2)
    "trial",                # trial index
    "block",                # block name
    "trial_type",           # trial type (practice / experimental)
    "condition",            # characteristic(s) specific to the task
    "key_correct",          # keyboard response expected (key name)
    "key_response",         # keyboard response recieved (key name)
    "joy_correct",          # joystick response expected (up / down / left / right)
    "joy_response",         # joystick response recieved (up / down / left / right)
    "correct",              # trial result (1 = correct / 0 = incorrect / None = timeout)
    # ------ Specific to task ---------
    "tap_num",
    "pace_ms",
    "synch_sound_ticks",
    "response_ticks",
    "intervals",
    "trial_outcome",        # valid / invalid based on IRI ranges
    # ------ Moved to end ---------
    "stimulus_path",        # file path (name) to the stimulus
    "start_time",           # start time of the current block (ISO format)
    "end_time",             # end time of the current block (ISO format)
]


def _language_from_pid(pid: str | None) -> str:
    """Derive language from first char of PID: U/u -> English, M/m -> Espanol, else NA."""
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
    - File name pattern: "cfg.{cfg.PID}_template_results.csv" (TODO: replace "template" with actual project name)

    Side effects:
    - Creates a CSV file if missing.
    - Writes a single header row using COLUMNS.

    :return: None
    """
    RESULTS_DIR.mkdir(exist_ok=True)
    filename = f"{cfg.PID}_TAP_results_{datetime.datetime.now().strftime('%Y_%m_%d')}.csv"
    csv_path = RESULTS_DIR / filename

    version = 1
    while csv_path.exists():
        version += 1
        filename = f"{cfg.PID}_TAP_results_{datetime.datetime.now().strftime('%Y_%m_%d')}_v{version:02d}.csv"
        csv_path = RESULTS_DIR / filename
    
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
    
    logger.info(f"Results file created at {csv_path}")
    cfg.RESULTS_FILE = filename


# TODO: Modify saved items based on needs

def update_save(
        type: str,
        block: str,
        correct: bool,
        starttime: datetime,
        endtime: datetime,
        key_corr: str,
        key_resp: str,
        intervals: int,
        pace_ms: int,
        synch_sound_ticks: int,
        response_ticks: int,
        trial: int,
        tap_num: int,
        tap_type: str,
        trial_outcome: str,
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

    :param difficulty: Difficulty label (template may use "NA")
    :type difficulty: str

    :param correct: Whether the response is correct, incorrect, or timeout
    :type correct: str

    :param reaction_time: Reaction time for this trial (unit determined by caller; typically ms)
    :type reaction_time: int

    :param stimulus_path: Path (name) to the stimulus file presented on this trial
    :type stimulus_path: str

    :return: None
    """
    csv_path = RESULTS_DIR / cfg.RESULTS_FILE

    # Check if header exists
    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        rows = list(reader)
        has_header = bool(rows) and rows[0] == COLUMNS

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
        "mapping": "1",
        "trial": trial,
        "block": block,
        "trial_type": type,
        "condition": tap_type,
        "key_correct": key_corr,
        "key_response": key_resp,
        "joy_correct": "NA",
        "joy_response": "NA",
        "correct": correct,
        "tap_num": tap_num,
        "pace_ms": pace_ms,
        "synch_sound_ticks": synch_sound_ticks if synch_sound_ticks is not None else "NA",
        "response_ticks": response_ticks if response_ticks is not None else "NA",
        "intervals": intervals if intervals is not None else "NA",
        "trial_outcome": trial_outcome,
        "stimulus_path": "tapping_task_tone_1000Hz_50ms_0.25amp.wav",
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