import csv
import os.path
import datetime

import pygame
import time
import utils.config as cfg
import utils.paths as path
from utils.config import *
from ui.pygame_render import *
from utils.event_handler import EventHandler
from ui.pygame_render import (
    toggle_full_screen,
    show_feedback,
)
from core.saves import update_save

def _flush_input() -> None:
    """
    Flush all pending pygame input events.

    :return: None
    """
    pygame.event.clear()
    pygame.time.delay(1)
    pygame.event.clear()

# Run synchronized sequence:
#   Warm-up tones play until the subject's first tap; then the next
#   max_key_press (=12) tones are counted and recorded. Tap detection is
#   decoupled from the tones: all genuine taps are captured continuously and
#   each counted tone is matched to a tap afterward (post-hoc pairing).
#   Non-counted tones are still saved, labeled "synchronized_warmup" (before the
#   first tap) or "synchronized_reference" (the tone the first tap synced to).
def run_synchronized(screen, start_tick, target_key, max_key_press,
                     stimulus_path, event_handler: EventHandler):
    pygame.event.clear()
    time.sleep(1)  # Delay before the first tone (let the subject prepare)

    stimulus = pygame.mixer.Sound(stimulus_path)
    tones_to_count = max_key_press          # = cfg.NUM_SYNCHRONIZED (12)
    half = SYNCHRONIZED_INTERVAL / 2.0      # half response window (+/-275 ms)

    sound_ticks = []          # counted tones only (ms since start_tick)
    warmup_ticks = []         # tones before the first tap (saved, response NA)
    reference_ticks = []      # non-counted tone(s) after the first tap (response NA)
    taps = []                 # all genuine taps (ms since start_tick); taps[0] = trigger
    first_tap_tick = None     # first tap = start of counting
    stop_after_tick = None    # raw-tick deadline to stop after the last tone

    # Track key-hold state via KEYDOWN/KEYUP edges; never re-seed from physical state.
    pygame.event.pump()
    space_held = bool(pygame.key.get_pressed()[pygame.K_SPACE])

    phase_start = pygame.time.get_ticks()
    next_tone_time = phase_start            # fixed grid -> no cumulative drift

    while True:
        now = pygame.time.get_ticks()

        # Play the next tone if it is due and counted tones are still needed
        if len(sound_ticks) < tones_to_count and now >= next_tone_time:
            t_rel = pygame.time.get_ticks() - start_tick   # timestamp the play command
            stimulus.play()
            next_tone_time += SYNCHRONIZED_INTERVAL         # advance to next grid slot

            if first_tap_tick is None:
                # Before the first tap -> warm-up tone (not counted)
                warmup_ticks.append(t_rel)
                print(f"\nWarm-up tone {len(warmup_ticks)} at {t_rel} ms (not counted)")
            elif t_rel < first_tap_tick + half:
                # After the first tap but within half a window -> reference tone,
                # i.e. the tone the first tap synced to (not counted)
                reference_ticks.append(t_rel)
                print(f"\nReference tone at {t_rel} ms (synced to first tap, not counted)")
            else:
                # Counted tone
                sound_ticks.append(t_rel)
                n = len(sound_ticks)
                print(f"\nTone {n}/{tones_to_count} (counted) at {t_rel} ms")
                if n == tones_to_count:
                    # listen one extra interval to capture the response to the 12th
                    stop_after_tick = pygame.time.get_ticks() + SYNCHRONIZED_INTERVAL

        # Drain events: capture every genuine tap (edge-triggered detection)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    screen = toggle_full_screen(screen)
                    _flush_input()
                    space_held = False
                elif event.key == pygame.K_SPACE:
                    if not space_held:  # genuine new press (not an OS key-repeat)
                        tap_tick = pygame.time.get_ticks() - start_tick
                        taps.append(tap_tick)
                        if first_tap_tick is None:
                            first_tap_tick = tap_tick
                            print(f"  -> FIRST TAP at {tap_tick} ms: counting {tones_to_count} tones")
                        else:
                            print(f"  -> tap at {tap_tick} ms")
                    space_held = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    space_held = False

        # Stop once the 12 tones played and the extra listen window passed
        if stop_after_tick is not None and pygame.time.get_ticks() >= stop_after_tick:
            break

        pygame.time.wait(1)

    pygame.time.delay(10)  # Prevent CPU overuse

    # Post-hoc pairing: each counted tone owns a +/-half window; tones are
    # SYNCHRONIZED_INTERVAL apart so the windows tile the axis with no overlap.
    # Match each tone to the nearest tap in its window (closest wins). The
    # trigger tap (taps[0]) is excluded -- it starts the count, not a response.
    key_responses = [[None, None] for _ in range(len(sound_ticks))]
    best_for_tone = {}  # tone_idx -> (distance, tap_tick)

    sync_taps = taps[1:] if first_tap_tick is not None else taps  # drop the trigger
    for tap in sync_taps:
        if not sound_ticks:
            break
        d, idx = min((abs(tap - st), i) for i, st in enumerate(sound_ticks))
        if d <= half:
            if idx not in best_for_tone or d < best_for_tone[idx][0]:
                best_for_tone[idx] = (d, tap)

    for idx, (d, tap) in best_for_tone.items():
        key_responses[idx] = [True, tap]

    # Prepend non-counted tones (response None) in chronological order, labeled so
    # they can be filtered out; the 12 counted tones keep the label "synchronized".
    all_sound_ticks   = warmup_ticks + reference_ticks + sound_ticks
    all_key_responses = ([[None, None]] * (len(warmup_ticks) + len(reference_ticks))
                         + key_responses)
    tone_kinds = (["synchronized_warmup"]    * len(warmup_ticks) +
                  ["synchronized_reference"] * len(reference_ticks) +
                  ["synchronized"]           * len(sound_ticks))
    return all_sound_ticks, all_key_responses, tone_kinds


