"""
Multi-task phase playback:
- multi_task_practice
- multi_task_experimental_block_1
- multi_task_experimental_block_2
"""


from __future__ import annotations
from pathlib import Path
import datetime

import pygame

import utils.config as cfg
from utils import paths
from utils.logger import get_logger
from utils.event_handler import EventHandler
from utils.saves import update_save
from ui.pygame_render import toggle_full_screen, show_feedback
from core.construct_trials import TrialSpec


logger = get_logger("./src/core/multi_tasks")

VOWELS = {"a", "e", "i", "u"}


def _flush_input() -> None:
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()


def _run_fixation_without_input(
    screen: pygame.Surface,
    image_cache: dict[Path, pygame.Surface],
) -> None:
    blocked_types = [
        pygame.KEYDOWN,
        pygame.KEYUP,
        pygame.JOYAXISMOTION,
        pygame.JOYBALLMOTION,
        pygame.JOYHATMOTION,
        pygame.JOYBUTTONDOWN,
        pygame.JOYBUTTONUP,
    ]

    _flush_input()
    for ev_type in blocked_types:
        pygame.event.set_blocked(ev_type)

    try:
        _draw_fixation(screen, image_cache)
        pygame.display.flip()
        pygame.time.delay(cfg.FIXATION_CROSS_TIME)
    finally:
        for ev_type in blocked_types:
            pygame.event.set_allowed(ev_type)
        _flush_input()


def _load_image(path: Path, cache: dict[Path, pygame.Surface]) -> pygame.Surface:
    if path not in cache:
        cache[path] = pygame.image.load(str(path)).convert_alpha()
    return cache[path]


def _draw_fixation(
    screen: pygame.Surface,
    image_cache: dict[Path, pygame.Surface],
) -> None:
    screen.fill(cfg.BLACK_RGB)
    fix_img = _load_image(paths.FIXATION_CROSS, image_cache)
    screen_w, screen_h = screen.get_size()
    img_w, img_h = fix_img.get_size()
    scale = min(screen_w / img_w, screen_h / img_h)
    fix_scaled = pygame.transform.smoothscale(fix_img, (int(img_w * scale), int(img_h * scale)))
    rect = fix_scaled.get_rect(center=screen.get_rect().center)
    screen.blit(fix_scaled, rect.topleft)


def _draw_mapping_and_stimulus(
    screen: pygame.Surface,
    mapping_img_path: Path,
    stim_path: Path,
    image_cache: dict[Path, pygame.Surface],
) -> None:
    screen.fill(cfg.BLACK_RGB)

    mapping_img = _load_image(mapping_img_path, image_cache)
    stim_img = _load_image(stim_path, image_cache)

    screen_w, screen_h = screen.get_size()
    map_w, map_h = mapping_img.get_size()

    # Scale mapping to fit within screen (contain)
    scale = min(screen_w / map_w, screen_h / map_h)
    target_w = max(1, int(round(map_w * scale)))
    target_h = max(1, int(round(map_h * scale)))
    mapping_scaled = pygame.transform.smoothscale(mapping_img, (target_w, target_h))
    mapping_rect = mapping_scaled.get_rect(center=screen.get_rect().center)
    screen.blit(mapping_scaled, mapping_rect.topleft)

    stim_w, stim_h = stim_img.get_size()
    stim_scaled = pygame.transform.smoothscale(
        stim_img,
        (max(1, int(stim_w * cfg.STIM_SCALE)), max(1, int(stim_h * cfg.STIM_SCALE))),
    )
    stim_rect = stim_scaled.get_rect(center=screen.get_rect().center)
    screen.blit(stim_scaled, stim_rect.topleft)


def _mapping_base() -> int:
    # Mapping table:
    # - 1/3/5/7: left = vowel / lower
    # - 2/4/6/8: left = consonant / upper
    return 1 if cfg.mapping_left_is_vowel_lower(cfg.MAPPING) else 2


def _expected_side_for_multi(trial: TrialSpec) -> str:
    letter = trial["stimuli"].lower()
    is_vowel = letter in VOWELS
    is_lower = trial["case_type"] == "lower"

    if trial["color"] == "pink":
        category_left = is_vowel
    else:
        category_left = is_lower

    mapping_base = _mapping_base()
    if mapping_base == 1:
        return "left" if category_left else "right"
    return "right" if category_left else "left"


def _phase_to_block(task_phase: str) -> str:
    if task_phase.startswith("multi_task"):
        return "multi_task"
    raise ValueError(f"Unsupported multi-task phase: {task_phase}")


