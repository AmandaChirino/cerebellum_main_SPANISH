

# Cerebellar battery (track changes for final version)

# GSS — (28 April 2026)

**PID format fix (`experiment_flow.py`):** Block sequence assignment now extracts trailing digits from the PID using `re.search(r'\d+$', ...)`, so both `aa01` and `aa_01` correctly map to sequence index 1. Previously only PIDs with a `_` or `-` separator worked.

**Block sequence counterbalancing fix:**
- Corrected PID-to-sequence assignment from `% 16` to `% 12` in `experiment_flow.py`.
- There are 12 predefined block sequences; the correct cycle length is 12. The previous `% 16` produced wrong sequence assignments for participants with PID suffix ≥ 17 (e.g., PID 17 would get sequence 1 instead of sequence 5), breaking the counterbalancing design.

**New CSV columns for DDM analysis (`saves.py`, `test.py`, `goal_practice.py`):**

Added 8 columns to support a Drift Diffusion Model (DDM/HSSM) analysis 

| Column | Values | Purpose |
|---|---|---|
| `goal` | `speed` / `accuracy` | Goal type for the current interval |
| `block_type` | `fixed` / `varying` | Whether the block has a single goal or alternates |
| `congruency` | `congruent` / `incongruent` | Whether word and ink color match |
| `interval_index` | integer (1-based) | Interval number within the block |
| `interval_duration_ms` | integer (ms) | Total window length for the current interval |
| `time_in_interval_ms` | float (ms) | Time from interval onset to stimulus onset — DDM threshold predictor |
| `joy_word_dir` | direction string | Joystick direction for the color *word* (prepotent/Stroop response) |
| `error_type` | `correct` / `stroop_error` / `random_error` / `NA` | Trial outcome classification |

`error_type` is computed automatically by the new `_classify_error()` helper in `saves.py`:
- `correct` — response matches ink color direction
- `stroop_error` — incorrect response that matches the *word* direction (prepotent error; keep for DDM)
- `random_error` — incorrect response that matches neither (exclude from DDM)
- `NA` — no response recorded

**DDM filtering recipe:**
```python
df_ddm = df[
    (df['trial_type'] == 'test') &
    (df['error_type'].isin(['correct', 'stroop_error']))
]
```

**Bug fix in `test.py`:** `varying_test_1` and `varying_test_2` previously used `pairs.index((goal, duration))` to get the interval index, which would return the wrong index when duplicate durations exist in the pairs list. Fixed by switching to `enumerate(pairs, 1)`.

**RT precision fix (`test.py`, `goal_practice.py`):** `stim_t0 = pygame.time.get_ticks()` was previously captured *after* `_flush_input()` (which includes a deliberate `delay(1)`). Moved it to immediately after `pygame.display.flip()` so RT and `time_in_interval_ms` are anchored to the actual moment the stimulus appeared on screen, not 1-2ms later. The explicit `cfg.joy_response = None` still follows the flush, so no stale responses can leak in. Change applied to all 12 stimulus-display sites across both files (initial stim, fullscreen-toggle redraw, and after-response next-stim).

**Fullscreen resolution fix (`ui/pygame_render.py`):** `init_display` and `toggle_full_screen` now call `pygame.display.Info()` to read the monitor's native resolution before entering fullscreen, updating `cfg.SCREEN_W/H` accordingly.

**Caption fix:** Window title corrected from `"CCS"` to `"GSS"`.

**Files changed:** `utils/saves.py`, `core/test.py`, `core/goal_practice.py`, `ui/pygame_render.py`.

# Template — (28 April 2026)

**Native-resolution fullscreen fix (`ui/pygame_render.py`):** `init_display` and `toggle_full_screen` now call `pygame.display.Info()` to read the monitor's native resolution before entering fullscreen, updating `cfg.SCREEN_W/H` accordingly. Previously they used the fixed config values, which could produce a wrong-sized window on monitors with a different resolution, causing inconsistent stimulus scaling across machines. All new tasks built from the template will inherit this behavior automatically.

