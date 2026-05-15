import pygame

from core.instructions import *
from core.stimuli import *
import utils.config as cfg
from utils.config import *
from utils.event_handler import EventHandler

GlobalParticipantName = ""

# Toggle fullscreen function
def toggle_fullscreen(screen):
    global SCREEN_W, SCREEN_H
    screen_info = pygame.display.Info()

    if screen.get_flags() & pygame.FULLSCREEN:
        # Switch to windowed mode
        # Use 80% of screen size for windowed mode to ensure it fits
        window_width = int(screen_info.current_w * 0.8)
        window_height = int(screen_info.current_h * 0.8)

        # Ensure minimum size but not larger than screen
        SCREEN_W = max(1024, min(window_width, screen_info.current_w - 100))
        SCREEN_H = max(768, min(window_height, screen_info.current_h - 100))

        new_screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        print(f"Switched to windowed mode: {SCREEN_W}x{SCREEN_H}")
    else:
        # Switch to fullscreen mode
        SCREEN_W = screen_info.current_w
        SCREEN_H = screen_info.current_h
        new_screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
        print(f"Switched to fullscreen mode: {SCREEN_W}x{SCREEN_H}")
    
    # Update the global screen reference and meta_parameters
    import core.framework as framework
    framework.screen = new_screen
    cfg.SCREEN_W = SCREEN_W
    cfg.SCREEN_H = SCREEN_H
    
    return new_screen

# Show Participant ID input page
def get_participant_id(screen):
    font = pygame.font.SysFont(None, 48)
    input_text = ""
    active = True
    event_handler = EventHandler()

    global GlobalParticipantName

    while active:
        screen.fill(BLACK_RGB)
        screen_rect = screen.get_rect()
        
        prompt = font.render("Enter Participant ID (press enter when completed):", True, COCO_RGB)
        text_surface = font.render(input_text, True, COCO_RGB)
        
        # Center text using dynamic screen dimensions
        screen.blit(prompt, (screen_rect.centerx - prompt.get_width() // 2, screen_rect.centery - 100))
        screen.blit(text_surface, (screen_rect.centerx - text_surface.get_width() // 2, screen_rect.centery))
        pygame.display.flip()

        state = event_handler.poll()
        if state.quit:
            pygame.quit()
            quit()
        if state.toggle_full_screen:
            screen = toggle_fullscreen(screen)
        if state.confirm and input_text != "":
            active = False
        elif state.backspace:
            input_text = input_text[:-1]
        elif state.text_input:
            input_text += state.text_input
    GlobalParticipantName = input_text
    print("entered participant ID:", GlobalParticipantName)
    return input_text

def GetParticipantId():
    return GlobalParticipantName

# Scale stimulus to fit screen while maintaining aspect ratio
def get_scaled_stimulus(image, screen):
    """
    Scale an image to fit within 90% of the screen size while maintaining aspect ratio.
    This ensures proper centering and display across different screen resolutions.
    """
    screen_width = screen.get_width()
    screen_height = screen.get_height()
    
    # Target area is 90% of screen size
    target_width = int(screen_width * 0.9)
    target_height = int(screen_height * 0.9)
    
    # Get original image dimensions
    img_width = image.get_width()
    img_height = image.get_height()
    
    # Calculate scaling factor to fit within target area while maintaining aspect ratio
    scale_x = target_width / img_width
    scale_y = target_height / img_height
    scale_factor = min(scale_x, scale_y)
    
    # Calculate new dimensions
    new_width = int(img_width * scale_factor)
    new_height = int(img_height * scale_factor)
    
    # Scale the image using smooth scaling to prevent pixelation
    scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))
    
    return scaled_image

# Show instruction flow handler
def run_instruction_flow(screen, instruction_flow, all_results, all_acc, next_segment_func):
    """
    Handle a sequence of instructions and practice/block tasks
    instruction_flow: list of tuples (type, content) where type is "instruction" or "practice"/"block"
    """
    def process_flow(index):
        if index >= len(instruction_flow):
            next_segment_func()
            return
        
        flow_type, content = instruction_flow[index]
        
        if flow_type == "instruction":
            # Show instruction page
            show_instruction(
                screen,
                content,
                lambda: process_flow(index + 1),
                is_last_instruction=(index == len(instruction_flow) - 1),
            )
        elif flow_type in ["practice", "block"]:
            # Run practice or block
            results, acc = content(screen)
            all_results.extend(results)
            all_acc.append(acc)
            process_flow(index + 1)
    
    process_flow(0)

# Show one instruction page, then call next_func
def show_instruction(screen, instruction_page, next_func, is_last_instruction=False):
    # Clear screen with gray background
    screen.fill(BLACK_RGB)
    
    # Scale instruction image to fit screen properly
    scaled_instruction = get_scaled_stimulus(instruction_page, screen)
    
    # Center the instruction on screen
    screen_rect = screen.get_rect()
    instruction_rect = scaled_instruction.get_rect(center=screen_rect.center)
    
    # Display the scaled and centered instruction
    screen.blit(scaled_instruction, instruction_rect)
    pygame.display.flip()

    pygame.event.clear()
    page_start_time = pygame.time.get_ticks()
    event_handler = EventHandler()

    while pygame.time.get_ticks() - page_start_time < cfg.READ_TIME:
        state = event_handler.poll()
        if state.quit:
            pygame.quit()
            raise SystemExit
        if state.toggle_full_screen:
            screen = toggle_fullscreen(screen)
            # Redraw instruction after screen change
            screen.fill(BLACK_RGB)
            scaled_instruction = get_scaled_stimulus(instruction_page, screen)
            screen_rect = screen.get_rect()
            instruction_rect = scaled_instruction.get_rect(center=screen_rect.center)
            screen.blit(scaled_instruction, instruction_rect)
            pygame.display.flip()

    waiting = True
    wait_start_time = pygame.time.get_ticks()
    while waiting:
        state = event_handler.poll()
        if state.quit:
            pygame.quit()
            raise SystemExit
        if state.toggle_full_screen:
            screen = toggle_fullscreen(screen)
            # Redraw instruction after screen change
            screen.fill(BLACK_RGB)
            scaled_instruction = get_scaled_stimulus(instruction_page, screen)
            screen_rect = screen.get_rect()
            instruction_rect = scaled_instruction.get_rect(center=screen_rect.center)
            screen.blit(scaled_instruction, instruction_rect)
            pygame.display.flip()
        elif state.next_page:
            waiting = False

        if is_last_instruction and (pygame.time.get_ticks() - wait_start_time >= cfg.LAST_INSTRUCTION_AUTO_EXIT_MS):
            pygame.quit()
            raise SystemExit

    next_func()

# Reusable recursive flow handler
def run_instruction_sequence(
    screen,
    flow,
    all_results,
    all_acc,
    final_callback,
    index=0,
    auto_exit_on_last=False,
):
    if index >= len(flow):
        final_callback()
        return

    page, task_func = flow[index]

    def next_step():
        if task_func:
            # Page turn before starting trials: clear the previous instruction page.
            screen.fill(BLACK_RGB)
            pygame.display.flip()
            pygame.event.clear()
            # Pre-block ISI before the first fixation cross
            pygame.time.delay(cfg.M_ISI_TIME)
            results, acc = task_func(screen)
            all_results.extend(results)
            all_acc.append(acc)
        run_instruction_sequence(screen, flow, all_results, all_acc, final_callback, index + 1)

    show_instruction(
        screen,
        page,
        next_step,
        is_last_instruction=(auto_exit_on_last and index == len(flow) - 1),
    )
