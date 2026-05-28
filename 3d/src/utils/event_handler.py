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
        self._suppress_joystick_until_neutral = False

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
        # Reset state every frame
        self._state = ControlState()
        self._input_source_frame = None

        for event in pygame.event.get():
            self._process_event(event)

        self._process_joystick()

        if self._input_source_frame is not None:
            cfg._input_source = self._input_source_frame

        return self._state

    def reset_trial_input(self) -> None:
        """
        Clear queued key events and ignore any already-held joystick direction.

        This should be called immediately after the stimulus has been flipped to
        the screen, before the trial response timer starts.
        """
        pygame.event.clear()
        pygame.event.pump()
        pygame.event.clear()
        cfg.key_response = None
        cfg.joy_response = None
        self._state = ControlState()
        self._input_source_frame = None
        self._suppress_joystick_until_neutral = self._joystick is not None

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

        # Dead zone
        if abs(x) < cfg.DZ_X and abs(y) < cfg.DZ_Y:
            self._suppress_joystick_until_neutral = False
            return

        if self._suppress_joystick_until_neutral:
            return

        # Update input source
        if self._input_source_frame is None:
            self._input_source_frame = "joy"

        # Process joystick input
        angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

        if cfg.JOY_MODE == 2:
            # Double-layer filter for horizontal-only detection.
            # Layer 1: Standard deadzone (prevents micro-movements)
            if abs(x) < cfg.DZ_X and abs(y) < cfg.DZ_Y:
                return

            # Layer 2: Directional strength filter (prevent accidental verticals)
            # Require horizontal magnitude to be at least 70% of vertical magnitude
            if abs(x) < abs(y) * 0.7:
                return

            # Process only strong horizontal movements
            # Angle is measured with 0 at up and increasing clockwise
            if 180 <= angle < 360:
                self._state.option_1 = True  # Left
                cfg.joy_response = "left"
            elif 0 <= angle < 180:
                self._state.option_2 = True  # Right
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
