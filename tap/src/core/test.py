# For Developing Only!!!

# Import
import pygame
from src.utils.config import *
from src.ui.pygame_render import *
from src.core.run_trial import *

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.mixer.init()
 
# Test run_synchronized
test_run_synchronized = False
if test_run_synchronized:
    global_start = pygame.time.get_ticks()
    run_synchronize_sound_ticks, run_synchronize_key_responses = run_synchronized(global_start, pygame.K_v, NUM_SYNCHRONIZED, STIMULUS_PATH_900)
    assert len(run_synchronize_sound_ticks) == len(run_synchronize_key_responses)
    print()
    print("Synchronized - Sound ticks:", run_synchronize_sound_ticks)
    print("Synchronized - Key responses: ", run_synchronize_key_responses)
    print()

# Test run_self_paced
test_run_self_paced = False
if test_run_self_paced:
    global_start = pygame.time.get_ticks()
    run_self_pace_key_responses = run_self_paced(global_start, pygame.K_v, NUM_SELF_PACE)
    assert len(run_self_pace_key_responses) == NUM_SELF_PACE
    print()
    print("Self-paced - Key responses: ", run_self_pace_key_responses)
    print()

# Test run_trial
test_run_trial = False
if test_run_trial:
    global_start = pygame.time.get_ticks()
    (run_synchronize_sound_ticks, 
     run_synchronize_key_responses, 
     run_self_pace_key_responses) = run_trial(global_start, 
                                              pygame.K_v, 
                                              NUM_SYNCHRONIZED, 
                                              NUM_SELF_PACE, 
                                              STIMULUS_PATH_900)
    assert len(run_synchronize_sound_ticks) == len(run_synchronize_key_responses) 
    assert len(run_self_pace_key_responses) == NUM_SELF_PACE
    print()
    print("Synchronized - Sound ticks:", run_synchronize_sound_ticks)
    print("Synchronized - Key responses: ", run_synchronize_key_responses)
    print("Self-paced - Key responses: ", run_self_pace_key_responses)
    print()

# Test practice1
test_practice1 = True
if test_practice1:
    global_start = pygame.time.get_ticks()
    results = []
    # single_trail("practice1", global_start, pygame.K_v, results)
    for result in results:
        print()
        print(result)