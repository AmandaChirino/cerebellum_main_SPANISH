"""
Centralized input-event abstraction that converts raw user interactions into
frame-level control signals.
"""


from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

import utils.config as cfg
from utils.logger import get_logger


logger = get_logger("./src/ui/pygame_render")


@dataclass
class ControlState:
    """
    Snapshot of control signals for a single frame.

    Fields:
        quit: request to exit pygame
        toggle_full_screen: toggle fullscreen/windowed display
        is_left: select left option (cfg.DH / cfg.UH = "left")
        is_right: select right option (cfg.DH / cfg.UH = "right")
        next_page: advance to next page
        option_1: response option 1
        option_2: response option 2
    """
    quit: bool = False
    toggle_full_screen: bool = False
    is_left: bool = False
    is_right: bool = False
    next_page: bool = False
    x_raw: float = 0.0
    y_raw: float = 0.0

    option_1: bool = False
    option_2: bool = False
    # option_3: bool = False              # response option_3
    # option_4: bool = False              # response option_4


class EventHandler:
    """
    Centralized event handler for collecting and normalizing input events.
    """
    def __init__(self) -> None:
        self._state = ControlState()  # control state for current frame
        self._input_source_frame: str | None = None  # key = keyboard / joy = joystick

        # Initialize joystick
        pygame.joystick.init()
        if pygame.joystick.get_count() > 0:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()
            logger.info(f"Joystick detected: {self._joystick.get_name()}")
        else:
            self._joystick = None
            logger.warning("No joystick detected — keyboard only")

    def poll(self) -> ControlState:
        """
        Poll pygame events and return a control-state snapshot for the current frame.

        :return: ControlState
        """
        # Reset state every frame
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
        # Arrow keys mapped to joystick directions (treated as 'joy' input)
        elif key == pygame.K_UP:
            self._input_source_frame = "joy"
            cfg.joy_response = "up"
        elif key == pygame.K_DOWN:
            self._input_source_frame = "joy"
            cfg.joy_response = "down"
        elif key == pygame.K_LEFT:
            self._input_source_frame = "joy"
            cfg.joy_response = "left"
        elif key == pygame.K_RIGHT:
            self._input_source_frame = "joy"
            cfg.joy_response = "right"

        # Select [Option 2] for response to stimuli (k)
        elif key == pygame.K_k:
            self._state.option_2 = True
            cfg.key_response = pygame.key.name(key)
    
    def _process_joystick(self) -> None:
        """
        Handle joystick input.
        """
        if self._joystick is None:
            return

        pygame.event.pump()

        x = self._joystick.get_axis(0)
        y = self._joystick.get_axis(1)
        self._state.x_raw = x
        self._state.y_raw = y

        # Dead zone
        if abs(x) < cfg.DZ_X and abs(y) < cfg.DZ_Y:
            return

        # Update input source
        if self._input_source_frame is None:
            self._input_source_frame = "joy"

        # Process joystick input
        angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

        if cfg.JOY_MODE == 2:
            # Keep left/right response zones, but exclude bottom 90 degrees:
            # no binding in [135, 225).
            # left: [225, 360)
            if 225 <= angle < 360:
                self._state.option_1 = True
                cfg.joy_response = "left"

            # right: [0, 135)
            elif 0 <= angle < 135:
                self._state.option_2 = True
                cfg.joy_response = "right"

        elif cfg.JOY_MODE == 4:
            # left: [225, 315)
            if 225 <= angle < 315:
                self._state.option_1 = True
                cfg.joy_response = "left"

            # right: [45, 135）
            elif 45 <= angle < 135:
                self._state.option_2 = True
                cfg.joy_response = "right"

            # up: [0. 45) + [315, 360)
            elif angle >= 315 or angle < 45:
                self._state.option_3 = True
                cfg.joy_response = "up"

            # down: [135. 225)
            elif 135 <= angle < 225:
                self._state.option_4 = True
                cfg.joy_response = "down"

        else:
            logger.error("Invalid JOY_MODE selected")


