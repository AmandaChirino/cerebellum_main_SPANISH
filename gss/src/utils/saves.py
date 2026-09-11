# ./src/core/saves.py
"""
Centralized utilities for persisting per-trial experiment outcomes.
"""


import csv
import datetime
import math
from pathlib import Path

import utils.config as cfg
from utils.paths import RESULTS_DIR
from utils.logger import get_logger


logger = get_logger("./src/utils/saves")    # create logger


TASK_NAME = "gss"

_current_results_path: Path | None = None
_joy_buffer: list[dict] = []
_current_joy_path: Path | None = None
_joy_trial_counter: int = 1

NA_STR = "NA"
_prev_goal: str = NA_STR


def reset_prev_goal() -> None:
    global _prev_goal
    _prev_goal = NA_STR


COLUMNS = [
    "task",                 # task name (abbreviation)
    "participant_id",       # participant ID (input at the start of task)
    "language",             # English / Espanol / NA (derived from PID[0])
    "location",             # USA / MEX / NA (derived from PID[0])
    "group",                # Pilot / Ctrl / Pat (derived from cfg.GROUP)
    "group_det",            # Pilot / Control / CD / Stroke / Tumor / Other
    "session",              # session (1-6) from cfg.SESSION
    "dominant_hand",        # participant's dominant hand (left / right)
    "hand_used",            # hand used during task (left / right)
    "mode",                 # task mode (demo / full)
    "mapping",              # task mapping (1 / 2)
    "trial",                # trial index
    "block",                # block name
    "trial_type",           # trial type (practice / experimental)
    "condition",            # characteristic(s) specific to the task
    "word",                 # stroop word text
    "ink",                  # ink color the word is printed in
    "key_correct",          # keyboard response expected (key name)
    "key_response",         # keyboard response recieved (key name)
    "joy_correct",          # joystick response expected (up / down / left / right)
    "joy_response",         # joystick response recieved (up / down / left / right)
    "correct",              # trial result (1 = correct / 0 = incorrect / None = timeout)
    "reaction_time",        # reaction time (ms)
    "goal",                 # trial goal: speed / accuracy
    "block_type",           # block type: fixed / varying
    "congruency",           # trial congruency: congruent / incongruent
    "interval_index",       # interval index within the block (1-indexed)
    "trial_in_interval",    # trial counter within the interval (resets to 1 each new goal icon)
    "interval_duration_ms", # total duration of the interval window (ms)
    "time_in_interval_ms",  # time from interval start to stimulus onset (ms) — DDM threshold predictor
    "is_switch",            # 1 = first trial of new goal interval (switch); 0 = repeat; NA = not applicable
    "joy_word_dir",         # joystick direction for the COLOR WORD (prepotent response; used to classify DDM errors)
    "error_type",           # error classification: correct / stroop_error / random_error / NA (timeout). For DDM: include only stroop_error trials.
    "stimulus_path",        # file path (name) to the stimulus
    "start_time",           # start time of the current block (ISO format)
    "end_time",             # end time of the current block (ISO format)
    "global_start_time",    # whole task start time (ISO)
    "global_end_time",      # whole task end time (ISO)
]


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

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

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


JOY_COLUMNS = ["timestamp_ms", "trial_index", "block", "x_raw", "y_raw", "magnitude", "angle_deg", "direction", "event"]


def create_joy_save() -> None:
    global _current_joy_path
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    base_pid = cfg.PID or "unknown"
    path = RESULTS_DIR / f"{base_pid}_gss_joystick_{_today_yyyymmdd()}.csv"
    counter = 2
    while path.exists():
        path = RESULTS_DIR / f"{base_pid}_gss_joystick_{counter:02d}_{_today_yyyymmdd()}.csv"
        counter += 1
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(JOY_COLUMNS)
    _current_joy_path = path


def _angle_to_direction(magnitude: float, angle_deg: float) -> str:
    if magnitude < 0.1:
        return "rest"
    a = angle_deg
    if 225 <= a < 315: return "left"
    if  45 <= a < 135: return "right"
    if 135 <= a < 225: return "down"
    return "up"


def log_joy_frame(timestamp_ms: int, block: str, x_raw: float, y_raw: float, event: str = "") -> None:
    magnitude = math.sqrt(x_raw ** 2 + y_raw ** 2)
    angle_deg = round((math.degrees(math.atan2(x_raw, -y_raw)) + 360) % 360, 2)
    _joy_buffer.append({
        "timestamp_ms": timestamp_ms,
        "trial_index": _joy_trial_counter,
        "block": block,
        "x_raw": round(x_raw, 4),
        "y_raw": round(y_raw, 4),
        "magnitude": round(magnitude, 4),
        "angle_deg": angle_deg,
        "direction": _angle_to_direction(magnitude, angle_deg),
        "event": event,
    })


