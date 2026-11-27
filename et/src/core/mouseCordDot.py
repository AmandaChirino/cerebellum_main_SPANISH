import pygame
import random
import numpy as np
import pandas as pd
from pathlib import Path

import utils.config as cfg

class MouseCordDot:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.x = 0.0
        self.y = 0.0

    def _half_px(self) -> float:
        # Pixels the mouse travels from the center to the end of the bar
        return cfg.SLIDER_HALF_LENGTH * self.screen.get_height()

    def set_pos(self, pos: tuple[float, float]):
        self.x, self.y = pos
        w, h = self.screen.get_size()
        half_px = self._half_px()
        # Normalised values back to screen pixels (y grows downwards on screen)
        screen_x = int(w / 2 + self.x * half_px)
        screen_y = int(h / 2 - self.y * half_px)
        pygame.mouse.set_pos(screen_x, screen_y)

    def get_pos(self) -> tuple[float, float]:
        mx, my = pygame.mouse.get_pos()
        w, h = self.screen.get_size()
        half_px = self._half_px()
        # Mouse position relative to the screen center, scaled so the bar ends are +-1
        self.x = (mx - w / 2) / half_px
        self.y = (h / 2 - my) / half_px
        return (self.x, self.y)

    def clamp(self, limit: float = 1.0):
        x, y = self.get_pos()
        clamped_x = max(-limit, min(limit, x))
        clamped_y = max(-limit, min(limit, y))
        if clamped_x != x or clamped_y != y:
            self.set_pos((clamped_x, clamped_y))
        return (clamped_x, clamped_y)