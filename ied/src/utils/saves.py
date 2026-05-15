# ./src/utils/saves.py
"""
Utilities for saving trial-level experiment results to CSV files.
"""

from __future__ import annotations

import csv
import datetime
from pathlib import Path

import utils.config as cfg
from utils.paths import RESULTS_DIR
from utils.logger import get_logger


logger = get_logger("./src/utils/saves")


COLUMNS = [
    "task",
    "participant_id",
    "language",
    "group",
    "session",
    "dominant_hand",
    "hand_used",
    "mode",
    "mapping",
    "trial",
    "block",
    "block_type",
    "condition",
    "key_correct",
    "key_response",
    "joy_correct",
    "joy_response",
    "correct",
    "correct_shape",
    "correct_line",
    "incorrect_shape",
    "incorrect_line",
    "chosen_shape",
    "chosen_line",
    "unchosen_shape",
    "unchosen_line",
    "correct_count",
    "trial_count",
    "reaction_time",
    "start_time",
    "end_time",
    "global_start_time",
    "global_end_time",
]


def _language_from_pid(pid: str | None) -> str:
    """Derive language from PID's first character.

    - 'U'/'u' -> 'English'
    - 'M'/'m' -> 'Espanol'
    - otherwise -> 'NA'
    """
    if not pid:
        return "NA"
    first = str(pid)[0]
    if first in ("U", "u"):
        return "English"
    if first in ("M", "m"):
        return "Espanol"
    return "NA"


STIMULUS_FEATURES = {
    "ied_circle_big.png": {"shape": "circle_big", "line": "NA"},
    "ied_circle_little.png": {"shape": "circle_little", "line": "NA"},
    "ied_s1.png": {"shape": "s1", "line": "NA"},
    "ied_s2.png": {"shape": "s2", "line": "NA"},
    "ied_s3.png": {"shape": "s3", "line": "NA"},
    "ied_s4.png": {"shape": "s4", "line": "NA"},
    "ied_s5.png": {"shape": "s5", "line": "NA"},
    "ied_s6.png": {"shape": "s6", "line": "NA"},
    "ied_l1.png": {"shape": "NA", "line": "l1"},
    "ied_l2.png": {"shape": "NA", "line": "l2"},
    "ied_l3.png": {"shape": "NA", "line": "l3"},
    "ied_l4.png": {"shape": "NA", "line": "l4"},
    "ied_l5.png": {"shape": "NA", "line": "l5"},
    "ied_l6.png": {"shape": "NA", "line": "l6"},
}


def _extract_stimulus_features(img_path_str: str) -> dict:
    """Extract shape and line features from stimulus image path."""
    from pathlib import Path
    filename = Path(img_path_str).name
    return STIMULUS_FEATURES.get(filename, {"shape": "NA", "line": "NA"})


phase_to_condition = {
    "PRACTICE1": "Choose the big circle",
    "PRACTICE2": "Choose the little circle",
    "P1": "Simple Discrimination (SD)",
    "P2": "Simple Reversal (SR)",
    "P3": "Compound Discrimination Separated (CDS)",
    "P4": "Compound Discrimination Overlapped (CDO)",
    "P5": "Compound Discrimination Reversal (CDR)",
    "P6": "Intra-Dimensional Shift (IDS)",
    "P7": "Intra-Dimensional Reversal (IDR)",
    "P8": "Extra-Dimensional Shift (EDS)",
    "P9": "Extra-Dimensional Reversal (EDR)",
}

phase_to_difficulty = {
    "PRACTICE1": "Choose the big circle",
    "PRACTICE2": "Choose the little circle",
    "P1": "SD",
    "P2": "SR",
    "P3": "CDS",
    "P4": "CDO",
    "P5": "CDR",
    "P6": "IDS",
    "P7": "IDR",
    "P8": "EDS",
    "P9": "EDR",
}


def _results_path() -> Path:
    if cfg.RESULTS_FILENAME:
        return RESULTS_DIR / cfg.RESULTS_FILENAME
    date_str = cfg.RESULTS_DATE or datetime.datetime.now().strftime("%Y_%m_%d")
    return RESULTS_DIR / f"{cfg.PID}_ied_results_{date_str}.csv"