def flush_joy_buffer() -> None:
    global _joy_buffer
    if not _joy_buffer or _current_joy_path is None:
        _joy_buffer = []
        return
    with _current_joy_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=JOY_COLUMNS)
        writer.writerows(_joy_buffer)
    _joy_buffer = []


def _classify_error(
    correct: str | int | None,
    joy_response: str,
    joy_word_dir: str,
) -> str:
    """
    Classify the trial outcome for DDM error filtering.

    Returns one of:
      "correct"       — response was correct
      "stroop_error"  — wrong response, but matches the color WORD direction
                        (the prepotent/automatic Stroop error; INCLUDE in DDM)
      "random_error"  — wrong response, does NOT match the color WORD direction
                        (likely a slip or random press; EXCLUDE from DDM)
      "NA"            — timeout or missing response

    The paper (CAC_Aging_ms_3.3) explicitly keeps only stroop_error trials
    among incorrect responses when fitting the Drift Diffusion Model.
    """
    if correct in (None, "NA", "timeout", ""):
        return NA_STR
    if str(correct).lower() in ("correct", "1", "true"):
        return "correct"
    # incorrect trial: is the response the prepotent (word) direction?
    if (
        joy_response not in (None, "", NA_STR)
        and joy_word_dir not in (None, "", NA_STR)
        and str(joy_response) == str(joy_word_dir)
    ):
        return "stroop_error"
    return "random_error"


