# ./src/utils/event_handler.py
"""
This module defines a centralized event handling abstraction for the experiment.

The EventHandler is responsible for:
- Collecting raw pygame events from external input sources.
- Translating device-specific events into standardized, high-level control signals.
- Providing a clean interface between low-level input events and experiment logic.

Design principles:
- Decoupling: experiment flow should not directly depend on pygame event types.
- Edge-trigger semantics: control flags are valid for a single frame only.
- Passive role: this module does NOT execute actions or call external functions.
"""


from __future__ import annotations

import pygame
from dataclasses import dataclass
import math

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
    mapping_1: bool = False
    mapping_2: bool = False
    next_page: bool = False
    option_1: bool = False
    option_2: bool = False
    option_3: bool = False
    option_4: bool = False


class EventHandler:
    """
    Centralized event handler for collecting and normalizing input events.

    The EventHandler polls pygame events each frame and converts them into a ControlState object that can be safely consumed by the experiment loop.
    """

    def __init__(self) -> None:
        self._state = ControlState()

        # Joystick disabled - only using keyboard
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
        
        # Joystick processing disabled - only using keyboard
        # self._process_joystick()

        return self._state

    def _process_event(self, event: pygame.event.Event) -> None:
        """
        Translate a single pygame event into control signals.

        :param event: A single pygame event retrieved from the event queue
        :type event: pygame.event.Event

        :return: None
        """
        # Quit pygame (x)
        if event.type == pygame.QUIT:
            self._state.quit = True
            return

        # Handle keypress (keydown)
        if event.type == pygame.KEYDOWN:
            self._process_keydown(event.key)

    def _process_keydown(self, key: int) -> None:
        """
        Handle keyboard keydown events and update control flags.

        :param key: Pygame key code (e.g., pygame.K_ESCAPE)
        :type key: int

        :return: None
        """
        # Toggle full screen (ESC)
        if key == pygame.K_ESCAPE:
            self._state.toggle_full_screen = True
        
        # Select [Mapping 1] (L)
        if key == pygame.K_l:
            self._state.mapping_1 = True
        
        # Select [Mapping 2] (R)
        elif key == pygame.K_r:
            self._state.mapping_2 = True

        # Proceed to next page (SPACE) and Select [Option 1] - MATCH response
        elif key == pygame.K_SPACE:
            self._state.next_page = True
            self._state.option_1 = True
        
        # TODO: Add additional input mappings and proper docstrings if necessary
    
    def _process_joystick(self) -> None:
        """
        Read joystick axis input and map directional movement to option flags.

        :return: None
        """
        if self._joystick is None:
            return

        pygame.event.pump()

        x = self._joystick.get_axis(0)
        y = self._joystick.get_axis(1)

        # Dead zone
        if abs(x) < 0.5 and abs(y) < 0.5:
            return

        angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

        if cfg.js_mode == 2:
            # left: [180,360)
            if 180 <= angle < 360:
                self._state.option_1 = True
            
            # right: [0,180)
            elif 0 <= angle < 180:
                self._state.option_2 = True

        elif cfg.js_mode == 4:
            # left: [225, 315)
            if 225 <= angle < 315:
                self._state.option_1 = True

            # right: [45, 135）
            elif 45 <= angle < 135:
                self._state.option_2 = True

            # up: [0. 45) + [315, 360)
            elif angle >= 315 or angle < 45:
                self._state.option_3 = True

            # down: [125. 225)
            elif 135 <= angle < 225:
                self._state.option_4 = True
