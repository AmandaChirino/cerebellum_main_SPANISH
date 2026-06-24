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

import pygame  # type: ignore[import]
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
    mapping_1: bool = False
    mapping_2: bool = False
    next_page: bool = False

    is_left: bool = False
    is_right: bool = False

    option_1: bool = False
    option_2: bool = False
    option_3: bool = False
    option_4: bool = False
    key: str = ""


class EventHandler:
    """
    Centralized event handler for collecting and normalizing input events.

    The EventHandler polls pygame events each frame and converts them into a ControlState object that can be safely consumed by the experiment loop.
    """

    def __init__(self) -> None:
        self._state = ControlState()  # control state for current frame
        self._input_source_frame: str | None = None  # key = keyboard / joy = joystick
        self.last_axis_x: float = 0.0
        self.last_axis_y: float = 0.0

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
        self._input_source_frame = None

        for event in pygame.event.get():
            self._process_event(event)
        
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
            self._state.next_page = True

        # Select [Left hand] (L)
        elif key == pygame.K_l:
            self._state.is_left = True

        # Select [Right hand] (R)
        elif key == pygame.K_r:
            self._state.is_right = True

        # Select [Option 1] for response to stimuli (d)
        elif key == pygame.K_d:
            self._state.option_1 = True
            cfg.key_response = pygame.key.name(key)

        # Select [Option 2] for response to stimuli (k)
        elif key == pygame.K_k:
            self._state.option_2 = True
            cfg.key_response = pygame.key.name(key)
    
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
        self.last_axis_x = x
        self.last_axis_y = y

        # Layer 1: Standard deadzone (prevents micro-movements)
        if abs(x) < cfg.DZ_X and abs(y) < cfg.DZ_Y:
            return

        # Layer 2: Directional strength filter (prevents accidental verticals)
        if abs(x) < abs(y) * 0.7:  # Horizontal must be >=70% of vertical strength
            return

        # Update input source
        if self._input_source_frame is None:
            self._input_source_frame = "joy"

        angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

        if cfg.js_mode == 2:
            # left: [180,360)
            if 180 <= angle < 360:
                self._state.option_1 = True
                self._state.key = "left"
                cfg.joy_response = "left"
            
            # right: [0,180)
            elif 0 <= angle < 180:
                self._state.option_2 = True
                self._state.key = "right"
                cfg.joy_response = "right"
        else:
            logger.error("Invalid JOY_MODE selected")
