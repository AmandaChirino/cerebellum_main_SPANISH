"""
Centralized input-event abstraction that converts raw user interactions into
frame-level control signals.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

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


# Module-level joystick cache — initialised once and reused by every
# EventHandler instance.  Repeated calls to pygame.joystick.init() on
# macOS trigger HID re-enumeration, which causes get_count() to return 0
# briefly and permanently poisons the cache with None.
_joystick_cache: pygame.joystick.JoystickType | None = None
_joystick_initialised: bool = False


def _get_joystick() -> pygame.joystick.JoystickType | None:
    """
    Return the cached joystick, initializing once on first call.

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
        # pygame.init() (called in experiment_flow) already initialized the
        # joystick subsystem; just acquire the Joystick object.
        count = pygame.joystick.get_count()
        if count == 0:
            # Give SDL a moment to finish its internal device scan on macOS.
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


class EventHandler:
    """
    Centralized event handler for collecting and normalizing input events.
    
    :param expected_direction: Optional filter for motor tasks - only accepts joystick movement
                               in the specified direction ('left' or 'right'). Use None to accept
                               any direction (default for sensorimotor).
    :param expected_key: Optional filter for motor tasks - only accepts this specific key
                         (pygame.K_d or pygame.K_k). Use None to accept any key (default for sensorimotor).
    """
    def __init__(self, expected_direction: str | None = None, expected_key: int | None = None) -> None:
        self._state = ControlState()  # control state for current frame
        self._input_source_frame: str | None = None  # key = keyboard / joy = joystick
        self._expected_direction = expected_direction  # 'left', 'right', or None
        self._expected_key = expected_key  # pygame.K_d, pygame.K_k, or None

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
            # Motor key filter: only accept if this is the expected key
            if self._expected_key is None or self._expected_key == pygame.K_d:
                self._state.option_1 = True
                cfg.key_response = pygame.key.name(key)

        # Select [Option 2] for response to stimuli (k)
        elif key == pygame.K_k:
            # Motor key filter: only accept if this is the expected key
            if self._expected_key is None or self._expected_key == pygame.K_k:
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
        Handle joystick input for horizontal (left/right) responses.

        Two-layer filter to prevent accidental up/down movements:
          Layer 1 — deadzone: ignores micro-movements on both axes.
          Layer 2 — directional strength: horizontal movement must be at least
                    70% as strong as vertical, preventing diagonal registrations.
        """
        if self._joystick is None:
            return

        pygame.event.pump()

        x = self._joystick.get_axis(0)
        y = self._joystick.get_axis(1)

        # Layer 1: deadzone — ignore micro-movements on both axes.
        if abs(x) < cfg.DZ_X and abs(y) < cfg.DZ_Y:
            return

        # Layer 2: directional strength — horizontal must be ≥70% of vertical.
        if abs(x) < abs(y) * 0.7:
            return

        # Update input source
        self._input_source_frame = "joy"

        angle = (math.degrees(math.atan2(x, -y)) + 360) % 360

        if cfg.JOY_MODE == 2:
            if 180 <= angle < 360:  # left
                if self._expected_direction is None or self._expected_direction == "left":
                    self._state.option_1 = True
                    cfg.joy_response = "left"
            elif 0 <= angle < 180:  # right
                if self._expected_direction is None or self._expected_direction == "right":
                    self._state.option_2 = True
                    cfg.joy_response = "right"
        else:
            logger.error("Invalid JOY_MODE selected")
