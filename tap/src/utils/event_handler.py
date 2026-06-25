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
from utils.logger import get_logger
import math
import utils.config as cfg

logger = get_logger("./src/ui/pygame_render")


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
    version_1: bool = False
    version_2: bool = False
    next_page: bool = False
    pressed: bool = False
    # option_2: bool = False
    # option_3: bool = False
    # option_4: bool = False


class EventHandler:
    """
    Centralized event handler for collecting and normalizing input events.

    The EventHandler polls pygame events each frame and converts them into a ControlState object that can be safely consumed by the experiment loop.
    """

    def __init__(self) -> None:
        self._state = ControlState()
        self._keys_down = set()
        self._joystick = None

        if getattr(cfg, "USE_JOYSTICK", False):
            # Joystick support is optional; TAP normally runs keyboard-only.
            pygame.joystick.init()
            if pygame.joystick.get_count() > 0:
                self._joystick = pygame.joystick.Joystick(0)
                self._joystick.init()

    def poll(self) -> ControlState:
        """
        Poll pygame events and return a control-state snapshot for the current frame.

        :return: ControlState
        """
        # Reset state every frame (edge-triggered behavior)
        self._state = ControlState()
        self._input_source_frame = None

        for event in pygame.event.get():
            self._process_event(event)

        if self._joystick is not None:
            self._process_joystick()
        
        if self._input_source_frame is not None:
            cfg._input_source = self._input_source_frame

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
            # Update input source
            self._input_source_frame = "key"
            # Process keyboard input
            self._process_keydown(event.key)

        if event.type == pygame.KEYUP:         
            self._keys_down.discard(event.key)    

    def _process_keydown(self, key: int) -> None:
        """
        Handle keyboard input.

        :param key: Pygame key code (e.g., pygame.K_ESCAPE)
        :type key: int
        """
        # Toggle full screen (ESC)
        if key == pygame.K_ESCAPE:
            self._state.toggle_full_screen = True

        # Proceed to next page (SPACE)
        elif key == pygame.K_SPACE:
            if key not in self._keys_down:    
                self._state.next_page = True
                self._state.pressed = True
                cfg.key_response = pygame.key.name(key)
            self._keys_down.add(key)

        # Select [Left hand] (L)
        elif key == pygame.K_l:
            self._state.is_left = True

        # Select [Right hand] (R)
        elif key == pygame.K_r:
            self._state.is_right = True

    def reset_pressed_state(self) -> None:
        """Reset key-hold tracking so the next KEYDOWN is treated as a fresh press."""
        self._keys_down.discard(pygame.K_SPACE)

    def _process_joystick(self) -> None:
        """
        Read joystick axis input and map directional movement to option flags.
        Prevents accidental up/down movements by using strict deadzone logic.

        :return: None
        """
        if self._joystick is None:
            return

        pygame.event.pump()

        x = self._joystick.get_axis(0)
        y = self._joystick.get_axis(1)
        dz_x = getattr(cfg, "dz_x", getattr(cfg, "DZ_X", 0.6))
        dz_y = getattr(cfg, "dz_y", getattr(cfg, "DZ_Y", 0.6))
        js_mode = getattr(cfg, "js_mode", getattr(cfg, "JOY_MODE", 2))

        # Strict dead zone - prevents accidental movements when hand is resting
        if abs(x) < dz_x and abs(y) < dz_y:
            return

        # Additional check: require primarily horizontal movement
        # Only register movement if horizontal movement is significantly stronger than vertical
        if abs(x) < abs(y) * 0.7:  # Horizontal must be at least 70% of vertical strength
            return

        # Update input source
        if self._input_source_frame is None:
            self._input_source_frame = "joy"

        angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

        if js_mode == 2:
            # left: [180,360)
            if 180 <= angle < 360:
                self._state.option_1 = True
                self._state.key = "left"
            
            # right: [0,180)
            elif 0 <= angle < 180:
                self._state.option_2 = True
                self._state.key = "right"
        else:
            logger.error("Invalid JOY_MODE selected")