def _pick_available_filename() -> str:
    date_str = cfg.RESULTS_DATE or datetime.datetime.now().strftime("%Y_%m_%d")
    base_name = f"{cfg.PID}_ied_results_{date_str}.csv"
    base_path = RESULTS_DIR / base_name

    if not base_path.exists():
        return base_name

    index = 2
    while True:
        suffix = f"_v{index:02d}.csv"
        candidate = f"{cfg.PID}_ied_results_{date_str}{suffix}"
        if not (RESULTS_DIR / candidate).exists():
            return candidate
        index += 1


def create_save() -> None:
    """Create a new results CSV for a participant with header row."""
    # Ensure results directory exists
    RESULTS_DIR.mkdir(exist_ok=True)

    filename = _pick_available_filename()
    cfg.RESULTS_FILENAME = filename
    csv_path = RESULTS_DIR / filename

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)

    logger.info("Results file created at %s", csv_path)


def _phase_to_block(phase: str) -> str:
    if phase == "PRACTICE1":
        return "p1"
    if phase == "PRACTICE2":
        return "p2"
    if phase.startswith("P") and phase[1:].isdigit():
        return f"b{phase[1:]}"
    return phase.lower()


def _block_to_type(block: str) -> str:
    if block in ("p1", "p2"):
        return "practice"
    if block.startswith("b"):
        return "experimental"
    return "experimental"


def _normalize_condition(condition: str | None) -> str | None:
    if condition == "Choose the big circle":
        return "big"
    if condition == "Choose the little circle":
        return "small"
    return condition


def _to_csv_value(value: object) -> object:
    """Serialize missing values to 'NA' for CSV output."""
    if value is None:
        return "NA"
    if isinstance(value, str) and (value.strip() == "" or value == "None"):
        return "NA"
    return value


