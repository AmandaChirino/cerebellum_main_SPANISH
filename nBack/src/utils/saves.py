# ./src/core/saves.py
"""
Utilities for saving trial-level experiment results to CSV files.

This module handles creation of participant-specific result files and appends one row per completed trial using a fixed column schema.
"""


import csv
import datetime

import utils.config as cfg
from utils.paths import RESULTS_DIR
from utils.logger import get_logger


logger = get_logger("./src/utils/saves")    # create logger


COLUMNS = [
    "task",                 # task name (always "nBack")
    "participant_id",       # participant id (input at the start of task)
    "language",             # spanish / english
    "location",             # USA / MEX / NA (derived from PID[0])
    "group",                # Pilot / Ctrl / Pat (derived from cfg.GROUP)
    "group_det",            # Pilot / Control / CD / Stroke / Tumor / Other
    "session",              # s1-s9
    "dominant_hand",       # participant's dominant hand
    "hand_used",   # hand used by participant to respond
    "mode",                 # "full" or "demo" based on cfg.MODE
    "mapping",              # task mapping
    "trial",                # number of trials (starting from 1)
    "block",                # block identifier (p1, p2... for practice; b1, b2... for test)
    "type",                 # "practice" / "experimental"
    "condition",            # "1_back" / "2_back" / "3_back"
    "key_correct",          # correct response
    "key_response",         # participant's response
    "joy_correct",          # joystick correct response (placeholder, always NA)
    "joy_response",         # joystick response (placeholder, always NA)
    "correct",              # 1 if correct, 0 if incorrect
    "reaction_time",        # reaction time
    "signal_detection",     # "hit" / "miss" / "false_alarm" / "correct_rejection"
    "letter_presented",     # letter presented (stimulus file name)
    "start_time",           # trial row written time
    "end_time",             # trial row written time
    "global_start_time",    # global task start time
    "global_end_time",      # global task end time
]


def _to_csv_value(value: object) -> object:
    """Serialize empty values as 'NA' for CSV output."""
    if value is None:
        return "NA"
    if isinstance(value, str):
        if value.strip() == "" or value in ("None", "null"):
            return "NA"
    return value


def _group_label(group) -> str:
    """Abbreviated group label: Pilot / Ctrl / Pat."""
    try:
        g = int(group)
    except (TypeError, ValueError):
        return "NA"
    if g == 1:
        return "Pilot"
    if g == 2:
        return "Ctrl"
    return "Pat"


def _group_det_label(group) -> str:
    """Detailed group label from numeric group (1-6)."""
    _MAP = {1: "Pilot", 2: "Control", 3: "CD", 4: "Stroke", 5: "Tumor", 6: "Other"}
    try:
        return _MAP.get(int(group), "NA")
    except (TypeError, ValueError):
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


def create_save() -> None:
    """
    Create a new results CSV for the current participant, writing the header row if the file does not exist.

    File path rules:
    - Output directory: RESULTS_DIR
    - File name pattern: "{cfg.PID}_nBack_results_YYYY_MM_DD.csv"
    - If file exists, creates a versioned file: "{cfg.PID}_v2_nBack_results_YYYY_MM_DD.csv", "_v3", etc.

    Side effects:
    - Creates a CSV file if missing.
    - Writes a single header row using COLUMNS.
    - Updates cfg.PID if a version suffix is added (e.g., "amanda023" -> "amanda023_v2")

    :return: None
    """
    # Ensure results directory exists
    RESULTS_DIR.mkdir(exist_ok=True)

    base_pid = cfg.PID
    # Get current date for filename
    date_str = datetime.datetime.now().strftime("%Y_%m_%d")
    csv_path = RESULTS_DIR / f"{base_pid}_nBack_results_{date_str}.csv"

    # If base file exists, find the next available version
    if csv_path.exists():
        version = 2
        while True:
            versioned_pid = f"{base_pid}_v{version}"
            csv_path = RESULTS_DIR / f"{versioned_pid}_nBack_results_{date_str}.csv"
            if not csv_path.exists():
                # Update PID to include version suffix
                cfg.PID = versioned_pid
                logger.info(f"File already exists for {base_pid}. Using versioned ID: {cfg.PID}")
                break
            version += 1

    # Create the file with header
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
    
    logger.info(f"Results file created at {csv_path}")


