"""Practice block wrapper for target mental-rotation task."""

from __future__ import annotations

from pathlib import Path

import pygame

from utils.event_handler import EventHandler
from core.test import run_experimental_block


def run_practice(
    screen: pygame.Surface,
    event_handler: EventHandler,
    stimuli_root: Path,
) -> tuple[pygame.Surface, float]:
    """Run practice block with trial-level feedback."""
    return run_experimental_block(
        screen=screen,
        event_handler=event_handler,
        phase_label="practice",
        block_name="practice",
        stimuli_root=stimuli_root,
        show_trial_feedback=True,
        break_duration_ms=0,
    )
