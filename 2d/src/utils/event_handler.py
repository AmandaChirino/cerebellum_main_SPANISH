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

        Call this before drawing the stimulus so t0 can be set immediately after flip().
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

        # Keyboard response routing is mapping-dependent.
        # mapping 1: d -> option_1, k -> option_2
        # mapping 2: d -> option_2, k -> option_1
        elif key == pygame.K_d:
            cfg.key_response = "d"
            option = cfg.option_for_key("d")
            if option == 1:
                self._state.option_1 = True
            else:
                self._state.option_2 = True

        elif key == pygame.K_k:
            cfg.key_response = "k"
            option = cfg.option_for_key("k")
            if option == 1:
                self._state.option_1 = True
            else:
                self._state.option_2 = True
    
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

        def _apply_direction_to_option(direction: str) -> None:
            """Map a physical joystick direction to the active version's option."""
            key_name = "d" if direction == "left" else "k"
            option = cfg.option_for_key(key_name)
            if option == 1:
                self._state.option_1 = True
            else:
                self._state.option_2 = True
            cfg.joy_response = direction

        if cfg.JOY_MODE == 2:
            # Layer 2: Directional strength filter (prevents accidental verticals)
            if abs(x) < abs(y) * 0.7:  # Horizontal must be ?70% of vertical strength
                return

            # Process only strong horizontal movements
            angle = (math.degrees(math.atan2(x, -y)) + 360) % 360
            if 180 <= angle < 360:
                _apply_direction_to_option("left")
            elif 0 <= angle < 180:
                _apply_direction_to_option("right")
        elif cfg.JOY_MODE == 4:
            # left: [225, 315)
            if 225 <= angle < 315:
                _apply_direction_to_option("left")

            # right: [45, 135）
            elif 45 <= angle < 135:
                _apply_direction_to_option("right")

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