**Standardized fixation cross added to template:**
- `Fixation_Cross.png` has been added to `template/resources/stimuli/` and wired into `test.py` and `practice.py`.
- The cross is displayed using `fit_mode="contain"` so it always renders at a small, centered size regardless of screen resolution — no more full-screen cross.
- All new tasks built from the template will inherit this behavior automatically. If you're updating an existing task, copy `Fixation_Cross.png` from `template/resources/stimuli/` into your task's `resources/` folder and replace the `screen.fill(BLACK)` fixation line with `place_image(screen, FIXATION_CROSS_IMAGE, fit_mode="contain")`.

# 2D — (23 April 2026)

**2D task — Mapping hint overlay fix:**
- Removed `_draw_response_hint()` from `2d/src/core/test.py` and its two call sites in the trial render loop and fullscreen toggle redraw.
- The function drew black text ("D / normal", "K / mirrored") at screen center that was overlapping and smearing the white arrows already embedded in the new `1.png` / `2.png` mapping images, causing a dark smudge.

**Trial structure (`stimuli_conditions.py`):**
- 10 practice trials followed by three experimental blocks of 48 trials each (144 total).
- Each block contains 24 Normal + 24 Mirrored trials, 12 per letter, 20 positive + 20 negative + 8 zero-degree rotation angles.
- **Block A:** canonical random assignment — for each (letter, magnitude) pair, one sign (+ or −) is assigned randomly; both Normal and Mirrored conditions receive that same sign. 8 zero-degree trials (4 letters × 2 conditions).
- **Block B:** mirror of Block A — each (letter, magnitude, condition) gets the opposite sign from Block A. Its 80 non-zero trials are fully disjoint from Block A's 80. Zero-degree trials repeat (by design).
- **Block C:** condition-flip of Block A's rotated trials — same letter and signed angle as Block A, but Normal ↔ Mirrored swapped. Adds a 3rd repetition of the 8 zero-degree cells (new objects, not references to A/B). Block C's 40 rotated `(letter, angle, condition)` tuples are disjoint from Block B's; they are the complement of Block A's (same angles, opposite conditions).
- Constrained shuffle applied independently to each block: max run of 2 identical conditions and max run of 3 identical letters; first and last trial must not be 0°.
- Blocks are generated once per session and cached; PID parity determines the response-key version (even → Normal=k, odd → Normal=d).

**New CSV output columns (`saves.py`, `test.py`):**
- Added `letter`, `rotation_angle` (signed, e.g. −45), `rotation` (absolute value), and `stimuli_path` columns, inserted before `condition`.
- Renamed language value `'Espanol'` → `'Spanish'`.


# GSS — (27 March 2026)

-Stroop trials are generated with an equal probability (50/50) of being congruent or incongruent.
-Neither the color word nor the ink color can be repeated in two consecutive trials.

# How to ensure the results/ folder always exists in new tasks

# CCC — Full overhaul (9–10 March 2026)

# How to ensure the results/ folder always exists in new tasks

To avoid errors when saving CSV files if the `results/` folder doesn't exist, add the following line at the beginning of the `create_save()` function in the `saves.py` file of each task:
```python
RESULTS_DIR.mkdir(exist_ok=True)
```

This automatically creates the folder if it doesn't exist before saving the file, without affecting normal functionality or the naming/versioning logic of the results.

Place this command **before** any attempt to save the CSV file.

**Presentation time:**
- Single-task trials: 4000 ms
- Multi-task trials: 5000 ms

**Too Late! feedback:** Practice blocks now show "Too Late!" (instead of "Timeout!") when no response is given within the time window.

**New CSV columns (8 added after `condition`):** `list`, `color`, `class`, `case`, `congruency`, `switching`, `stim_repetition`, `stimuli`. For single-task trials these are computed from the stimulus filename at runtime; for multi-task trials they come directly from the pre-defined trial lists (sourced from the Excel spreadsheets).

**`condition` and `block` columns:** `condition` now stores `"single"` or `"multi"`. `block` stores positional labels (p1/b1/p2/b2/p3/b3/b4) that reflect the participant's actual task order as determined by their mapping.

**Mapping system expanded from 4 to 8 (2×2×2 counterbalancing):**

The mapping is derived automatically from the last digit of the participant ID (`digit % 8`, with 0 → 8).