def run_multi_task_phase(
    screen: pygame.Surface,
    task_phase: str,
    trial_series: list[TrialSpec],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run one mixed-task phase from fixed trial specs.
    """
    mapping_img = paths.get_mapping_image_for_task_phase(task_phase)
    image_cache: dict[Path, pygame.Surface] = {}
    is_practice = task_phase.endswith("practice")
    trial_type = "practice" if is_practice else "experimental"
    block_name = cfg.BLOCK_LABEL_BY_MAPPING[cfg.MAPPING][task_phase]
    condition = "multi"

    for trial in trial_series:
        stim_path = trial["stim_path"]
        cfg._start_time = datetime.datetime.now().isoformat()

        # 1) fixation cross
        _run_fixation_without_input(screen, image_cache)

        # 2) mapping + stimulus (up to MAX_RESPONSE_TIME, early stop on input)
        _draw_mapping_and_stimulus(screen, mapping_img, stim_path, image_cache)
        pygame.display.flip()

        response_side: str | None = None
        reaction_time = cfg.MAX_RESPONSE_TIME_MULTI
        start_ms = pygame.time.get_ticks()

        while True:
            state = event_handler.poll()

            if state.quit:
                pygame.quit()
                raise SystemExit

            if state.toggle_full_screen:
                pygame.event.clear()
                screen = toggle_full_screen(screen)
                pygame.event.clear()
                _draw_mapping_and_stimulus(screen, mapping_img, stim_path, image_cache)
                pygame.display.flip()

            elapsed = pygame.time.get_ticks() - start_ms

            if state.option_1:
                response_side = "left"
                reaction_time = elapsed
                break
            if state.option_2:
                response_side = "right"
                reaction_time = elapsed
                break
            if elapsed >= cfg.MAX_RESPONSE_TIME_MULTI:
                break

            pygame.time.delay(1)

        cfg._end_time = datetime.datetime.now().isoformat()

        expected_side = _expected_side_for_multi(trial)
        key_correct = "d" if expected_side == "left" else "k"
        joy_correct = expected_side
        key_response = "d" if response_side == "left" else ("k" if response_side == "right" else "")
        joy_response = response_side or ""
        correct = None if response_side is None else int(response_side == expected_side)

        # 3) practice feedback: keep mapping + letter on screen, FB_DURATION always
        if is_practice and response_side is not None:
            feedback_status = "correct" if response_side == expected_side else "incorrect"

            _draw_mapping_and_stimulus(screen, mapping_img, stim_path, image_cache)
            show_feedback(screen, feedback_status)
            pygame.display.flip()

            fb_start = pygame.time.get_ticks()
            while pygame.time.get_ticks() - fb_start < cfg.FB_DURATION:
                state = event_handler.poll()
                if state.quit:
                    pygame.quit()
                    raise SystemExit
                if state.toggle_full_screen:
                    pygame.event.clear()
                    screen = toggle_full_screen(screen)
                    pygame.event.clear()
                    _draw_mapping_and_stimulus(screen, mapping_img, stim_path, image_cache)
                    show_feedback(screen, feedback_status)
                    pygame.display.flip()
                pygame.time.delay(1)

        elif is_practice and response_side is None:
            _draw_mapping_and_stimulus(screen, mapping_img, stim_path, image_cache)
            show_feedback(screen, "timeout")
            pygame.display.flip()

            fb_start = pygame.time.get_ticks()
            while pygame.time.get_ticks() - fb_start < cfg.FB_DURATION:
                state = event_handler.poll()
                if state.quit:
                    pygame.quit()
                    raise SystemExit
                if state.toggle_full_screen:
                    pygame.event.clear()
                    screen = toggle_full_screen(screen)
                    pygame.event.clear()
                    _draw_mapping_and_stimulus(screen, mapping_img, stim_path, image_cache)
                    show_feedback(screen, "timeout")
                    pygame.display.flip()
                pygame.time.delay(1)

        update_save(
            block_name=block_name,
            trial_type=trial_type,
            condition=condition,
            list_name=trial["list_name"],
            color=trial["color"],
            trial_class=trial["trial_class"],
            case=trial["case_type"],
            congruency=trial["congruency"],
            switching=trial["switching"],
            stim_repetition=trial["stim_repetition"],
            stimuli=trial["stimuli"],
            key_correct=key_correct,
            key_response=key_response,
            joy_correct=joy_correct,
            joy_response=joy_response,
            correct=correct,
            reaction_time=reaction_time,
            stimulus_path=stim_path.name,
        )

        logger.info(
            "TASK_TRIAL | phase=%s | stimulus=%s | response=%s | rt_ms=%d",
            task_phase,
            stim_path.name,
            response_side if response_side is not None else "None",
            reaction_time,
        )

    return screen
