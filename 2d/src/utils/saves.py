# ./src/core/saves.py
"""
Centralized utilities for persisting per-trial experiment outcomes.
"""


import csv
import datetime
from pathlib import Path

import utils.config as cfg
from utils.paths import RESULTS_DIR
from utils.logger import get_logger


logger = get_logger("./src/utils/saves")    # create logger


TASK_NAME = "2d"

_current_results_path: Path | None = None

NA_STR = "NA"


COLUMNS = [
    "task",
    "participant_id",
    # New columns inserted immediately after participant_id per spec
    "language",       # from PID[0]: U/u -> English; M/m -> Spanish; else NA
    "group",          # cfg.GROUP after admin
    "session",        # cfg.SESSION after admin
    # Keep existing dominant_hand and hand_used without duplication
    "dominant_hand",  # cfg.DH
    "hand_used",      # cfg.UH
    "mode",
    "mapping",
    "trial",
    "block",
    "block_type",
    "letter",
    "condition",
    "rotation_angle",
    "rotation",
    "stimuli_path",
    "key_correct",
    "key_response",
    "joy_correct",
    "joy_response",
    "correct",
    "reaction_time",
    "start_time",
    "end_time",
    "gloabl_start_time",
    "global-end_time",
]




def _language_from_pid(pid: str | None) -> str:
    """Compute language string from the first character of PID.

    Rules:
    - 'U'/'u' -> 'English'
    - 'M'/'m' -> 'Spanish'
    - otherwise -> 'NA' (string, not None)
    """
    if not pid or len(pid) == 0:
        return NA_STR
    c = str(pid)[0]
    if c in ("U", "u"):
        return "English"
    if c in ("M", "m"):
        return "Spanish"
    return NA_STR
def _today_yyyymmdd() -> str:
    """
    Get today's local date string in YYYY_MM_DD format.

    :return: Date string (YYYY_MM_DD)
    :rtype: str
    """
    return datetime.datetime.now().strftime("%Y_%m_%d")


def _results_csv_path() -> tuple[Path, str]:
    """
    Build the results path for the current participant.

    :return: (csv_path, date_str)
    :rtype: tuple[Path, str]
    """
    date_str = _today_yyyymmdd()

    base_pid = cfg.PID or "unknown"
    stem = f"{base_pid}_{TASK_NAME}_results_{date_str}.csv"
    csv_path = RESULTS_DIR / stem
    return csv_path, date_str


def create_save() -> None:
    """
    Create a new results CSV for the current participant, writing the header row.

    Filename format:
    - {PID}_{TASK_NAME}_results_YYYY_MM_DD.csv
    - If the file exists, increment with a two-digit counter:
      {PID}_{TASK_NAME}_results_02_YYYY_MM_DD.csv, 03, ...

    :return: None
    """

    global _current_results_path

    # Ensure results directory exists
    RESULTS_DIR.mkdir(exist_ok=True)

    base_path, date_str = _results_csv_path()
    if not base_path.exists():
        csv_path = base_path
    else:
        base_pid = cfg.PID or "unknown"
        counter = 2
        while True:
            stem = f"{base_pid}_{TASK_NAME}_results_{counter:02d}_{date_str}.csv"
            candidate = RESULTS_DIR / stem
            if not candidate.exists():
                csv_path = candidate
                break
            counter += 1

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)

    _current_results_path = csv_path
    logger.info(f"Results file created at {csv_path}")


def format_time(value: datetime.datetime | str | None = None) -> str:
    """
    Format time as `[yyyy-mm-dd hh-mm-ss]`.
    """
    if value is None:
        dt = datetime.datetime.now()
    elif isinstance(value, datetime.datetime):
        dt = value
    else:
        try:
            dt = datetime.datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return NA_STR
    return dt.strftime("%Y-%m-%d %H-%M-%S")


def _resolve_csv_path() -> Path:
    if _current_results_path is not None:
        return _current_results_path
    csv_path, _ = _results_csv_path()
    return csv_path


def update_save(
    block: str,
    block_type: str,
    letter: str | None,
    condition: str | None,
    rotation_angle: int | None,
    rotation: int | None,
    stimuli_path: str | None,
    key_correct: str,
    key_response: str | None,
    joy_correct: str,
    joy_response: str | None,
    correct: int | str | None,
    reaction_time: int | None,
    start_time: str,
    end_time: str,
    gloabl_start_time: str,
    global_end_time: str | None = None,
) -> None:
    """Append one trial result to the participant's results CSV."""
    csv_path = _resolve_csv_path()
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Results file not found: {csv_path}. Call create_save() first."
        )

    # Count existing trials (exclude header)
    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        rows = list(reader)
        has_header = bool(rows) and rows[0] == COLUMNS
        data_rows = rows[1:] if has_header else rows
        next_trial_index = len(data_rows) + 1

    # Route response fields based on detected input source.
    # Rule: per trial, record either key_* or joy_*, and leave the other pair empty.
    src = cfg._input_source

    if src == "key":
        joy_correct = ""
        joy_response = ""

    elif src == "joy":
        # Prefer explicitly provided joy_*; if empty but key_* is provided, fall back to key_*
        if (joy_correct == "" or joy_correct is None) and (key_correct != "" and key_correct is not None):
            joy_correct = key_correct
        if (joy_response == "" or joy_response is None) and (key_response != "" and key_response is not None):
            joy_response = key_response

        key_correct = ""
        key_response = ""


    record = {
        "task": TASK_NAME,
        "participant_id": cfg.PID,
        "language": _language_from_pid(cfg.PID),
        "group": cfg.GROUP or "",
        "session": cfg.SESSION or "",
        "dominant_hand": cfg.DH,
        "hand_used": cfg.UH,
        "mode": cfg.MODE,
        "mapping": cfg.MAPPING,
        "trial": next_trial_index,
        "block": block,
        "block_type": block_type,
        "letter": letter,
        "condition": condition,
        "rotation_angle": rotation_angle,
        "rotation": rotation,
        "stimuli_path": stimuli_path,
        "key_correct": key_correct,
        "key_response": key_response,
        "joy_correct": joy_correct,
        "joy_response": joy_response,
        "correct": correct,
        "reaction_time": reaction_time,
        "start_time": start_time,
        "end_time": end_time,
        "gloabl_start_time": gloabl_start_time,
        "global-end_time": global_end_time,
    }


    # Fill empty entries with "NA" for CSV consistency.
    normalized_record = {}
    for k in COLUMNS:
        v = record.get(k, "")
        if v is None or v == "":
            normalized_record[k] = NA_STR
        else:
            normalized_record[k] = v

    # Write record in fixed column order
    write_header = not has_header
    with csv_path.open("a", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow(normalized_record)
    
    logger.info("Results file updated")


def finalize_save(global_end_time: str) -> None:
    """
    Fill `global-end_time` for all saved rows at task end.
    """
    csv_path = _resolve_csv_path()
    if not csv_path.exists():
        return

    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.DictReader(rf)
        rows = list(reader)

    for row in rows:
        row["global-end_time"] = global_end_time

    with csv_path.open("w", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            normalized_row = {}
            for k in COLUMNS:
                v = row.get(k, "")
                if v is None or v == "":
                    normalized_row[k] = NA_STR
                else:
                    normalized_row[k] = v
            writer.writerow(normalized_row)

    logger.info("Results file finalized with global-end_time")