| Mapping | Single-task order | Key side (left=…) | Multi-task block order |
|---------|-------------------|-------------------|------------------------|
| 1 | Phonetic → Orthographic | vowel / lower | List 1 → List 2 |
| 2 | Phonetic → Orthographic | consonant / upper | List 1 → List 2 |
| 3 | Orthographic → Phonetic | vowel / lower | List 1 → List 2 |
| 4 | Orthographic → Phonetic | consonant / upper | List 1 → List 2 |
| 5 | Phonetic → Orthographic | vowel / lower | List 2 → List 1 |
| 6 | Phonetic → Orthographic | consonant / upper | List 2 → List 1 |
| 7 | Orthographic → Phonetic | vowel / lower | List 2 → List 1 |
| 8 | Orthographic → Phonetic | consonant / upper | List 2 → List 1 |

Mappings 5–8 reuse the same instruction image folders as 1–4 (the multi-task instructions never reference block 1 or 2 by name). The block order swap happens at the trial-series level in `experiment_flow.py`. The `block` column in the CSV always records the presentation position (b3 = first multi-task experimental block shown, b4 = second), while the `list` column records which stimulus list (list1/list2) was actually used.

**Files changed:** `config.py`, `paths.py`, `pygame_render.py`, `single_tasks.py`, `multi_tasks.py`, `experiment_flow.py`, `saves.py`, `construct_trials.py`.

# ADMINISTRATOR SCREENS - language, group and session  (8 March, 2026)

Applied to all 6 tasks: **bmr, ccc, ccs, ied, nBack, sd**.

After the participant enters their ID in Admin_1, three new sequential screens are shown before proceeding to the hand preference question:
1. **Language** — Admin_Lan.png, press 1 (Spanish) or 2 (English), confirmation screen + ENTER
2. **Group** — Admin_Grp.png, press 1–6 (pilot/control/cd/stroke/tumor/other), confirmation screen + ENTER
3. **Session** — Admin_Session.png, press 1–9 (s1–s9), confirmation screen, ENTER

Files modified per task:
- `src/utils/paths.py` — added 20 new admin image path constants (`ADMIN_LAN`, `ADMIN_LAN_SPANISH`, `ADMIN_LAN_ENGLISH`, `ADMIN_GRP`, `ADMIN_GRP_1–6`, `ADMIN_SESSION`, `ADMIN_SESSION_1–9`)
- `src/utils/config.py` — added 3 runtime state variables: `LANGUAGE`, `GROUP`, `SESSION`
- `src/utils/saves.py` (or `src/core/saves.py` for SD) — added `"language"`, `"group"`, `"session"` columns to `COLUMNS` list and to the record dict, inserted after `"participant_id"`
- `src/ui/pygame_render.py` (or `pygame_renderer.py` for IED) — added `_await_one_of_keys()` helper and `record_language_group_session()` function; wired the call inside `get_participant_id()` after `cfg.PID` is set


# GENERAL CHANGES, PLEASE IMPLEMENT IN ALL TASKS (6 March, 2026)

**A. Reaction Time Measurement Correction:**
- **Problem:** The RT timer was started BEFORE the stimulus became visible on screen. In the original code, `phase_start_tick` was captured before the first `_draw_base()` and `pygame.display.flip()` cycle, causing a systematic error in all RT measurements.

- **Original timing sequence:**
  ```
  phase_start_tick = get_ticks()  (Timer starts here)
  Loop begins:
    poll() events                  
    _draw_base()                   
    pygame.display.flip()          (~8-16ms delay with vsync)
    Stimulus visible for first time (8-16ms after timer started)
  ```
  All RTs were inflated (sum of first poll + draw + flip cycle)

- **Corrected timing sequence:**
  ```
  _draw_base("stimulus")           (Display stimulus)
  pygame.display.flip()            (Vsync waits, stimulus visible)
  phase_start_tick = get_ticks()   (Timer starts here)
  phase_end_tick = start + duration
  Loop begins:
    poll() events                  (Response detection starts immediately)
    now_tick = get_ticks()
    RT = now_tick - phase_start_tick  (Accurate RT from stimulus visibility)
  ```
  - **Remeber to keep Vsync=1** It Synchronizes `pygame.display.flip()` with the monitor's refresh cycle (60Hz = 16.67ms intervals). This ensures the flip() command WAITS until the next screen refresh before returning, preventing "tearing" artifacts and guaranteeing the stimulus is displayed at a known time boundary.