def update_save(
        block_name: str,
        trial_type: str,
        condition: str,
        key_correct: str,
        key_response: str,
        joy_correct: str,
        joy_response: str,
        correct: int | None,
        reaction_time: int | None,
        stimulus_path: str,
        goal: str = NA_STR,
        block_type: str = NA_STR,
        congruency: str = NA_STR,
        word: str = NA_STR,
        ink: str = NA_STR,
        interval_index: int | None = None,
        trial_in_interval: int | None = None,
        interval_duration_ms: int | None = None,
        time_in_interval_ms: int | None = None,
        joy_word_dir: str = NA_STR,
) -> None:
    """
    Append one trial result to the participant's results CSV.

    :param block_name: Bloc name
    :type block_name: str

    :param trrial_type: Trial type (practice / test)
    :type type: str

    :param condition: Characteristic(s) specific to the task
    :type condition: str

    :param key_correct: Keyboard response expected (key name)
    :type key_correct: str

    :param key_response: Keyboard response recieved (key name)
    :type key_response: str

    :param joy_correct: Joystick response expected (up / down / left / right)
    :type joy_correct: str

    :param joy_response: Joystick response recieved (up / down / left / right)
    :type joy_response: str

    :param correct: Trial result (1 = correct / 0 = incorrect / None = timeout)
    :type correct: int

    :param reaction_time: Reaction time (ms)
    :type reaction_time: int

    :param stimulus_path: File path (name) to the stimulus
    :type stimulus_path: str

    :param goal: Trial goal (speed / accuracy)
    :type goal: str

    :param block_type: Block type (fixed / varying)
    :type block_type: str

    :param congruency: Trial congruency (congruent / incongruent)
    :type congruency: str

    :param interval_index: Index of the interval within the block (1-indexed)
    :type interval_index: int | None

    :param interval_duration_ms: Total duration of the interval window (ms)
    :type interval_duration_ms: int | None

    :param time_in_interval_ms: Time from interval start to stimulus onset (ms)
    :type time_in_interval_ms: int | None

    :param joy_word_dir: Joystick direction for the color WORD (prepotent DDM error classifier)
    :type joy_word_dir: str
    """
    global _joy_trial_counter, _prev_goal

    if _current_results_path is not None:
        csv_path = _current_results_path
    else:
        csv_path, _ = _results_csv_path()

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

    # Unify correct fields to keep key_correct and joy_correct consistent
    # If one is empty, copy from the other; if both present but different, prefer key_correct.
    if (key_correct is None or key_correct == "") and (joy_correct not in (None, "")):
        key_correct = joy_correct
    if (joy_correct is None or joy_correct == "") and (key_correct not in (None, "")):
        joy_correct = key_correct
    if (key_correct not in (None, "")) and (joy_correct not in (None, "")) and (key_correct != joy_correct):
        joy_correct = key_correct

    if goal in (NA_STR, None, ""):
        is_switch = NA_STR
    elif trial_in_interval == 1 and interval_index == 1:
        is_switch = NA_STR
        _prev_goal = NA_STR
    elif trial_in_interval == 1 and _prev_goal in (NA_STR, None, ""):
        is_switch = NA_STR
    elif trial_in_interval == 1 and goal != _prev_goal:
        is_switch = 1
    elif trial_in_interval == 1 and goal == _prev_goal:
        is_switch = 0
    else:
        is_switch = 0

    if goal not in (NA_STR, None, "") and trial_in_interval == 1:
        _prev_goal = goal

    # Prepare one record
    record = {
        "task": TASK_NAME,
        "participant_id": cfg.PID,
        "language": _derive_language_from_pid(cfg.PID),
        "location": _location_from_pid(cfg.PID),
        "group": _group_label(cfg.GROUP),
        "group_det": _group_det_label(cfg.GROUP),
        "session": cfg.SESSION,
        "dominant_hand": cfg.DH,
        "hand_used": cfg.UH,
        "mode": cfg.MODE,
        "mapping": cfg.MAPPING,
        "trial": next_trial_index,
        "block": block_name,
        "trial_type": trial_type,
        "condition": condition,
        "word": word,
        "ink": ink,
        "key_correct": key_correct,
        "key_response": key_response,
        "joy_correct": joy_correct,
        "joy_response": joy_response,
        "correct": correct,
        "reaction_time": reaction_time,
        "goal": goal,
        "block_type": block_type,
        "congruency": congruency,
        "interval_index": interval_index,
        "trial_in_interval": trial_in_interval,
        "interval_duration_ms": interval_duration_ms,
        "time_in_interval_ms": time_in_interval_ms,
        "is_switch": is_switch,
        "joy_word_dir": joy_word_dir,
        "error_type": _classify_error(correct, joy_response, joy_word_dir),
        "stimulus_path": stimulus_path,
        "start_time": cfg._start_time,
        "end_time": cfg._end_time,
        "global_start_time": getattr(cfg, "global_start_time", None),
        "global_end_time": getattr(cfg, "global_end_time", None),
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

    _joy_trial_counter += 1

    logger.debug(f"Results file updated")


def _csv_now_iso() -> str:
    return datetime.datetime.now().isoformat()


def finalize_block_end_time() -> None:
    """Fill all NA end_time entries with the current time for the active CSV."""
    global _current_results_path
    csv_path = _current_results_path or _results_csv_path()[0]
    if not csv_path.exists():
        return
    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.DictReader(rf)
        rows = list(reader)
        fieldnames = reader.fieldnames or COLUMNS
    changed = False
    now_iso = _csv_now_iso()
    for row in rows:
        if row.get("end_time", "") in ("", NA_STR):
            row["end_time"] = now_iso
            changed = True
    if changed:
        with csv_path.open("w", newline="", encoding="utf-8") as wf:
            writer = csv.DictWriter(wf, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def finalize_global_end_time() -> None:
    """Set global_end_time for all rows to the current time for the active CSV."""
    global _current_results_path
    csv_path = _current_results_path or _results_csv_path()[0]
    if not csv_path.exists():
        return
    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        reader = csv.DictReader(rf)
        rows = list(reader)
        fieldnames = reader.fieldnames or COLUMNS
    now_iso = _csv_now_iso()
    for row in rows:
        row["global_end_time"] = now_iso
    with csv_path.open("w", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def _derive_language_from_pid(pid: str | None) -> str:
    if not pid or len(str(pid)) == 0:
        return NA_STR
    first = str(pid)[0]
    if first == 'U' or first == 'u':
        return 'English'
    if first == 'M' or first == 'm':
        return 'Espanol'
    return NA_STR


def _group_label(group) -> str:
    """Abbreviated group label: Pilot / Ctrl / Pat."""
    try:
        g = int(group)
    except (TypeError, ValueError):
        return NA_STR
    if g == 1:
        return "Pilot"
    if g == 2:
        return "Ctrl"
    return "Pat"


def _group_det_label(group) -> str:
    """Detailed group label from numeric group (1-6)."""
    _MAP = {1: "Pilot", 2: "Control", 3: "CD", 4: "Stroke", 5: "Tumor", 6: "Other"}
    try:
        return _MAP.get(int(group), NA_STR)
    except (TypeError, ValueError):
        return NA_STR


def _location_from_pid(pid: str | None) -> str:
    """Derive location from first char of PID: U/u -> USA, M/m -> MEX, else NA."""
    if not pid:
        return NA_STR
    first = str(pid)[0]
    if first in ("U", "u"):
        return "USA"
    if first in ("M", "m"):
        return "MEX"
    return NA_STR
