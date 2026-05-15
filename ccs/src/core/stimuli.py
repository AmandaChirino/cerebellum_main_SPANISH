import pygame

from utils.paths import STIMULI_DIR, load_stimuli

# Motor / Sensorimotor shared circle assets
M_FIXATION = pygame.image.load(str(STIMULI_DIR / "CCS_Fixation.png"))
M_BLUE = pygame.image.load(str(STIMULI_DIR / "CCS_Blue.png"))
M_RED = pygame.image.load(str(STIMULI_DIR / "CCS_Red.png"))
M_NOGO = pygame.image.load(str(STIMULI_DIR / "CCS_Fixation.png"))


# Sensorimotor
class SensorimotorStimuli:
    def __init__(self, version):
        self.version = version
        self.load_stimuli()

    def load_stimuli(self):
        paths = load_stimuli(self.version)

        # Load images
        self.SM_FIXATION = pygame.image.load(str(paths["fixation"]))
        self.SM_BLUE = pygame.image.load(str(paths["blue"]))
        self.SM_RED = pygame.image.load(str(paths["red"]))
        self.SM_NOGO = pygame.image.load(str(paths["white"]))
        self.SM_MAPPING = pygame.image.load(str(paths["mapping"]))