- **Code change:**
  ```python
  # BEFORE (incorrect):
  phase_start_tick = pygame.time.get_ticks()
  while pygame.time.get_ticks() < phase_end_tick:
      poll()
      _draw_base()
      flip()  # Stimulus visible here, but timer started earlier
  
  # AFTER (correct):
  _draw_base("stimulus")
  pygame.display.flip()  # Vsync waits here, stimulus visible
  phase_start_tick = pygame.time.get_ticks()  # Timer starts AFTER visibility
  while pygame.time.get_ticks() < phase_end_tick:
      poll()
      
  ```

**B. Trial-by-Trial Input Source Detection and Column Segregation:**
- **Problem:** Previously, all responses were recorded in joystick columns (`joy_correct`, `joy_response`, `stimulus_joy_response`, `isi_joy_response`) regardless of whether keyboard or joystick was used. Keyboard columns (`key_correct`, `key_response`, `stimulus_key_response`, `isi_key_response`) remained empty even when keyboard was used.

The solution was to implemented trial-by-trial input source detection that automatically populates the appropriate columns based on the actual input device used:
  - *Keyboard trials:* Records in `key_*` columns with values "d" or "k"
  - *Joystick trials:* Records in `joy_*` columns with values "left" or "right"
-
- **Code change:**

```python
# motor.py - _register_first_response() function
def _register_first_response(phase_name, now_tick, phase_start_tick, joy_resp):
    # RT firts
    phase_rt = now_tick - phase_start_tick
    trial_input_source = cfg._input_source  # Captured simultaneously with RT
    
    if phase_name == "stimulus":
        # Column assignment happens AFTER RT capture
        if trial_input_source == "key":
            stimulus_key_response = "d" if joy_resp == "left" else "k"
        else:  # joystick
            stimulus_joy_response = joy_resp
        
        # RT assignment uses already-captured value (no added latency)
        stimulus_reaction_time = phase_rt
        reaction_time = phase_rt
```

```python
# motor.py - partResult dictionary construction
# Correct answer columns also populate based on trial input source
if trial_input_source == "key":
    key_correct_out = "d" if key_correct == pygame.K_d else "k"
    joy_correct_out = None
else:
    key_correct_out = None
    joy_correct_out = "left" if key_correct == pygame.K_d else "right"

partResult = {
    "key_correct": key_correct_out,
    "joy_correct": joy_correct_out,
    "stimulus_key_response": stimulus_key_response,  # Populated only if keyboard used
    "isi_key_response": isi_key_response,
    "stimulus_joy_response": stimulus_joy_response,  # Populated only if joystick used
    "isi_joy_response": isi_joy_response,
    "input_source": trial_input_source,  # "key" or "joy"
    # ... other fields ...
}
```

**C. Joystick Intermittent Failure Fix (macOS IOHIDManager HID lifecycle bug ONLY IN CCS):**

On macOS, SDL2 uses the IOHIDManager API to receive joystick axis events. When `pygame.quit()` is called at the end of a participant run, macOS begins tearing down the IOHIDManager HID device handle. If the next `pygame.init()` (next participant) opens the joystick before macOS completes the HID device lifecycle cleanup, SDL records the device as "open" (`get_count() == 1`, name readable) but the IOHIDManager IOHID callback is never re-registered. The result: `get_axis()` always returns 0, `JOYAXISMOTION` events are never generated. The device appeared fully functional in all logging but was silently producing no input data.

The symptom was timing-dependent: after a keyboard-only participant (joystick idle, axes at 0.0 the entire session), the SDL internal axis cache held stale 0.0 values, making the ghost-open device completely invisible. After a joystick participant (axes last seen at non-zero), the stale cache at least showed residual movement, which is why the bug was harder to trigger in some orderings.

- **Code change:**

