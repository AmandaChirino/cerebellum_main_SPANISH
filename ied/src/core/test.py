# ./src/core/test.py
"""
Test block execution logic using pygame.
"""

from __future__ import annotations

from pathlib import Path
import random
import pygame

import utils.config as cfg
from utils.logger import get_logger
from utils.event_handler import EventHandler
from utils.saves import update_save
from ui.pygame_renderer import (
    toggle_full_screen,
    show_ied_ui,
    place_single_image,
    place_side_by_side_images,
    place_overlapped_images,
    show_feedback,
)


logger = get_logger("./src/core/test")


def _flush_input() -> None:
    """Flush all pending pygame input events."""
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _response_from_state(state) -> tuple[int | None, str | None, str | None]:
    if state.up:
        return 1, "up", state.input_source
    if state.down:
        return 2, "down", state.input_source
    if state.left:
        return 3, "left", state.input_source
    if state.right:
        return 4, "right", state.input_source
    return None, None, None


def _correct_dir_from_index(correct_ind: int | None) -> str | None:
    mapping = {1: "up", 2: "down", 3: "left", 4: "right"}
    return mapping.get(correct_ind)


def _handle_response(
    phase: str,
    response: int,
    response_dir: str | None,
    input_source: str | None,
    correct_stimulus: Path,
    incorrect_stimulus: Path,
    correct_buffer: Path | None = None,
    incorrect_buffer: Path | None = None,
    reaction_time: int | None = None,
) -> bool:
    """
    Update counts and save results. Return whether response was correct.
    """
    correct_dir = _correct_dir_from_index(cfg.correct_ind)

    if response == cfg.correct_ind:
        cfg.correct_count += 1
        cfg.trial_count += 1
        update_save(
            phase, 1, correct_dir, response_dir, input_source,
            str(correct_stimulus.name), str(incorrect_stimulus.name),
            str(correct_buffer.name) if correct_buffer else None,
            str(incorrect_buffer.name) if incorrect_buffer else None,
            reaction_time=reaction_time,
        )
        return True

    cfg.correct_count = 0
    cfg.trial_count += 1
    update_save(
        phase, 0, correct_dir, response_dir, input_source,
        str(correct_stimulus.name), str(incorrect_stimulus.name),
        str(correct_buffer.name) if correct_buffer else None,
        str(incorrect_buffer.name) if incorrect_buffer else None,
        reaction_time=reaction_time,
    )
    return False


