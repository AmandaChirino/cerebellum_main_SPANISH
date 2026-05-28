"""
Single-task phase playback:
- phonetic_task_practice
- phonetic_task_experimental
- orthographic_task_practice
- orthographic_task_experimental
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


logger = get_logger("./src/core/singla_tasks")

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


def _expected_side_for_single(task_phase: str, stim_path: Path) -> str:
    stem = stim_path.stem  # e.g. A_upper_pink
    letter_token, case_token, _ = stem.split("_")
    letter = letter_token.lower()
    is_vowel = letter in VOWELS
    is_lower = case_token == "lower"

    mapping_base = _mapping_base()

    if task_phase.startswith("phonetic"):
        if mapping_base == 1:
            return "left" if is_vowel else "right"
        return "right" if is_vowel else "left"

    if mapping_base == 1:
        return "left" if is_lower else "right"
    return "right" if is_lower else "left"


def _phase_to_block(task_phase: str) -> str:
    if task_phase.startswith("phonetic"):
        return "phonetic"
    if task_phase.startswith("orthographic"):
        return "orthographic"
    raise ValueError(f"Unsupported single-task phase: {task_phase}")


def _parse_stim_meta(task_phase: str, stim_path: Path, prev_rule: str | None) -> dict:
    """Compute trial metadata from the stimulus filename and phase."""
    letter_token, case_token, color_token = stim_path.stem.split("_")
    letter = letter_token.lower()
    trial_class = "vocal" if letter in VOWELS else "consonant"
    # rule for stim_repetition: class for phonetic, case for orthographic
    current_rule = trial_class if task_phase.startswith("phonetic") else case_token
    stim_rep = "yes" if (prev_rule is not None and prev_rule == current_rule) else "no"
    return {
        "list_name": "random",
        "color": color_token,
        "trial_class": trial_class,
        "case": case_token,
        "congruency": "NA",
        "switching": "NA",
        "stim_repetition": stim_rep,
        "stimuli": letter_token,
        "_rule": current_rule,
    }


def run_single_task_phase(
    screen: pygame.Surface,
    task_phase: str,
    trial_series: list[Path],
    event_handler: EventHandler,
) -> pygame.Surface:
    """
    Run one single-task phase using generated trial paths.
    """
    mapping_img = paths.get_mapping_image_for_task_phase(task_phase)
    image_cache: dict[Path, pygame.Surface] = {}
    is_practice = task_phase.endswith("practice")
    trial_type = "practice" if is_practice else "experimental"
    block_name = cfg.BLOCK_LABEL_BY_MAPPING[cfg.MAPPING][task_phase]
    condition = "single"
    prev_rule: str | None = None

    for stim_path in trial_series:
        meta = _parse_stim_meta(task_phase, stim_path, prev_rule)
        prev_rule = meta["_rule"]
        cfg._start_time = datetime.datetime.now().isoformat()

        # 1) fixation cross
        _run_fixation_without_input(screen, image_cache)

        # 2) mapping + stimulus (up to MAX_RESPONSE_TIME, early stop on input)
        _draw_mapping_and_stimulus(screen, mapping_img, stim_path, image_cache)
        pygame.display.flip()

        response_side: str | None = None
        reaction_time = cfg.MAX_RESPONSE_TIME_SINGLE
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
            if elapsed >= cfg.MAX_RESPONSE_TIME_SINGLE:
                break

            pygame.time.delay(1)

        cfg._end_time = datetime.datetime.now().isoformat()

        expected_side = _expected_side_for_single(task_phase, stim_path)
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
            list_name=meta["list_name"],
            color=meta["color"],
            trial_class=meta["trial_class"],
            case=meta["case"],
            congruency=meta["congruency"],
            switching=meta["switching"],
            stim_repetition=meta["stim_repetition"],
            stimuli=meta["stimuli"],
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