Changes in `experiment_flow.py`:
```python
import time  # added

def run() -> None:
    pygame.init()

    # Force a full joystick subsystem cycle so macOS has time to complete the
    # IOHIDManager HID device lifecycle from the previous process/run.
    pygame.joystick.quit()     # explicitly tear down IOHIDManager handle
    time.sleep(0.3)            # wait 300ms for macOS HID cleanup to finish
    pygame.joystick.init()     # fresh re-enumeration via IOHIDManager

    # Wait for JOYDEVICEADDED — SDL's confirmation that IOHIDManager callbacks
    # are fully active and the device will deliver JOYAXISMOTION events.
    reset_joystick_cache()
    _joy_deadline = pygame.time.get_ticks() + 2000
    _joy_count = 0
    while pygame.time.get_ticks() < _joy_deadline:
        for _ev in pygame.event.get():
            if _ev.type == pygame.JOYDEVICEADDED:
                _joy_count += 1
        if _joy_count > 0:
            break
        pygame.time.delay(20)
    if _joy_count == 0:
        _joy_count = pygame.joystick.get_count()
```

**D. Joystick Movement Restrictions (Horizontal-Only Validation):**
- Implemented two-layer filtering system to prevent accidental up/down movements when hand is resting on joystick:

```python
# event_handler.py - _process_joystick() method
def _process_joystick(self) -> None:
    x = self._joystick.get_axis(0)
    y = self._joystick.get_axis(1)
    
    # Layer 1: Standard deadzone (prevents micro-movements)
    if abs(x) < cfg.DZ_X and abs(y) < cfg.DZ_Y:  # DZ_X = DZ_Y = 0.60
        return
    
    # Layer 2: Directional strength filter (prevents accidental verticals)
    if abs(x) < abs(y) * 0.7:  # Horizontal must be ≥70% of vertical strength
        return
    
    # Process only strong horizontal movements
    angle = (math.degrees(math.atan2(x, -y)) + 360) % 360
    if 180 <= angle < 360:
        self._state.option_1 = True  # Left
        cfg.joy_response = "left"
    elif 0 <= angle < 180:
        self._state.option_2 = True  # Right
        cfg.joy_response = "right"
```


# CCS (5 March, 2026)

**Directory Creation Fix:**
- Added automatic `results/` directory creation if it doesn't exist to prevent "No such file or directory" errors when saving CSV files. `RESULTS_DIR.mkdir(exist_ok=True)` added to `create_save()` function in each task's `saves.py`.
- Applied to CCS, IED, nBack, and SD tasks for consistency.

**Condition Variable Format:**
- Removed "-actual" suffix from condition variable for regular trials (e.g., "motor" instead of "motor-actual").
- Catch trials still use "-catch" suffix (e.g., "motor-catch") for proper identification.
- Modified in `saves.py`: `condition = f"{condition_task}{'-catch' if is_catch else ''}"`

**Practice Structure Simplification (Motor & Sensorimotor):**

All practice phases have been simplified to single continuous sessions:

**Motor Practice 1 (Blue Circles):**
- **Changed:** Single continuous 12-trial session (10 regular blue trials + 2 catch/no-go trials).
- **Removed:** Accuracy threshold checking and repeat loops - practice runs once regardless of performance.
- **Removed:** Intermediate instruction screens (6.png and 7.png).

**Motor Practice 2 (Red Circles):**
- **Changed:** Single continuous 12-trial session (10 regular red trials + 2 catch/no-go trials).
- **Removed:** Accuracy threshold checking and repeat loops - practice runs once regardless of performance.
- **Removed:** Intermediate instruction screens (16.png and 17.png).

**Sensorimotor Practice (Mixed Colors):**
- **Changed:** Single continuous 24-trial session (10 red trials + 10 blue trials + 4 catch/no-go trials).
- **Removed:** Accuracy threshold checking and repeat loops - practice runs once regardless of performance.
- **Removed:** Intermediate instruction screens (6.png and 7.png).


# SD (24 Feb, 2026)

**General changes:**
- Added a 'list' column (A/B) to results for stimulus set tracking.
- Timeout trials now record correct=0 and show expected joystick direction or key, with NA for responses.
- Fixed mapping logic: Mapping 1 (d/left=meaningful, k/right=meaningless), Mapping 2 (d/left=meaningless, k/right=meaningful).
- Results columns for key/joystick responses and correct answers now always match the mapping version.
- The code automatically fills key_* or joy_* columns depending on the input device used.
- The order of sentences in each block is sampled randomly from the CSV, not fully shuffled (the result is the same since I have 45 sentences available per block).
- SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