def run_single_stimulus_phase(
    screen: pygame.Surface,
    phase: str,
    stimuli: dict[str, Path],
    event_handler: EventHandler,
    show_fe_fb: bool,
) -> pygame.Surface:
    """
    Run one phase with only one stimulus image (P1 / P2).
    """
    running = True
    waiting = True
    trial_start: int | None = None
    clock = pygame.time.Clock()
    feedback_until = 0
    fe_feedback_until = -1
    feedback_is_correct = None
    
    is_first_trial_p1 = (phase == "P1")
    first_trial_done = False
    show_first_trial_feedback = False
    first_trial_feedback_until = -1
    first_trial_correct = None

    correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
    cfg.correct_ind = correct_ind
    cfg.correct_count = 0
    cfg.trial_count = 0

    font = pygame.font.SysFont(None, cfg.FONT_SIZE)
    reminder_font = pygame.font.SysFont(None, cfg.LARGE_FONT_SIZE)

    while running:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()

        if waiting:
            response, response_dir, input_source = _response_from_state(state)
            if response is not None and response in (correct_ind, incorrect_ind):
                correct_img = stimuli[f"{phase}_CORRECT"]
                incorrect_img = stimuli[f"{phase}_INCORRECT"]
                reaction_time = pygame.time.get_ticks() - trial_start if trial_start is not None else None
                feedback_is_correct = _handle_response(phase, response, response_dir, input_source, correct_img, incorrect_img, reaction_time=reaction_time)
                feedback_until = pygame.time.get_ticks() + cfg.FB_DURATION
                if show_fe_fb and not feedback_is_correct:
                    fe_feedback_until = pygame.time.get_ticks() + cfg.FE_FB_DURATION
                waiting = False
                if is_first_trial_p1 and not first_trial_done:
                    show_first_trial_feedback = True
                    first_trial_feedback_until = pygame.time.get_ticks() + 3000
                    first_trial_correct = feedback_is_correct
                    first_trial_done = True

        show_ied_ui(screen)
        correct_img = stimuli[f"{phase}_CORRECT"]
        incorrect_img = stimuli[f"{phase}_INCORRECT"]
        place_single_image(screen, correct_img, correct_ind)
        place_single_image(screen, incorrect_img, incorrect_ind)

        if waiting and is_first_trial_p1 and not first_trial_done:
            text_surface = reminder_font.render("Solo adivina la primera vez", True, cfg.COCO_RGB)
            text_rect = text_surface.get_rect(center=(screen.get_width() // 2, int(screen.get_height() * 0.1)))
            screen.blit(text_surface, text_rect)

        now = pygame.time.get_ticks()
        
        if show_first_trial_feedback:
            show_feedback(screen, first_trial_correct)
            if first_trial_correct:
                msg = "Good, now keep on trying to get it correct."
            else:
                msg = "Bad luck, now try to get it correct."
            text_surface = reminder_font.render(msg, True, cfg.COCO_RGB)
            text_rect = text_surface.get_rect(center=(screen.get_width() // 2, int(screen.get_height() * 0.1)))
            screen.blit(text_surface, text_rect)
            if now >= first_trial_feedback_until:
                show_first_trial_feedback = False
                feedback_is_correct = None
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.wait(cfg.ISI_MS)
                pygame.event.clear()
                correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
                cfg.correct_ind = correct_ind
                waiting = True
                trial_start = None
        elif feedback_is_correct is not None:
            if not feedback_is_correct and now < fe_feedback_until:
                show_feedback(screen, feedback_is_correct)
                text_surface = reminder_font.render("Remember, the rule will change", True, cfg.COCO_RGB)
                text_rect = text_surface.get_rect(center=(screen.get_width() // 2, int(screen.get_height() * 0.1)))
                screen.blit(text_surface, text_rect)
                show_fe_fb = False
            elif now < feedback_until:
                show_feedback(screen, feedback_is_correct)
            else:
                feedback_is_correct = None
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.wait(cfg.ISI_MS)
                pygame.event.clear()

                correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
                cfg.correct_ind = correct_ind
                waiting = True
                trial_start = None

        if cfg.correct_count >= cfg.CORRECT_REQUIREMENT:
            if pygame.time.get_ticks() >= feedback_until:
                logger.info("Passed phase %s", phase)
                running = False
        elif cfg.trial_count >= cfg.FORCE_QUIT_LIMIT:
            if pygame.time.get_ticks() >= feedback_until:
                logger.info("Trial count: %s -> force quit limit reached", cfg.trial_count)
                running = False
                cfg.force_quit = True

        pygame.display.flip()
        if waiting and trial_start is None:
            trial_start = pygame.time.get_ticks()
        clock.tick(60)

    return screen


def run_side_by_side_multiple_stimulus_phase(
    screen: pygame.Surface,
    phase: str,
    stimuli: dict[str, Path],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run one phase with side-by-side stimuli (P3).
    """
    running = True
    waiting = True
    trial_start: int | None = None
    clock = pygame.time.Clock()
    feedback_until = 0
    feedback_is_correct = None

    buffer1_img, buffer2_img = random.sample(
        [stimuli[f"{phase}_BUFFER1"], stimuli[f"{phase}_BUFFER2"]],
        2,
    )

    correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
    cfg.correct_ind = correct_ind
    cfg.correct_count = 0
    cfg.trial_count = 0

    while running:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()

        if waiting:
            response, response_dir, input_source = _response_from_state(state)
            if response is not None and response in (correct_ind, incorrect_ind):
                correct_img = stimuli[f"{phase}_CORRECT"]
                incorrect_img = stimuli[f"{phase}_INCORRECT"]
                reaction_time = pygame.time.get_ticks() - trial_start if trial_start is not None else None
                feedback_is_correct = _handle_response(phase, response, response_dir, input_source, correct_img, incorrect_img, buffer1_img, buffer2_img, reaction_time=reaction_time)
                feedback_until = pygame.time.get_ticks() + cfg.FB_DURATION
                waiting = False

        show_ied_ui(screen)
        correct_img = stimuli[f"{phase}_CORRECT"]
        incorrect_img = stimuli[f"{phase}_INCORRECT"]
        place_side_by_side_images(screen, correct_img, buffer1_img, correct_ind)
        place_side_by_side_images(screen, incorrect_img, buffer2_img, incorrect_ind)

        now = pygame.time.get_ticks()
        if feedback_is_correct is not None:
            if now < feedback_until:
                show_feedback(screen, feedback_is_correct)
            else:
                feedback_is_correct = None
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.wait(cfg.ISI_MS)
                pygame.event.clear()

                correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
                cfg.correct_ind = correct_ind
                buffer1_img, buffer2_img = random.sample(
                    [stimuli[f"{phase}_BUFFER1"], stimuli[f"{phase}_BUFFER2"]],
                    2,
                )
                waiting = True
                trial_start = None

        if cfg.correct_count >= cfg.CORRECT_REQUIREMENT:
            if pygame.time.get_ticks() >= feedback_until:
                logger.info("Passed phase %s", phase)
                running = False
        elif cfg.trial_count >= cfg.FORCE_QUIT_LIMIT:
            if pygame.time.get_ticks() >= feedback_until:
                logger.info("Trial count: %s -> force quit limit reached", cfg.trial_count)
                running = False
                cfg.force_quit = True

        pygame.display.flip()
        if waiting and trial_start is None:
            trial_start = pygame.time.get_ticks()
        clock.tick(60)

    return screen


def run_overlapped_multiple_stimulus_phase_targeting_shape(
    screen: pygame.Surface,
    phase: str,
    stimuli: dict[str, Path],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run one phase with overlapped stimuli (target = shape) (P4-P7).
    """
    running = True
    waiting = True
    trial_start: int | None = None
    clock = pygame.time.Clock()
    feedback_until = 0
    feedback_is_correct = None

    buffer1_img, buffer2_img = random.sample(
        [stimuli[f"{phase}_BUFFER1"], stimuli[f"{phase}_BUFFER2"]],
        2,
    )

    correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
    cfg.correct_ind = correct_ind
    cfg.correct_count = 0
    cfg.trial_count = 0

    while running:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()

        if waiting:
            response, response_dir, input_source = _response_from_state(state)
            if response is not None and response in (correct_ind, incorrect_ind):
                correct_img = stimuli[f"{phase}_CORRECT"]
                incorrect_img = stimuli[f"{phase}_INCORRECT"]
                reaction_time = pygame.time.get_ticks() - trial_start if trial_start is not None else None
                feedback_is_correct = _handle_response(phase, response, response_dir, input_source, correct_img, incorrect_img, buffer1_img, buffer2_img, reaction_time=reaction_time)
                feedback_until = pygame.time.get_ticks() + cfg.FB_DURATION
                waiting = False

        show_ied_ui(screen)
        correct_img = stimuli[f"{phase}_CORRECT"]
        incorrect_img = stimuli[f"{phase}_INCORRECT"]
        place_overlapped_images(screen, correct_img, buffer1_img, correct_ind)
        place_overlapped_images(screen, incorrect_img, buffer2_img, incorrect_ind)

        now = pygame.time.get_ticks()
        if feedback_is_correct is not None:
            if now < feedback_until:
                show_feedback(screen, feedback_is_correct)
            else:
                feedback_is_correct = None
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.wait(cfg.ISI_MS)
                pygame.event.clear()

                correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
                cfg.correct_ind = correct_ind
                buffer1_img, buffer2_img = random.sample(
                    [stimuli[f"{phase}_BUFFER1"], stimuli[f"{phase}_BUFFER2"]],
                    2,
                )
                waiting = True
                trial_start = None

        if cfg.correct_count >= cfg.CORRECT_REQUIREMENT:
            if pygame.time.get_ticks() >= feedback_until:
                logger.info("Passed phase %s", phase)
                running = False
        elif cfg.trial_count >= cfg.FORCE_QUIT_LIMIT:
            if pygame.time.get_ticks() >= feedback_until:
                logger.info("Trial count: %s -> force quit limit reached", cfg.trial_count)
                running = False
                cfg.force_quit = True

        pygame.display.flip()
        if waiting and trial_start is None:
            trial_start = pygame.time.get_ticks()
        clock.tick(60)

    return screen


def run_overlapped_multiple_stimulus_phase_targeting_line(
    screen: pygame.Surface,
    phase: str,
    stimuli: dict[str, Path],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run one phase with overlapped stimuli (target = line) (P8/P9).
    """
    running = True
    waiting = True
    trial_start: int | None = None
    clock = pygame.time.Clock()
    feedback_until = 0
    feedback_is_correct = None

    buffer1_img, buffer2_img = random.sample(
        [stimuli[f"{phase}_BUFFER1"], stimuli[f"{phase}_BUFFER2"]],
        2,
    )

    correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
    cfg.correct_ind = correct_ind
    cfg.correct_count = 0
    cfg.trial_count = 0

    while running:
        state = event_handler.poll()

        if state.quit:
            pygame.quit()
            raise SystemExit

        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()

        if waiting:
            response, response_dir, input_source = _response_from_state(state)
            if response is not None and response in (correct_ind, incorrect_ind):
                correct_img = stimuli[f"{phase}_CORRECT"]
                incorrect_img = stimuli[f"{phase}_INCORRECT"]
                reaction_time = pygame.time.get_ticks() - trial_start if trial_start is not None else None
                feedback_is_correct = _handle_response(phase, response, response_dir, input_source, correct_img, incorrect_img, buffer1_img, buffer2_img, reaction_time=reaction_time)
                feedback_until = pygame.time.get_ticks() + cfg.FB_DURATION
                waiting = False

        show_ied_ui(screen)
        correct_img = stimuli[f"{phase}_CORRECT"]
        incorrect_img = stimuli[f"{phase}_INCORRECT"]
        place_overlapped_images(screen, buffer1_img, correct_img, correct_ind)
        place_overlapped_images(screen, buffer2_img, incorrect_img, incorrect_ind)

        now = pygame.time.get_ticks()
        if feedback_is_correct is not None:
            if now < feedback_until:
                show_feedback(screen, feedback_is_correct)
            else:
                feedback_is_correct = None
                screen.fill(cfg.BLACK_RGB)
                pygame.display.flip()
                pygame.time.wait(cfg.ISI_MS)
                pygame.event.clear()

                correct_ind, incorrect_ind = random.sample((1, 2, 3, 4), 2)
                cfg.correct_ind = correct_ind
                buffer1_img, buffer2_img = random.sample(
                    [stimuli[f"{phase}_BUFFER1"], stimuli[f"{phase}_BUFFER2"]],
                    2,
                )
                waiting = True
                trial_start = None

        if cfg.correct_count >= cfg.CORRECT_REQUIREMENT:
            if pygame.time.get_ticks() >= feedback_until:
                logger.info("Passed phase %s", phase)
                running = False
        elif cfg.trial_count >= cfg.FORCE_QUIT_LIMIT:
            if pygame.time.get_ticks() >= feedback_until:
                logger.info("Trial count: %s -> force quit limit reached", cfg.trial_count)
                running = False
                cfg.force_quit = True

        pygame.display.flip()
        if waiting and trial_start is None:
            trial_start = pygame.time.get_ticks()
        clock.tick(60)

    return screen
