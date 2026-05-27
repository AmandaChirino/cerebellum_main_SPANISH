import time
from datetime import datetime

import pygame

from core.motor import Motor
from core.sensorimotor import Sensorimotor
from ui.pygame_render import get_participant_id
import utils.config as cfg
from utils.event_handler import reset_joystick_cache
from utils.logger import get_logger
from utils.saves import InitResultCSV


logger = get_logger("./src/core/experiment_flow")


def run() -> None:
    run_started_at = datetime.now()
    pygame.init()

    # Force a full joystick subsystem cycle on macOS.
    # After the previous process calls pygame.quit(), macOS needs time to finish
    # releasing the IOHIDManager HID handle.  If the next process re-opens the
    # device too quickly (especially after a keyboard-only participant that left
    # the joystick axis idle), SDL's IOHIDManager callbacks do not fully re-register
    # and get_axis() returns 0 while JOYAXISMOTION events are never generated.
    #
    # Fix: quit the joystick subsystem (tears down IOHIDManager), sleep 300 ms to
    # let macOS complete the HID lifecycle, then re-init so SDL re-enumerates fresh.
    # Then wait up to 2 s for SDL's JOYDEVICEADDED event — this is SDL's confirmation
    # that the device is fully registered in IOHIDManager and ready to deliver events.
    pygame.joystick.quit()
    time.sleep(0.3)
    pygame.joystick.init()

    # Wait for JOYDEVICEADDED — the reliable signal that SDL has fully re-registered
    # the device and IOHIDManager callbacks are active.
    reset_joystick_cache()
    _joy_count = 0
    _joy_deadline = pygame.time.get_ticks() + 2000
    while pygame.time.get_ticks() < _joy_deadline:
        for _ev in pygame.event.get():
            if _ev.type == pygame.JOYDEVICEADDED:
                _joy_count += 1
        if _joy_count > 0:
            break
        pygame.time.delay(20)
    if _joy_count == 0:
        _joy_count = pygame.joystick.get_count()
    logger.info(f"Joystick count at startup: {_joy_count}")

    try:
        # Set up screen in fullscreen mode
        screen_info = pygame.display.Info()
        screen_width = screen_info.current_w
        screen_height = screen_info.current_h
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)

        # Update meta_parameters with actual screen dimensions
        cfg.SCREEN_W = screen_width
        cfg.SCREEN_H = screen_height

        pygame.mixer.init()

        # Legacy variables (no longer used for data saving - trials save individually)
        all_results = []
        all_acc = []

        # Record global task start time (yyyy-mm-dd-hh-mm-ss)
        cfg.START_TIME = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        def end_and_save():
            cfg._end_time = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            pygame.time.wait(1000)
            pygame.quit()
            quit()

        def run_sensorimotor():
            logger.info("Transition: entering sensorimotor task")
            sensorimotor = Sensorimotor(screen, all_results, all_acc, version=cfg.MAPPING)
            sensorimotor.run_sm_segment1(lambda: sensorimotor.run_sm_segment2(lambda: end_and_save()))

        def run_motor():
            logger.info("Transition: entering motor task")
            motor = Motor(screen, all_results, all_acc, version=cfg.MAPPING)
            motor.run_m_segment1(
                lambda: motor.run_m_segment3(
                    lambda: motor.run_m_segment4(lambda: run_sensorimotor())
                )
            )
        # Get participant ID and complete Admin phase (group/session/DH/UH)
        screen = get_participant_id(screen)
        participant_id = cfg.PID or ""


        InitResultCSV("results.csv", participant_id)
        run_motor()
    finally:
        elapsed_seconds = int((datetime.now() - run_started_at).total_seconds())
        elapsed_minutes = elapsed_seconds / 60
        logger.info(
            f"Total task duration: {elapsed_minutes:.2f} minutes ({elapsed_seconds} seconds)"
        )


if __name__ == "__main__":
    run()
