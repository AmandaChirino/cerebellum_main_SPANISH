# ./src/core/saves.py
"""
Centralized utilities for persisting per-trial experiment outcomes.
"""


import csv
import datetime
from pathlib import Path
import pygame

import utils.config as cfg
from utils.paths import RESULTS_DIR
from utils.logger import get_logger


logger = get_logger("./src/utils/saves")    # create logger


TASK_NAME = "ccs"

_current_results_path: Path | None = None


COLUMNS = [
    "task",                     # ccs (motor/sensorimotor)
    "participant_id",           # participant ID
    "language",                 # English / Espanol
    "group",                    # pilot / control / cd / stroke / tumor / other
    "session",                  # s1-s9
    "dominant_hand",            # left / right
    "hand_used",                # left / right
    "mode",                     # demo / full
    "mapping",                  # 1 / 2
    "trial",                    # trial index
    "block",                    # block name (p1-p3 / b1-b4)
    "type",                     # practice / experimental
    "condition",                # task_catch or task (e.g., motor_catch, motor)
    "key_correct",              # expected key response
    "key_response",             # first captured key response (trial-level)
    "stimulus_key_response",    # stimulus-stage key response
    "isi_key_response",         # isi-stage key response
    "joy_correct",              # expected joystick response (left / right)
    "joy_response",             # first captured joystick response (trial-level)
    "stimulus_joy_response",    # stimulus-stage joystick response
    "isi_joy_response",         # isi-stage joystick response
    "correct",                  # 0 / 1
    "reaction_time",            # time from stimulus onset to response
    "error_type",               # error category
    "start_time",               # current block start time (yyyy-mm-dd-hh-mm-ss)
    "end_time",                 # current block end time (yyyy-mm-dd-hh-mm-ss)
    "global_start_time",        # task start time (yyyy-mm-dd-hh-mm-ss)
    "global_end_time",          # task end time (yyyy-mm-dd-hh-mm-ss)
]

STR_COLUMNS = {
    "task",
    "participant_id",
    "language",
    "group",
    "session",
    "dominant_hand",
    "hand_used",
    "mode",
    "block",
    "type",
    "condition",
    "key_correct",
    "key_response",
    "stimulus_key_response",
    "isi_key_response",
    "joy_correct",
    "joy_response",
    "stimulus_joy_response",
    "isi_joy_response",
    "start_time",
    "end_time",
    "global_start_time",
    "global_end_time",
    "error_type",
}


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
    - If the file exists, increment with a suffix:
      {PID}_{TASK_NAME}_results_YYYY_MM_DD_2.csv, _3, ...

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
            stem = f"{base_pid}_{TASK_NAME}_results_{date_str}_{counter}.csv"
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


def _first_non_empty(*vals: str) -> str:
    for v in vals:
        if v not in ("", None):
            return str(v)
    return ""


def _task_from_condition(condition_task: str) -> str:
    return "ccs"


def _normalize_mode(raw_mode: str | None) -> str:
    if raw_mode == "full":
        return "full"
    return "demo"



def _language_from_pid(pid: str | None) -> str:
    """Derive language from the first character of PID: U/u->English, M/m->Espanol, else NA."""
    if not pid:
        return "NA"
    first = str(pid)[0]
    if first == 'U' or first == 'u':
        return "English"
    if first == 'M' or first == 'm':
        return "Espanol"
    return "NA"

def _normalize_record_for_csv(record: dict) -> dict:
    normalized = dict(record)
    for key in STR_COLUMNS:
        val = normalized.get(key)
        if val in ("", None):
            normalized[key] = "NA"
        else:
            normalized[key] = str(val)
    return normalized


def _key_to_str(key) -> str:
    if key is None:
        return ""
    if key == pygame.K_v:
        return "v"
    if key == pygame.K_m:
        return "m"
    if key == pygame.K_d:
        return "d"
    if key == pygame.K_k:
        return "k"
    return str(key)


