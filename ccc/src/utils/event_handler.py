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

# ---------------------------------------------------------------------------
# Module-level joystick cache — initialised once and reused by every
# EventHandler instance.  Repeated calls to pygame.joystick.init() on
# macOS trigger HID re-enumeration, which causes get_count() to return 0
# briefly and permanently poisons the cache with None.
_joystick_cache: pygame.joystick.JoystickType | None = None
_joystick_initialised: bool = False


def _get_joystick() -> pygame.joystick.JoystickType | None:
    """Return the cached joystick, initializing once on first call.

    Deliberately does NOT call pygame.joystick.init() — pygame.init() already
    covers this.  Calling it again on macOS forces a HID re-enumeration: during
    that brief window get_count() returns 0, the cache is set to None, and the
    joystick becomes permanently undetected for the rest of the process.
    """
    global _joystick_cache, _joystick_initialised

    # If the joystick subsystem was torn down (e.g. after pygame.quit() +
    # pygame.init()), the cached object is stale — reset so we re-acquire.
    if _joystick_initialised and not pygame.joystick.get_init():
        _joystick_cache = None
        _joystick_initialised = False

    if not _joystick_initialised:
        count = pygame.joystick.get_count()
        if count == 0:
            pygame.time.delay(150)
            count = pygame.joystick.get_count()
        if count > 0:
            _joystick_cache = pygame.joystick.Joystick(0)
            _joystick_cache.init()
            logger.info(f"Joystick acquired: {_joystick_cache.get_name()}")
        else:
            logger.warning("No joystick found — axis input disabled.")
        _joystick_initialised = True

    return _joystick_cache


def reset_joystick_cache() -> None:
    """Force a fresh joystick acquisition on the next EventHandler creation.
    Call this at the start of each experiment run."""
    global _joystick_cache, _joystick_initialised
    _joystick_cache = None
    _joystick_initialised = False


@dataclass
class ControlState:
    """
    Snapshot of control signals for a single frame.

    Fields:
        quit: request to exit pygame
        toggle_full_screen: toggle fullscreen/windowed display
        is_left: select left version (cfg.DH / cfg.UH = "left")
        is_right: select right version (cfg.DH / cfg.UH = "right")
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
    confirm: bool = False
    backspace: bool = False
    text_input: str = ""
    # option_3: bool = False              # response option_3
    # option_4: bool = False              # response option_4


class EventHandler:
    """
    Centralized event handler for collecting and normalizing input events.
    """
    def __init__(self) -> None:
        self._state = ControlState()  # control state for current frame
        self._input_source_frame: str | None = None  # key = keyboard / joy = joystick

        # Reuse the single cached joystick instance (initialised once)
        self._joystick = _get_joystick()

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

        if not (self._state.option_1 or self._state.option_2):
            pressed = pygame.key.get_pressed()
            if pressed[pygame.K_d]:
                self._state.option_1 = True
                cfg.key_response = "d"
                if self._input_source_frame is None:
                    self._input_source_frame = "key"
            elif pressed[pygame.K_k]:
                self._state.option_2 = True
                cfg.key_response = "k"
                if self._input_source_frame is None:
                    self._input_source_frame = "key"

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
            self._process_text_input(event)

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

        # Confirm input / continue (ENTER)
        elif key == pygame.K_RETURN:
            self._state.confirm = True

        # Delete one character (BACKSPACE)
        elif key == pygame.K_BACKSPACE:
            self._state.backspace = True

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

    def _process_text_input(self, event: pygame.event.Event) -> None:
        """
        Collect printable text input for PID or similar text-entry screens.
        """
        if event.type != pygame.KEYDOWN:
            return
        if not hasattr(event, "unicode"):
            return

        if event.unicode and event.unicode.isprintable():
            self._state.text_input += event.unicode
    
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
            return

        # Directional strength filter: horizontal must be at least 70% as strong
        # as vertical, preventing accidental diagonal/up-down registrations.
        if abs(x) < abs(y) * 0.7:
            return

        # Update input source
        if self._input_source_frame is None:
            self._input_source_frame = "joy"

        # Process joystick input
        angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

        if cfg.JOY_MODE == 2:
            # left: [180,360)
            if 180 <= angle < 360:
                self._state.option_1 = True
                cfg.joy_response = "left"

            # right: [0,180)
            elif 0 <= angle < 180:
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