# Run self-paced sequence
def run_self_paced(screen, start_tick, target_key, max_key_press, event_handler:EventHandler):
    last_tick = start_tick
    key_responses = []
    self_paced_start_tick = pygame.time.get_ticks()  # Record start of self-paced phase
    
    while len(key_responses) < max_key_press:
        # Abort the phase if it runs too long (participant cannot complete the taps)
        elapsed_time = pygame.time.get_ticks() - self_paced_start_tick
        if elapsed_time >= SELF_PACED_TIMEOUT:
            print(f"Self-paced phase timed out after {elapsed_time}ms (limit: {SELF_PACED_TIMEOUT}ms)")
            print(f"Completed {len(key_responses)}/{max_key_press} taps before timeout")
            break

        state = event_handler.poll()
        response_tick = pygame.time.get_ticks() - start_tick
            
        if state.quit:
            pygame.quit()
            raise SystemExit
        
        if state.toggle_full_screen:
            pygame.event.clear()
            screen = toggle_full_screen(screen)
            pygame.event.clear()
            _flush_input()

        if state.pressed and response_tick - last_tick > TREMOR_INTERVAL: # Tapped (space)
            last_tick = response_tick
            key_responses.append([state.pressed, response_tick])
            print(f"{state.pressed} pressed at {response_tick} ms ({len(key_responses)}/{max_key_press})")
        
    pygame.time.delay(10) # Prevent CPU overuse

    return key_responses

# Run trial (synchronized + self-paced)
def run_trial(screen, start_tick, target_key, max_synchronized_key_press, max_self_paced_key_press, stimulus_path, event_handler:EventHandler):
    synchronized_sound_ticks, synchronized_key_responses, synchronized_tone_kinds = run_synchronized(screen, start_tick, target_key, max_synchronized_key_press, stimulus_path,event_handler=event_handler,)
    self_paced_key_responses = run_self_paced(screen, start_tick, target_key, max_self_paced_key_press, event_handler=event_handler)
    return synchronized_sound_ticks, synchronized_key_responses, synchronized_tone_kinds, self_paced_key_responses

'''
=== Result Format ===
[block, trial, tap_num, type, pace_ms, synchronized_sound_ticks_ms, key_response, response_tick_ms, interval_ms, trial_type, key_correct, group]
- block: section name (practice / block)
- trial: the i-th trial (counting from the beginning)
- tap_num: the i-th tapping (counting from the beginning) = row index
- type: synchronized / self-paced
- pace_ms: = SYNCHRONIZED_INTERVAL (in milliseconds)
- synchronized_sound_ticks_ms:
    - [For (type == synchronized)] time tick when the stimulus beep-sound is played (counting from the global start time tick, in milliseconds)
    - [For (type == self_paced)] "v" / "m" = key_correct
- key_response:
    - [For (type == synchronized)] key pressed during given trial (could be None)
    - [For (type == self_paced)] "v"
- response_tick_ms:
    - [For (type == synchronized && synchronized_key_response is not None)] time tick when key is pressed (counting from the global start time tick, in milliseconds)
    - [For (type == synchronized && synchronized_key_response is None)] = synchronized_sound_ticks
    - [For (type == self_paced)] time tick when key is pressed (counting from the global start time tick, in milliseconds)
- interval_ms: time difference between two key presses (in milliseconds)
- trial_type: "Successful" (if all interval_ms of self-paced tappings in given trials is in [MIN_SELF_PACED_INTERVAL, MAX_SELF_PACED_INTERVAL]) / "Unsuccessful" (otherwise)
- key_correct: "v" / "m"
- group: i.e. YC / CD [first two text of participant_id]
'''