- **Font Path Fix:** 

Resolved cross-platform font loading issues by migrating FONT definition from config.py to paths.py using pathlib.Path. Ensure proper path resolution on Windows and macOS

**Font Path Resolution:**
```python
# Before (config.py):
FONT = "resources\\OpenSans.ttf"  # Windows-only backslashes

# After (paths.py):
FONT = RESOURCES_DIR / "OpenSans.ttf"  # pathlib.Path auto-resolves separators
```

- **SD Mapping Background Implementation:** 

Added SD mapping images as backgrounds for target words. SD_Mapping_1.png or SD_Mapping_2.png are displayed based on the mapping version (cfg.MAPPING) during target word presentation. I also updated the position of the mapping in the Figma templates. 

- **Joystick Movement Restrictions:** 

Implemented horizontal-only input validation to prevent accidental up/down movements when hand is resting on joystick. I applied 2 filters: deadzone validation (abs(x) < 0.60 && abs(y) < 0.60) and directional strength requirements (horizontal movement must be ≥70% stronger than vertical component) to prevent tahta very inaccurate diagonal movements are recognized as answers. 

```python
def _process_joystick(self) -> None:
    x = self._joystick.get_axis(0)
    y = self._joystick.get_axis(1)
    
    # Layer 1: Standard deadzone (prevents micro-movements)
    if abs(x) < cfg.dz_x and abs(y) < cfg.dz_y:
        return
    
    # Layer 2: Directional strength filter (prevents accidental verticals)
    if abs(x) < abs(y) * 0.7:  # Horizontal must be ≥70% of vertical strength
        return
    
    # Process only strong horizontal movements
    angle = (math.degrees(math.atan2(x, -y)) + 360) % 360
    if 180 <= angle < 360:
        self._state.option_1 = True  # Left
    elif 0 <= angle < 180:
        self._state.option_2 = True  # Right
```

# IED (Feb 18, 2026)

- **Stimulus Assignment Fix:** 

Corrected stimulus consistency across phases P3 (CDS), P4 (CDO), and P5 (CDR) to maintain proper rule sequence. P3-P4 now use the same correct stimulus, while P5 reverses back to P1's stimulus.

- **Phase Naming Update:**

Updated internal phase names to standard abbreviations: P3=CDS (Compound Discrimination Separated), P4=CDO (Compound Discrimination Overlapped), P5=CDR (Compound Discrimination Reversal), P6=IDS (Intra-Dimensional Shift), P7=IDR (Intra-Dimensional Reversal), P8=EDS (Extra-Dimensional Shift), P9=EDR (Extra-Dimensional Reversal).

- **Force Quit Improvement:**

Modified the 50-trial force quit mechanism to transition to the thank you screen instead of abruptly terminating the experiment.

- **Response Validation:**

Implemented validation to ignore responses to empty quadrants. Only responses to actual stimulus positions (correct or incorrect) are now recorded as valid trials.

- **Stimulus Feature Decomposition:**

Added 8 new columns to CSV output for attention modeling (Talwar et al., 2024 approach): `correct_shape`, `correct_line`, `incorrect_shape`, `incorrect_line`, `chosen_shape`, `chosen_line`, `unchosen_shape`, `unchosen_line`. This enables computational analysis of attention allocation during dimensional shifts.


## 1. General Changes - Implemented for all tasks (February 3, 2026)

- **Hand Preference Question:** 

Replaced the question regarding the less affected hand with "Which hand will the participant use to respond?". The answer to this question must be saved in the used_hand column of the output CSV.

- **Filename Formatting:** 

The output CSV filename now includes the date in YYYY_MM_DD format.

Example: For participant ctrl01, the generated results file will be: ctrl01_nBack_results_2026_02_03.csv.

- **Overwrite Protection (Versioning):**

 If the same participant ID is used more than once on the same date, the output CSV is not overwritten. Instead, a version suffix (_v2, _v3, etc.) is appended after the ID for subsequent runs.

-First run: ctrl01_nBack_results_2026_02_03.csv

--Second run: ctrl01_v2_nBack_results_2026_02_03.csv

Third run: ctrl01_v3_nBack_results_2026_02_03.csv

- **Task Column:**

 Added a new column named task at the beginning of the output CSV, containing the name of the specific task being executed.