def update_save(
    phase: str,
    correct: int,
    correct_dir: str | None,
    response_dir: str | None,
    input_source: str | None,
    correct_stimulus: str | None = None,
    incorrect_stimulus: str | None = None,
    correct_buffer: str | None = None,
    incorrect_buffer: str | None = None,
    reaction_time: int | None = None,
) -> None:
    """Append one trial result to the participant's CSV file."""
    csv_path = _results_path()

    if not csv_path.exists():
        raise FileNotFoundError(f"Results file not found: {csv_path}")

    # Count existing trials (exclude header)
    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        rows = list(reader)
        has_header = bool(rows) and rows[0] == COLUMNS
        data_rows = rows[1:] if has_header else rows
        next_trial_number = len(data_rows) + 1

    # Prepare one record
    block = _phase_to_block(phase)
    condition = _normalize_condition(phase_to_difficulty.get(phase))
    row_type = _block_to_type(block)

    key_correct = None
    key_response = None
    joy_correct = None
    joy_response = None

    if input_source == "keyboard":
        key_correct = correct_dir
        key_response = response_dir
    elif input_source == "joystick":
        joy_correct = correct_dir
        joy_response = response_dir

    # Extract stimulus features
    correct_features = _extract_stimulus_features(correct_stimulus) if correct_stimulus else {"shape": "NA", "line": "NA"}
    incorrect_features = _extract_stimulus_features(incorrect_stimulus) if incorrect_stimulus else {"shape": "NA", "line": "NA"}
    correct_buffer_features = _extract_stimulus_features(correct_buffer) if correct_buffer else {"shape": "NA", "line": "NA"}
    incorrect_buffer_features = _extract_stimulus_features(incorrect_buffer) if incorrect_buffer else {"shape": "NA", "line": "NA"}
    
    # Combine shape and line from stimulus and buffer (take non-NA value)
    correct_shape = correct_features["shape"] if correct_features["shape"] != "NA" else correct_buffer_features["shape"]
    correct_line = correct_features["line"] if correct_features["line"] != "NA" else correct_buffer_features["line"]
    incorrect_shape = incorrect_features["shape"] if incorrect_features["shape"] != "NA" else incorrect_buffer_features["shape"]
    incorrect_line = incorrect_features["line"] if incorrect_features["line"] != "NA" else incorrect_buffer_features["line"]
    
    # Determine chosen and unchosen based on correctness
    if correct == 1:
        chosen_shape = correct_shape
        chosen_line = correct_line
        unchosen_shape = incorrect_shape
        unchosen_line = incorrect_line
    else:
        chosen_shape = incorrect_shape
        chosen_line = incorrect_line
        unchosen_shape = correct_shape
        unchosen_line = correct_line

    record = {
        "task": "ied",
        "participant_id": cfg.PID,
        "language": _language_from_pid(cfg.PID),
        "group": cfg.GROUP or "",
        "session": cfg.SESSION or "",
        "dominant_hand": cfg.dominant_hand,
        "hand_used": cfg.hand_used,
        "mode": cfg.MODE,
        "mapping": cfg.MAPPING,
        "trial": next_trial_number,
        "block": block,
        "block_type": row_type,
        "condition": condition,
        "key_correct": key_correct,
        "key_response": key_response,
        "joy_correct": joy_correct,
        "joy_response": joy_response,
        "correct": correct,
        "correct_shape": correct_shape,
        "correct_line": correct_line,
        "incorrect_shape": incorrect_shape,
        "incorrect_line": incorrect_line,
        "chosen_shape": chosen_shape,
        "chosen_line": chosen_line,
        "unchosen_shape": unchosen_shape,
        "unchosen_line": unchosen_line,
        "reaction_time": reaction_time,
        "start_time": cfg.PHASE_START_TIME,
        "end_time": cfg.PHASE_END_TIME,
        "global_start_time": cfg.START_TIME,
        "global_end_time": cfg.GLOBAL_END_TIME,
        "correct_count": cfg.correct_count,
        "trial_count": cfg.trial_count,
    }

    # Write record in fixed column order
    write_header = not has_header
    with csv_path.open("a", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({k: _to_csv_value(record.get(k, "NA")) for k in COLUMNS})

    logger.info("Results file updated")


def finalize_phase(phase: str, phase_end_time: str) -> None:
    """
    Update all rows for the given phase (block) with the final end time.
    """
    csv_path = _results_path()
    if not csv_path.exists():
        return

    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        rows = list(reader)

    if not rows:
        return

    has_header = rows[0] == COLUMNS
    data_rows = rows[1:] if has_header else rows

    target_block = _phase_to_block(phase)
    updated = []
    for row in data_rows:
        record = dict(zip(COLUMNS, row))
        if record.get("block") == target_block:
            record["end_time"] = phase_end_time
        updated.append([_to_csv_value(record.get(col, "NA")) for col in COLUMNS])

    with csv_path.open("w", newline="", encoding="utf-8") as wf:
        writer = csv.writer(wf)
        if has_header:
            writer.writerow(COLUMNS)
        writer.writerows(updated)


def finalize_experiment(global_end_time: str) -> None:
    """
    Update all rows with the final global end time.
    """
    csv_path = _results_path()
    if not csv_path.exists():
        return

    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        rows = list(reader)

    if not rows:
        return

    has_header = rows[0] == COLUMNS
    data_rows = rows[1:] if has_header else rows

    updated = []
    for row in data_rows:
        record = dict(zip(COLUMNS, row))
        if record.get("end_time") in (None, "", "NA", "None"):
            record["end_time"] = global_end_time
        record["global_end_time"] = global_end_time
        updated.append([_to_csv_value(record.get(col, "NA")) for col in COLUMNS])

    with csv_path.open("w", newline="", encoding="utf-8") as wf:
        writer = csv.writer(wf)
        if has_header:
            writer.writerow(COLUMNS)
        writer.writerows(updated)

    if cfg.START_TIME and global_end_time:
        try:
            start_time_obj = datetime.datetime.strptime(cfg.START_TIME, "%Y-%m-%d %H:%M:%S")
            end_time_obj = datetime.datetime.strptime(global_end_time, "%Y-%m-%d %H:%M:%S")
            total_duration = end_time_obj - start_time_obj
            total_minutes = total_duration.total_seconds() / 60
            
            logger.info("Task completed successfully!")
            logger.info(f"Total task duration: {total_minutes:.2f} minutes ({int(total_duration.total_seconds())} seconds)")
        except Exception as e:
            logger.warning(f"Could not calculate task duration: {e}")
