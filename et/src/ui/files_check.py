# ./src/ui/files_check.py
"""
Stimulus files check.

This module verifies that every video and preview image listed in the stimuli CSV exists
before the session starts, and shows the missing ones on screen.
"""


from __future__ import annotations
from pathlib import Path
import pandas as pd
import pygame

import utils.paths as paths
from core.test import preview_image_path
from ui.monitor_check import _show_message, _wait_key
from utils.logger import get_logger


logger = get_logger("./src/ui/files_check")

MAX_SHOWN = 8   # missing files listed on screen; all of them go to the log


def find_missing_files(csv_path: Path) -> list[str]:
    """
    List the files of the stimuli CSV that are not on disk.

    :param csv_path: Path to the stimPaths CSV (columns: video, pre_snapshot)
    :return: Missing items, one text line each (empty if everything is there)
    """
    if not csv_path.is_file():
        return [f"CSV: {csv_path.name}"]

    missing = []
    df = pd.read_csv(csv_path)
    for row, (video, snapshot) in enumerate(zip(df["video"], df["pre_snapshot"]), start=2):
        if not isinstance(video, str) or not isinstance(snapshot, str):
            missing.append(f"CSV fila {row}: celda vacía")
            continue
        # The image listed in the CSV and the one the test block loads
        wanted = [("Video", paths.RESOURCES_DIR / video),
                  ("Imagen", paths.RESOURCES_DIR / snapshot),
                  ("Imagen", preview_image_path(video))]
        for label, file in wanted:
            line = f"{label}: {file.relative_to(paths.RESOURCES_DIR).as_posix()}"
            if not file.is_file() and line not in missing:
                missing.append(line)
    return missing


def check_stimuli_files(screen: pygame.Surface, csv_path: Path) -> None:
    """
    Check the stimulus files and, if any is missing, show them on screen until ESC is pressed.

    :param screen: Current display surface
    :param csv_path: Path to the stimPaths CSV
    """
    missing = find_missing_files(csv_path)
    if not missing:
        return

    logger.error("Missing stimulus files: %s", missing)
    lines = ["Faltan archivos de la tarea", ""] + missing[:MAX_SHOWN]
    if len(missing) > MAX_SHOWN:
        lines.append(f"... y {len(missing) - MAX_SHOWN} más")
    lines += ["", "Copia los archivos a resources/ y abre la tarea de nuevo", "ESC: salir"]

    _show_message(screen, lines)
    _wait_key((pygame.K_ESCAPE,))
    pygame.quit()
    raise SystemExit
