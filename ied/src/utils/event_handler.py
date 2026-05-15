# ./src/utils/event_handler.py
"""
Centralized event handling abstraction for the experiment.

The EventHandler is responsible for:
- Collecting raw pygame events from external input sources.
- Translating device-specific events into standardized, high-level control signals.
- Providing a clean interface between low-level input events and experiment logic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
import pygame

import utils.config as cfg


@dataclass
class ControlState:
    """
    Snapshot of control signals for a single frame.

    All fields are edge-triggered:
    - A value of True indicates that the corresponding input event occurred during the current frame.
    - All fields are reset at the beginning of the next polling cycle.
    """
    quit: bool = False
    toggle_full_screen: bool = False
    next_page: bool = False
    left_hand: bool = False
    right_hand: bool = False

    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    input_source: str | None = None
    response_dir: str | None = None

    enter: bool = False
    backspace: bool = False
    text: str = ""


class EventHandler:
    """
    Centralized event handler for collecting and normalizing input events.
    """

    def __init__(self) -> None:
        self._state = ControlState()

        # Initialize joystick
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()
        else:
            self._joystick = None

    def poll(self) -> ControlState:
        """
        Poll pygame events and return a control-state snapshot for the current frame.

        :return: ControlState
        """
        # Reset state every frame (edge-triggered behavior)
        self._state = ControlState()

        for event in pygame.event.get():
            self._process_event(event)

        self._process_joystick()

        return self._state

    def _process_event(self, event: pygame.event.Event) -> None:
        """
        Translate a single pygame event into control signals.
        """
        if event.type == pygame.QUIT:
            self._state.quit = True
            return

        if event.type == pygame.KEYDOWN:
            self._process_keydown(event)

    def _process_keydown(self, event: pygame.event.Event) -> None:
        """
        Handle keyboard keydown events and update control flags.
        """
        key = event.key

        # Toggle full screen (ESC)
        if key == pygame.K_ESCAPE:
            self._state.toggle_full_screen = True
            return

        # Proceed to next page (SPACE)
        if key == pygame.K_SPACE:
            self._state.next_page = True
            return

        # Confirm input (ENTER)
        if key == pygame.K_RETURN:
            self._state.enter = True
            return

        # Delete input (BACKSPACE)
        if key == pygame.K_BACKSPACE:
            self._state.backspace = True
            return

        # Select [Left hand] (L)
        if key == pygame.K_l:
            self._state.left_hand = True
            return

        # Select [Right hand] (R)
        if key == pygame.K_r:
            self._state.right_hand = True
            return

        # Arrow inputs
        if key == pygame.K_UP:
            self._state.up = True
            self._state.input_source = "keyboard"
            self._state.response_dir = "up"
            return
        if key == pygame.K_DOWN:
            self._state.down = True
            self._state.input_source = "keyboard"
            self._state.response_dir = "down"
            return
        if key == pygame.K_LEFT:
            self._state.left = True
            self._state.input_source = "keyboard"
            self._state.response_dir = "left"
            return
        if key == pygame.K_RIGHT:
            self._state.right = True
            self._state.input_source = "keyboard"
            self._state.response_dir = "right"
            return

        # Text input
        if event.unicode:
            self._state.text += event.unicode

    def _process_joystick(self) -> None:
        """
        Read joystick axis input and map directional movement to arrow flags.
        """
        if self._joystick is None:
            return

        pygame.event.pump()

        x = self._joystick.get_axis(0)
        y = self._joystick.get_axis(1)

        # Dead zone
        if abs(x) < cfg.DZ_X and abs(y) < cfg.DZ_Y:
            return

        angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

        if cfg.JS_MODE == 4:
            # left: [225, 315)
            if 225 <= angle < 315:
                self._state.left = True
                self._state.input_source = "joystick"
                self._state.response_dir = "left"
                return

            # right: [45, 135)
            if 45 <= angle < 135:
                self._state.right = True
                self._state.input_source = "joystick"
                self._state.response_dir = "right"
                return

            # up: [315, 360) + [0, 45)
            if angle >= 315 or angle < 45:
                self._state.up = True
                self._state.input_source = "joystick"
                self._state.response_dir = "up"
                return

            # down: [135, 225)
            if 135 <= angle < 225:
                self._state.down = True
                self._state.input_source = "joystick"
                self._state.response_dir = "down"
                return
