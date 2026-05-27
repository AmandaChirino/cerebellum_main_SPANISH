import pygame

from utils.config import *
from utils.paths import FEEDBACK_DIR

# Get feedback icons
CORRECT_IMG_RAW = pygame.image.load(str(FEEDBACK_DIR / "feedback_correct.png"))
INCORRECT_IMG_RAW = pygame.image.load(str(FEEDBACK_DIR / "feedback_incorrect.png"))

CORRECT_IMG = pygame.transform.smoothscale(CORRECT_IMG_RAW, (
    CORRECT_IMG_RAW.get_width() // 5,
    CORRECT_IMG_RAW.get_height() // 5
))
INCORRECT_IMG = pygame.transform.smoothscale(INCORRECT_IMG_RAW, (
    INCORRECT_IMG_RAW.get_width() // 5,
    INCORRECT_IMG_RAW.get_height() // 5
))

# Show feedback (temporary placeholder - will be changed to use images later)
def show_feedback(screen, correct, timeout, background, duration_ms):
    from core.framework import get_scaled_stimulus
    
    screen_rect = screen.get_rect()

    center_x = screen_rect.centerx
    center_y = screen_rect.centery + 200

    # Scale and center the background stimulus
    background_scaled = get_scaled_stimulus(background, screen)
    background_rect = background_scaled.get_rect(center=screen_rect.center)
    screen.blit(background_scaled, background_rect)
    
    if timeout:
        font = pygame.font.SysFont(None, 72)
        text = font.render("Too Late!", True, YELLOW_RGB)
        text_rect = text.get_rect(center=(center_x, center_y))
        screen.blit(text, text_rect)
    else:
        img = CORRECT_IMG if correct else INCORRECT_IMG
        img_rect = img.get_rect(center=(center_x, center_y))
        screen.blit(img, img_rect)
    
    pygame.display.flip()
    pygame.time.wait(duration_ms)
    pygame.event.clear()


def draw_feedback_overlay(screen, correct, timeout=False):
    """
    Draw feedback on top of current screen content without blocking.
    Caller controls display flip and timing.
    """
    screen_rect = screen.get_rect()

    center_x = screen_rect.centerx
    center_y = screen_rect.centery + 200

    if timeout:
        font = pygame.font.SysFont(None, 55)
        text = font.render("Too Late!", True, YELLOW_RGB)
        text_rect = text.get_rect(center=(center_x, center_y))
        screen.blit(text, text_rect)
    else:
        img = CORRECT_IMG if correct else INCORRECT_IMG
        img_rect = img.get_rect(center=(center_x, center_y))
        screen.blit(img, img_rect)