def update_save(
        block_name: str,
        condition_task: str,
        is_catch: bool,
        key_correct: str = "",
        joy_correct: str = "",
        stimulus_key_response: str = "",
        isi_key_response: str = "",
        stimulus_joy_response: str = "",
        isi_joy_response: str = "",
        correct: int | None = None,
        reaction_time: int | None = None,
        start_time: str = "",
        end_time: str = "",
        global_start_time: str = "",
        global_end_time: str = "",
        error_type: str = "",
        trial: int | None = None,
        input_source: str | None = None,
    ) -> None:
    """
    Append one trial result to the participant's results CSV.

    :param block_name: Block name (p1-p3 / b1-b4)
    :type block_name: str

    :param condition_task: Task condition (motor / sensorimotor)
    :type condition_task: str

    :param is_catch: Whether the current trial is a catch trial
    :type is_catch: bool

    :param key_correct: Expected keyboard response
    :type key_correct: str

    :param joy_correct: Expected joystick response (left / right)
    :type joy_correct: str

    :param stimulus_key_response: Stimulus-stage keyboard response
    :type stimulus_key_response: str

    :param isi_key_response: ISI-stage keyboard response
    :type isi_key_response: str

    :param stimulus_joy_response: Stimulus-stage joystick response
    :type stimulus_joy_response: str

    :param isi_joy_response: ISI-stage joystick response
    :type isi_joy_response: str

    :param correct: Trial result (1 = correct / 0 = incorrect/timeout)
    :type correct: int

    :param reaction_time: Time from stimulus onset to response (ms)
    :type reaction_time: int

    :param start_time: Current block start time (yyyy-mm-dd-hh-mm-ss)
    :type start_time: str

    :param end_time: Current block end time (yyyy-mm-dd-hh-mm-ss)
    :type end_time: str

    :param global_start_time: Whole-task start time (yyyy-mm-dd-hh-mm-ss)
    :type global_start_time: str

    :param global_end_time: Whole-task end time (yyyy-mm-dd-hh-mm-ss)
    :type global_end_time: str

    :param error_type: Error type label
    :type error_type: str

    :param trial: Explicit trial index. If None, inferred from row count.
    :type trial: int | None
    """
    if _current_results_path is None:
        raise FileNotFoundError(
            "Results file path is not initialized. Call create_save() first."
        )
    csv_path = _current_results_path

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
        next_trial_index = trial if trial is not None else (len(data_rows) + 1)

    # Keep exactly one input source per trial:
    # if key is used, clear all joystick fields; if joystick is used, clear all key fields.
    # Use the explicit input_source captured within the trial; fall back to cfg._input_source
    # only if no explicit source was provided (legacy paths).
    src = input_source if input_source is not None else cfg._input_source

    if src == "key":
        joy_correct = ""
        stimulus_joy_response = ""
        isi_joy_response = ""
    elif src == "joy":
        key_correct = ""
        stimulus_key_response = ""
        isi_key_response = ""
    else:
        # Fallback: infer source from populated fields
        has_key = any(v not in ("", None) for v in [stimulus_key_response, isi_key_response])
        has_joy = any(v not in ("", None) for v in [stimulus_joy_response, isi_joy_response])
        if has_key and not has_joy:
            joy_correct = ""
            stimulus_joy_response = ""
            isi_joy_response = ""
        elif has_joy and not has_key:
            key_correct = ""
            stimulus_key_response = ""
            isi_key_response = ""

    key_response = _first_non_empty(stimulus_key_response, isi_key_response)
    joy_response = _first_non_empty(stimulus_joy_response, isi_joy_response)

    trial_type = "practice" if str(block_name).startswith("p") else "experimental"
    condition = f"{condition_task}{'_catch' if is_catch else ''}"
    mode = _normalize_mode(cfg.MODE)
    task = _task_from_condition(condition_task)

    # Prepare one record
    record = {
        "task": task,
        "participant_id": cfg.PID,
        "language": _language_from_pid(cfg.PID),
        "group": cfg.GROUP or "",
        "session": cfg.SESSION or "",
        "dominant_hand": cfg.DH,
        "hand_used": cfg.UH,
        "mode": mode,
        "mapping": cfg.MAPPING,
        "trial": next_trial_index,
        "block": block_name,
        "type": trial_type,
        "condition": condition,
        "key_correct": key_correct,
        "key_response": key_response,
        "stimulus_key_response": stimulus_key_response,
        "isi_key_response": isi_key_response,
        "joy_correct": joy_correct,
        "joy_response": joy_response,
        "stimulus_joy_response": stimulus_joy_response,
        "isi_joy_response": isi_joy_response,
        "correct": 1 if correct else 0,
        "reaction_time": reaction_time,
        "start_time": start_time,
        "end_time": end_time,
        "global_start_time": global_start_time,
        "global_end_time": global_end_time,
        "error_type": error_type,
    }

    # Write record in fixed column order (must append to existing file only)
    normalized_record = _normalize_record_for_csv(record)
    write_header = not has_header
    with csv_path.open("a", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({k: normalized_record.get(k, "") for k in COLUMNS})
    
    logger.info(f"Results file updated")


def InitResultCSV(filename: str, participant_id: str) -> None:
    """
    Backward-compatible initializer.
    Creates exactly one new results file for this run via create_save().
    """
    if participant_id:
        cfg.PID = participant_id
    create_save()


def SaveResultsToCsv(
    filename: str,
    participant_id: str,
    all_results: dict,
    global_start_time: str,
    global_end_time: str,
) -> None:
    """
    Backward-compatible saver.
    Routes legacy per-trial payload into update_save().
    """
    if participant_id:
        cfg.PID = participant_id

    update_save(
        block_name=all_results.get("block", ""),
        condition_task=all_results.get("condition", ""),
        is_catch=bool(all_results.get("is_catch")),
        key_correct=_key_to_str(all_results.get("key_correct")),
        joy_correct=str(all_results.get("joy_correct") or ""),
        stimulus_key_response=_key_to_str(all_results.get("stimulus_key_response")),
        isi_key_response=_key_to_str(all_results.get("isi_key_response")),
        stimulus_joy_response=str(all_results.get("stimulus_joy_response") or ""),
        isi_joy_response=str(all_results.get("isi_joy_response") or ""),
        correct=1 if all_results.get("correct") else 0,
        reaction_time=int(all_results.get("reaction_time_ms", 0) or 0),
        start_time=str(all_results.get("block_start_time") or ""),
        end_time=str(all_results.get("block_end_time") or ""),
        global_start_time=str(cfg.START_TIME or global_start_time or ""),
        global_end_time=str(cfg._end_time or global_end_time or ""),
        error_type=str(all_results.get("error_type") or ""),
        trial=None,
        input_source=all_results.get("input_source"),
    )