from __future__ import annotations
from pathlib import Path
import pygame
import utils.config as cfg

# Cache loaded images to avoid disk I/O every trial
_CACHE: dict[str, pygame.Surface] = {}

# Resource paths (PNG ~400x400)
SCRIPT_DIR = Path(__file__).parent
RES_DIR = SCRIPT_DIR / ".." / ".." / "resources" / "feedback"

#RES_DIR = Path("resources") / "feedback"
PATH_CORRECT   = RES_DIR / "feedback_correct.png"
PATH_INCORRECT = RES_DIR / "feedback_incorrect.png"

def _load_image(path: Path) -> pygame.Surface:
    """Load and cache a feedback image."""
    key = str(path.resolve())
    if key in _CACHE:
        return _CACHE[key]
    if not path.exists():
        raise FileNotFoundError(f"Feedback image not found: {path}")
    img = pygame.image.load(str(path)).convert_alpha()
    _CACHE[key] = img
    return img

def _scale_to_region(screen: pygame.Surface, img: pygame.Surface, max_ratio: float = 0.14) -> pygame.Surface:
    """
    Scale feedback image relative to the shorter screen side.
    - Default 14%
    - Can be overridden via cfg.FEEDBACK_ICON_RATIO (0.05 ~ 0.20 recommended).
    - Optional hard cap via cfg.FEEDBACK_ICON_MAX_PX (e.g., 180).
    """
    sw, sh = screen.get_size()
    short = min(sw, sh)

    # Allow runtime override
    ratio = float(getattr(cfg, "FEEDBACK_ICON_RATIO", max_ratio))
    ratio = max(0.03, min(0.30, ratio))  # sane bounds

    target = int(short * ratio)
    hard_cap = getattr(cfg, "FEEDBACK_ICON_MAX_PX", None)
    if isinstance(hard_cap, (int, float)) and hard_cap > 0:
        target = min(target, int(hard_cap))

    iw, ih = img.get_width(), img.get_height()
    if max(iw, ih) <= target:
        return img
    scale = target / max(iw, ih)
    new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
    return pygame.transform.smoothscale(img, new_size)

def _feedback_anchor(screen: pygame.Surface, surf: pygame.Surface) -> tuple[int, int]:
    """Anchor feedback content slightly below the vertical center."""
    sw, sh = screen.get_size()
    rect = surf.get_rect(center=(sw // 2, int(sh * 0.72)))
    return rect.topleft

def _draw_feedback_image(screen: pygame.Surface, img: pygame.Surface) -> None:
    """Scale and blit feedback image at the anchored position."""
    scaled = _scale_to_region(screen, img, max_ratio=0.28)
    screen.blit(scaled, _feedback_anchor(screen, scaled))

def _draw_too_slow(screen: pygame.Surface, font_name: str = None) -> None:
    """Render 'Too Slow' in yellow text (instead of using an image)."""
    sw, sh = screen.get_size()
    font = pygame.font.SysFont(font_name, max(18, int(sh * 0.06)))
    yellow = getattr(cfg, "YELLOW_RGB", (255, 255, 0))
    text = font.render("Too Slow", True, yellow)
    screen.blit(text, _feedback_anchor(screen, text))

def _blit_lower_center(screen: pygame.Surface, surf: pygame.Surface, max_px: int = 400) -> None:
    """
    Scale surf to fit within max_px x max_px, then draw it at 'middle-lower' area:
    horizontally centered, vertically around ~72% screen height.
    """
    sw, sh = screen.get_size()
    iw, ih = surf.get_size()
    scale = min(max_px / iw, max_px / ih, 1.0)
    new_size = (max(1, int(iw * scale)), max(1, int(ih * scale)))
    surf_scaled = pygame.transform.smoothscale(surf, new_size)
    target_y = int(sh * 0.72)
    rect = surf_scaled.get_rect(center=(sw // 2, target_y))
    screen.blit(surf_scaled, rect.topleft)

def show_after_trial(
    screen: pygame.Surface,
    block_name: str,
    *,
    is_practice_only: bool = True,
    participant_ans: int | None = None,
    correct: bool | None = None,
    is_correct: bool | None = None,
    wait_ms: int | None = None,
) -> None:
    """
    Blocking feedback shown after a trial ends.
    Logic:
    - Only active in PRACTICE1/2/3 if is_practice_only=True.
    - First check if participant_ans is None:
        * If not None → use is_correct (True/False).
        * If None → check correct:
            - correct is None: 'no response' was expected → show correct.
            - correct is not None: response was expected but missing → show 'Too Slow'.
    - Images are scaled to 28% of shorter screen side.
    """
    if is_practice_only and block_name not in {"PRACTICE1", "PRACTICE2"}:
        return
    
    if is_practice_only == False:
        dur = wait_ms if wait_ms is not None else int(getattr(cfg, "FEEDBACK_DURATION_MS", 600))
        start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start < dur:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); raise SystemExit
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    try:
                        from src.ui.main_window import toggle_full_screen
                        toggle_full_screen(screen)
                        pygame.display.flip()
                    except Exception:
                        pass
        return

    # Decide what to show
    to_show = "image_correct"
    if participant_ans is not None:
        if bool(is_correct):
            to_show = "image_correct"
        else:
            to_show = "image_incorrect"
    else:
        if correct is None:
            to_show = "image_correct"
        else:
            to_show = "too_slow"

    # Draw feedback
    if to_show == "image_correct":
        _draw_feedback_image(screen, _load_image(PATH_CORRECT))
    else:
        _draw_feedback_image(screen, _load_image(PATH_INCORRECT))

    pygame.display.flip()

    # Block for feedback duration
    dur = wait_ms if wait_ms is not None else int(getattr(cfg, "FEEDBACK_DURATION_MS", 600))
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < dur:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); raise SystemExit
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                try:
                    from src.ui.main_window import toggle_full_screen
                    toggle_full_screen(screen)
                    pygame.display.flip()
                except Exception:
                    pass
       # pygame.time.delay(5)

def show_immediate(
    screen: pygame.Surface,
    block_name: str,
    *,
    participant_ans: int | None,
    correct: bool | None,
    is_correct: bool | None = None,
) -> None:
    """
    Non-blocking feedback shown immediately after a keypress.
    Only active in PRACTICE1/2/3. Images are scaled
    """
    if block_name not in {"PRACTICE1", "PRACTICE2"}:
        pygame.time.delay(5)
        return

    if participant_ans is not None:
        if bool(is_correct):
            _draw_feedback_image(screen, _load_image(PATH_CORRECT))
        else:
            _draw_feedback_image(screen, _load_image(PATH_INCORRECT))

    pygame.display.flip()
