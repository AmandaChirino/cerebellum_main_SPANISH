import pygame

from core.feedback import *
from core.framework import *
from core.generate_trials import *
from core.motor import run_trials
from core.stimuli import *
from utils.config import *

class Sensorimotor:
    def __init__(self, screen, all_results, all_acc, version):
        self.screen = screen
        self.all_results = all_results
        self.all_acc = all_acc
        self.version = version

        # Initialize and generate instruction paths/images
        self.instructions = Instructions(version)
        self.instructions.generate_paths(version)

        # Short aliases for instruction references
        self.SM_ALL_INSTRUCTIONS = self.instructions.SM_ALL_INSTRUCTIONS

        # Create stimuli instance
        self.stimuli = SensorimotorStimuli(version)

        # Generate trials
        self.practice3_trials = self.create_sm_trials(
            PRACTICE3_NUM_RED, PRACTICE3_NUM_BLUE, PRACTICE3_NUM_NOGO, "p3"
        )
        self.block3_trials = self.create_sm_trials(
            BLOCK3_NUM_RED, BLOCK3_NUM_BLUE, BLOCK3_NUM_NOGO, "b3"
        )
        self.block4_trials = self.create_sm_trials(
            BLOCK4_NUM_RED, BLOCK4_NUM_BLUE, BLOCK4_NUM_NOGO, "b4"
        )
    
    # Generate trials
    def create_sm_trials(self, num_red, num_blue, num_nogo, phase):
        trials = []
        for _ in range(num_red):
            time = random.randint(SM_MIN_FIXATION_TIME, SM_MAX_FIXATION_TIME)
            trials.append([time, self.stimuli.SM_RED, phase])
        for _ in range(num_blue):
            time = random.randint(SM_MIN_FIXATION_TIME, SM_MAX_FIXATION_TIME)
            trials.append([time, self.stimuli.SM_BLUE, phase])
        for _ in range(num_nogo):
            time = random.randint(SM_MIN_FIXATION_TIME, SM_MAX_FIXATION_TIME)
            trials.append([time, self.stimuli.SM_NOGO, phase])
        random.shuffle(trials)
        return trials

    # Read information from trials
    def read_sensorimotor_trial(self, trial):
        fixation_time, stimulus_image, phase = trial
        if stimulus_image == self.stimuli.SM_BLUE:
            if self.version == 1:
                key_correct = pygame.K_d
            else:
                key_correct = pygame.K_k
            type = "actual"
        elif stimulus_image == self.stimuli.SM_RED:
            if self.version == 1:
                key_correct = pygame.K_k
            else:
                key_correct = pygame.K_d
            type = "actual"
        elif stimulus_image == self.stimuli.SM_NOGO:
            key_correct = None
            type = "no_go"
        return fixation_time, stimulus_image, type, phase, key_correct

    def practice3(self, screen):
        results, acc = run_trials(self.practice3_trials, SM_RESPONSE_TIME, SM_ISI_TIME, "sensorimotor", self.read_sensorimotor_trial, screen)
        return results, acc

    def block3(self, screen):
        return run_trials(self.block3_trials, SM_RESPONSE_TIME, SM_ISI_TIME, "sensorimotor", self.read_sensorimotor_trial, screen)

    def block4(self, screen):
        return run_trials(self.block4_trials, SM_RESPONSE_TIME, SM_ISI_TIME, "sensorimotor", self.read_sensorimotor_trial, screen)

    # Segment 1: practice3
    def run_sm_segment1(self, next_segment_func):
        instruction_flow = []
        # Start sensorimotor pages and run merged practice3 / block3 at anchor pages.
        for i in range(PRACTICE3_PAGE - 1, BLOCK3_PAGE):
            if i == PRACTICE3_PAGE - 1:
                instruction_flow.append((self.SM_ALL_INSTRUCTIONS[i], self.practice3))
            elif i == BLOCK3_PAGE - 1:
                instruction_flow.append((self.SM_ALL_INSTRUCTIONS[i], self.block3))
            else:
                instruction_flow.append((self.SM_ALL_INSTRUCTIONS[i], None))

        def after_sm_segment1():
            next_segment_func()

        run_instruction_sequence(
            self.screen,
            instruction_flow,
            self.all_results,
            self.all_acc,
            after_sm_segment1,
        )

    # Segment 2: block 4
    def run_sm_segment2(self, next_segment_func=None):
        instruction_flow = []
        for i in range(BLOCK3_PAGE, END_PAGE):
            if i == BLOCK4_PAGE - 1:
                instruction_flow.append((self.SM_ALL_INSTRUCTIONS[i], self.block4))
            else:
                instruction_flow.append((self.SM_ALL_INSTRUCTIONS[i], None))

        def after_sm_segment2():
            if next_segment_func:
                next_segment_func()
            else:
                pygame.quit()
                quit()

        run_instruction_sequence(
            self.screen,
            instruction_flow,
            self.all_results,
            self.all_acc,
            after_sm_segment2,
            auto_exit_on_last=True,
        )
