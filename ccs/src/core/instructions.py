import pygame

from utils.config import END_PAGE
from utils.paths import load_instructions


class Instructions:
    def __init__(self, version):
        self.version = version

        # Motor and sensorimotor now share the same instruction pages.
        self.M_INSTRUCTION_PATH = None
        self.M_ALL_INSTRUCTIONS = []

        self.SM_INSTRUCTION_PATH = None
        self.SM_ALL_INSTRUCTIONS = []

    def generate_paths(self, version):
        all_instructions = [
            pygame.image.load(str(p)) for p in load_instructions(END_PAGE, version)
        ]

        self.M_INSTRUCTION_PATH = None
        self.M_ALL_INSTRUCTIONS = all_instructions

        self.SM_INSTRUCTION_PATH = None
        self.SM_ALL_INSTRUCTIONS = all_instructions
