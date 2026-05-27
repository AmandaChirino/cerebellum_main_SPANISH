"""
Per-trial CSV persistence for current CCC task.
"""


import csv
import datetime
from pathlib import Path

import utils.config as cfg
from utils.paths import RESULTS_DIR
from utils.logger import get_logger


logger = get_logger("./src/utils/saves")

TASK_NAME = "ccc"
NA_STR = "NA"
_current_results_path: Path | None = None


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


COLUMNS = [
    "task",
    "participant_id",
    "language",
    "location",      # USA / MEX / NA (derived from PID[0])
    "group",         # Pilot / Ctrl / Pat (derived from cfg.GROUP)
    "group_det",     # Pilot / Control / CD / Stroke / Tumor / Other
    "session",
    "dominant_hand",
    "hand_used",
    "mode",
    "mapping",
    "trial",
    "block",
    "trial_type",
    "condition",
    "list",
    "color",
    "class",
    "case",
    "congruency",
    "switching",
    "stim_repetition",
    "stimuli",
    "key_correct",
    "key_response",
    "joy_correct",
    "joy_response",
    "correct",
    "reaction_time",
    "stimulus_path",
    "start_time",
    "end_time",
    "global_start_time",
    "global_end_time",
]


def _today_yyyymmdd() -> str:
    return datetime.datetime.now().strftime("%Y_%m_%d")


def _results_csv_path() -> tuple[Path, str]:
    date_str = _today_yyyymmdd()
    base_pid = cfg.PID or "unknown"
    stem = f"{base_pid}_{TASK_NAME}_results_{date_str}.csv"
    return RESULTS_DIR / stem, date_str


def _version_suffix(counter: int) -> str:
    if counter < 10:
        return f"v0{counter}"
    return f"v{counter}"


def create_save() -> None:

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
            suffix = _version_suffix(counter)
            candidate = RESULTS_DIR / f"{base_pid}_{TASK_NAME}_results_{suffix}_{date_str}.csv"
            if not candidate.exists():
                csv_path = candidate
                break
            counter += 1

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)

    _current_results_path = csv_path
    logger.info(f"Results file created at {csv_path}")


def update_save(
    block_name: str,
    trial_type: str,
    condition: str,
    list_name: str,
    color: str,
    trial_class: str,
    case: str,
    congruency: str,
    switching: str,
    stim_repetition: str,
    stimuli: str,
    key_correct: str,
    key_response: str,
    joy_correct: str,
    joy_response: str,
    correct: int | None,
    reaction_time: int | None,
    stimulus_path: str,
) -> None:
    if _current_results_path is not None:
        csv_path = _current_results_path
    else:
        csv_path, _ = _results_csv_path()

    if not csv_path.exists():
        raise FileNotFoundError(f"Results file not found: {csv_path}. Call create_save() first.")

    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        rows = list(csv.reader(rf))
        has_header = bool(rows) and rows[0] == COLUMNS
        data_rows = rows[1:] if has_header else rows
        next_trial_index = len(data_rows) + 1

    src = cfg._input_source
    if src == "key":
        joy_correct = ""
        joy_response = ""
    elif src == "joy":
        if not joy_correct and key_correct:
            joy_correct = key_correct
        if not joy_response and key_response:
            joy_response = key_response
        key_correct = ""
        key_response = ""

    # Derive language from first char of PID: E/e or U/u -> English, M/m -> Espanol, else NA
    def _language_from_pid(pid: str | None) -> str:
        if not pid:
            return NA_STR
        first = str(pid)[0]
        if first in ("U", "u"):
            return "English"
        if first in ("M", "m"):
            return "Espanol"
        return NA_STR

    record = {
        "task": TASK_NAME,
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
        "trial": next_trial_index,
        "block": block_name,
        "trial_type": trial_type,
        "condition": condition,
        "list": list_name,
        "color": color,
        "class": trial_class,
        "case": case,
        "congruency": congruency,
        "switching": switching,
        "stim_repetition": stim_repetition,
        "stimuli": stimuli,
        "key_correct": key_correct,
        "key_response": key_response,
        "joy_correct": joy_correct,
        "joy_response": joy_response,
        "correct": correct,
        "reaction_time": reaction_time,
        "stimulus_path": stimulus_path,
        "start_time": cfg._start_time,
        "end_time": cfg._end_time,
        "global_start_time": cfg.START_TIME,
        "global_end_time": cfg.GLOBAL_END_TIME,
    }

    normalized = {}
    for key in COLUMNS:
        value = record.get(key, "")
        normalized[key] = NA_STR if value in ("", None) else value

    with csv_path.open("a", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        if not has_header:
            writer.writeheader()
        writer.writerow(normalized)


def finalize_save() -> None:
    if _current_results_path is not None:
        csv_path = _current_results_path
    else:
        csv_path, _ = _results_csv_path()

    if not csv_path.exists():
        return

    with csv_path.open("r", newline="", encoding="utf-8") as rf:
        rows = list(csv.DictReader(rf))

    for row in rows:
        row["global_start_time"] = cfg.START_TIME or NA_STR
        row["global_end_time"] = cfg.GLOBAL_END_TIME or NA_STR

    with csv_path.open("w", newline="", encoding="utf-8") as wf:
        writer = csv.DictWriter(wf, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