def update_save(
    condition: str,
    difficulty: str,
    response: str | None,
    correct_response: str | None,
    result: str,
    signal_detection: str | None,
    reaction_time: int | None,
    stimulus_path: str | None,
    block_label: str = None,
) -> None:
    """
    Append one trial result to the participant's results CSV.

    Behavior:
    - Ensures the CSV exists (calls create_save() if missing).
    - Computes the next trial_number by counting existing data rows (excluding header if present).
    - Appends a single row using the fixed column order defined in COLUMNS.

    Field mapping:
    - participant_id: cfg.PID
    - mapping: cfg.MAPPING
    - trial_number: auto-incremented starting from 1
    - start_time: cfg.START_TIME
    - end_time: current timestamp (ISO format)

    :param phase: Trial phase label (e.g., "practice" or "test")
    :type phase: str

    :param condition: Condition label (template may use "NA")
    :type condition: str

    :param difficulty: Difficulty label (template may use "NA")
    :type difficulty: str

    :param trial_type: Trial type: "practice", "test", or "null" (cannot be evaluated)
    :type trial_type: str

    :param response: Participant's response
    :type response: str

    :param correct_response: Correct (expected) response
    :type correct_response: str

    :param result: Whether the response is correct or incorrect
    :type result: str

    :param signal_detection: Signal detection classification: "hit", "miss", "false_alarm", "correct_rejection"
    :type signal_detection: str

    :param reaction_time: Reaction time for this trial (unit determined by caller; typically ms)
    :type reaction_time: int

    :param stimulus_path: Path (name) to the stimulus file presented on this trial
    :type stimulus_path: str

    :return: None
    """    
    # Get current date for filename (same as used in create_save)
    date_str = datetime.datetime.now().strftime("%Y_%m_%d")
    csv_path = RESULTS_DIR / f"{cfg.PID}_nBack_results_{date_str}.csv"

    # Ensure file exists with header
    if not csv_path.exists():
        create_save()

    # Count existing trials (exclude header)
    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.reader(rf)
        rows = list(reader)
        has_header = bool(rows) and rows[0] == COLUMNS
        data_rows = rows[1:] if has_header else rows
        next_trial_number = len(data_rows) + 1

    # Prepare one record
    record = {
        "task": "nBack",
        "participant_id": cfg.PID,
        "language": ("English" if (cfg.PID and str(cfg.PID)[0] in ("U","u")) else ("Espanol" if (cfg.PID and str(cfg.PID)[0] in ("M","m")) else "NA")),
        "location": _location_from_pid(cfg.PID),
        "group": _group_label(cfg.GROUP),
        "group_det": _group_det_label(cfg.GROUP),
        "session": cfg.SESSION or "",
        "dominant_hand": cfg.dominant_hand,
        "hand_used": cfg.hand_used,
        "mode": "full" if cfg.MODE == "full" else "demo",
        "mapping": cfg.MAPPING,
        "trial": next_trial_number,
        "block": block_label if block_label else cfg.current_block_label,
        "type": "practice" if condition == "practice" else "experimental",
        "condition": difficulty.replace("back", "_back"),
        "key_correct": correct_response,
        "key_response": response,
        "joy_correct": "NA",
        "joy_response": "NA",
        "correct": 1 if result == "correct" else 0,
        "reaction_time": reaction_time,
        "signal_detection": signal_detection,
        "letter_presented": stimulus_path,
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": datetime.datetime.now().isoformat(),
        "global_start_time": cfg.START_TIME,
        "global_end_time": cfg.GLOBAL_END_TIME,
    }

    # Write record in fixed column order
    write_header = not has_header
    with csv_path.open("a", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({k: _to_csv_value(record.get(k, "NA")) for k in COLUMNS})
    
    logger.info(f"Results file updated")


def finalize_experiment(global_end_time: str) -> None:
    """
    Update all rows with the final global end time.
    """
    date_str = datetime.datetime.now().strftime("%Y_%m_%d")
    csv_path = RESULTS_DIR / f"{cfg.PID}_nBack_results_{date_str}.csv"
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
        record["global_end_time"] = global_end_time
        updated.append([_to_csv_value(record.get(col, "NA")) for col in COLUMNS])

    with csv_path.open("w", newline="", encoding="utf-8") as wf:
        writer = csv.writer(wf)
        if has_header:
            writer.writerow(COLUMNS)
        writer.writerows(updated)