- **End Screen:** 

The final screen ("Thank you for your participation") will now close the experiment upon pressing the spacebar or after 10 seconds have elapsed, whichever occurs first.

- **Vsync. Warning on RT accuracy:**

Due to the 60Hz monitor refresh rate, there is a potential ~16ms lag between the software command and the actual stimulus display. To correct this, I have enabled V-Sync (vsync=1). This ensures pygame.display.flip() waits for the screen refresh before starting the timer (trial_start), synchronizing the code with the visual output. Without V-Sync, our timing would start prematurely.

I did this in the init_display function. Let’s keep it this way for all tasks, please.

- **Task Duration Tracking:**

Added automatic calculation and logging of total task completion time. The system now displays the total duration in minutes and seconds in the console when the task ends. 

**Location in code:**
- File: `nBack/src/core/experiment_flow.py`
- Function: `run()` (at the end, just before `pygame.quit()`)
- Lines: Added after line 290

**How it works:**
1. At the start of the experiment (line 137), the system records the start time: `cfg.START_TIME = datetime.datetime.now().isoformat()`
2. At the end of the task, the code calculates elapsed time:
   - Converts `cfg.START_TIME` back to a datetime object
   - Subtracts it from the current end time
   - Converts the result to minutes (total_seconds / 60)
3. Logs two messages to the console:
   - `Task completed successfully!`
   - `Total task duration: X.XX minutes (Y seconds)`

**Code implementation:**
```python
# Calculate and display total task duration
end_time = datetime.datetime.now()
start_time_obj = datetime.datetime.fromisoformat(cfg.START_TIME)
total_duration = end_time - start_time_obj
total_minutes = total_duration.total_seconds() / 60

logger.info(f"Task completed successfully!")
logger.info(f"Total task duration: {total_minutes:.2f} minutes ({int(total_duration.total_seconds())} seconds)")
```

**To reproduce this in other tasks:**
1. Ensure `datetime` is imported at the top of the file: `import datetime`
2. The task must already record `cfg.START_TIME` at startup
3. Add the above code block at the very end of the `run()` function, just before `pygame.quit()`

Example console output: `Total task duration: 23.45 minutes (1407 seconds)`

## 2. N-Back Updates (February 3, 2026)

- **Fixation Cross:** 

Added a fixation cross during the Inter-Stimulus Interval (ISI).

- **Fixed Timing (Jaeggi et al., 2010):** 

The stimulus (500 ms) and the fixation cross (2500 ms) now remain on screen for their full duration, even if a response is registered. Pressing the spacebar does not interrupt the display of these elements.

- **Smart Feedback Timing:**

Immediate feedback: Triggered when the participant responds (any time within the 3000ms window).

Delayed feedback: Displayed when there is no response to targets (appears in the last 500ms of the 3000ms window).

Maximized response opportunity: Full 3000ms uninterrupted response time allowed for missed targets.

Standard feedback duration: Set to 500ms for optimal visibility.

**Joystick Input Handling:**
- Updated joystick input handling in CCS to align with SD task behavior.
- All responses, whether from the keyboard or joystick, are now recorded as joystick responses.
- Refactored `motor.py` trial loop to use a single `EventHandler` per trial and ensure consistent input handling.

**Key Code Changes for Joystick Handling:**

- **motor.py**:
```python
# Refactored trial loop to use a single EventHandler per trial
# Ensures consistent input handling for both keyboard and joystick

def run_trials(trials):
    for trial in trials:
        event_handler = EventHandler()
        while not trial.is_complete:
            event_handler.process_events()
            trial.update(event_handler)
```

- **sensorimotor.py**:
```python
# Directly uses the updated run_trials function from motor.py
from motor import run_trials

def execute_sensorimotor_trials():
    trials = generate_trials()
    run_trials(trials)
```

- **event_handler.py**:
```python
# Unified handling of keyboard and joystick inputs
# All responses are recorded as joystick responses

def process_events(self):
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            self.joystick_response = map_key_to_joystick(event.key)
        elif event.type == pygame.JOYBUTTONDOWN:
            self.joystick_response = event.button
```

These changes ensure that all responses, regardless of input device, are treated as joystick responses and recorded consistently.