def single_trial(
        screen:pygame.Surface,
        block: str,
        start_tick: int,
        typeblock: str,
        target_key: pygame.key,
        trial,
        event_handler: EventHandler,
    ) -> pygame.Surface:
    screen.fill(BLACK_RGB)
    pygame.display.flip()
    start_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pace_ms = SYNCHRONIZED_INTERVAL # pace_ms
    key_correct = target_key

    # Run trial
    (synchronized_sound_ticks, 
     synchronized_key_responses, 
     synchronized_tone_kinds,
     self_paced_key_responses) = run_trial(screen,
                                           start_tick, 
                                           target_key,
                                           cfg.NUM_SYNCHRONIZED, 
                                           cfg.NUM_SELF_PACE, 
                                           paths.STIMULUS_PATH_1000,
                                           event_handler)
    
    # Write trial results
    assert len(synchronized_sound_ticks) == len(synchronized_key_responses)
    
    # type (warm-up/reference tones keep their labels; counted -> "synchronized")
    tap_types = (synchronized_tone_kinds +
                 ["self_paced"] * len(self_paced_key_responses))

    # synchrnoized_sound_tick_ms
    synchronized_sound_ticks += [None] * len(self_paced_key_responses)
    
    # key_response
    key_responses = ([response[0] for response in synchronized_key_responses] + 
                        [response[0] for response in self_paced_key_responses])
    
    # response_tick_ms
    response_ticks = ([response[1] for response in synchronized_key_responses] +
                      [response[1] for response in self_paced_key_responses])
    
    assert len(synchronized_sound_ticks) == len(response_ticks)
    assert len(key_responses) == len(response_ticks)

    # interval_ms
    intervals = [None]
    for i in range(1, len(response_ticks)):
        if response_ticks[i] is not None and response_ticks[i-1] is not None:
            # Check if this is the first self-paced tap (transition from synchronized to self-paced)
            # The first self-paced tap starts at index len(synchronized_key_responses)
            if i == len(synchronized_key_responses):
                # This is the transition from synchronized to self-paced - don't calculate interval
                intervals.append(None)
            else:
                intervals.append(response_ticks[i] - response_ticks[i-1])
        else:
            intervals.append(None)

    # Compute trial_outcome based on self-paced unguided IRIs (275-825 ms inclusive)
    # A trial is "valid" if every self-paced IRI (excluding the first transition) falls in [275, 825]
    self_paced_start_idx = len(synchronized_key_responses)
    self_paced_intervals = intervals[self_paced_start_idx:]
    # Skip the first self-paced interval (transition) and filter out None values
    unguided_iris = [iri for iri in self_paced_intervals[1:] if iri is not None]
    
    trial_outcome_value = "valid"
    trial_type = 1  # 1 = successful, 0 = unsuccessful
    for iri in unguided_iris:
        if iri < 275 or iri > 825:
            trial_outcome_value = "invalid"
            trial_type = 0
            break

    end_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # Compute tap_num per block: only count actual responses, restart numbering per block
    # We'll track a per-block counter externally, but for now we use a simple approach:
    # tap_num is sequential within each trial, starting from 1, but NA when response is None
    tap_counter = 0
    
    # Write one row per tap
    for i in range(len(response_ticks)):
        actual_key = key_responses[i] if key_responses[i] is not None else "FALSE"
        
        # Compute tap_num: only increment for actual responses
        if key_responses[i] is not None:
            tap_counter += 1
            tap_num_value = tap_counter
        else:
            tap_num_value = "NA"
        
        # Compute row-level trial_outcome: applies to entire trial, not individual taps
        # But we include it in every row for the trial
        update_save(
            block=block,
            type=typeblock,
            starttime=start_time,
            endtime=end_time,
            correct=trial_type,
            key_corr=pygame.key.name(target_key),
            key_resp=actual_key,
            pace_ms=pace_ms,
            synch_sound_ticks=synchronized_sound_ticks[i],
            response_ticks=response_ticks[i],
            intervals=intervals[i],
            trial=trial,
            tap_num=tap_num_value,
            tap_type=tap_types[i],
            trial_outcome=trial_outcome_value,
        )
    # Log result
    logger.info(
        "TRIAL_RESULT | block=%s | trial=%s | trial_type=%s | trial_outcome=%s | num_taps=%d",
        block,
        trial,
        trial_type,
        trial_outcome_value,
        len([r for r in key_responses if r is not None])
    )

    pygame.display.flip()
    pygame.time.delay(cfg.FB_DURATION)
    _flush_input()

    return screen, trial_type
