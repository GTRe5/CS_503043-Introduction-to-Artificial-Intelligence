import pygame
import sys
import pickle
import threading
import random
from State import State
from Problem import TicTacToeProblem
from AI import AIPlayer
import math

# --- Configuration ---
WIDTH, HEIGHT = 600, 700
ROWS, COLS = 9, 9
SQUARE_SIZE = WIDTH // COLS

LINE_COLOR = (200, 200, 200)
BG_COLOR = (255, 255, 255)
X_COLOR = (50, 50, 50)
O_COLOR = (50, 50, 50)
TEXT_COLOR = (0, 0, 0)

LINE_WIDTH = 3
CIRCLE_RADIUS = SQUARE_SIZE // 3
SPACE = SQUARE_SIZE // 4
HIGHLIGHT_COLOR = (255, 0, 0)

RESET_BTN_RECT = pygame.Rect(WIDTH - 120, HEIGHT - 62, 100, 50)
RESET_BTN_COLOR = (70, 130, 180)
RESET_BTN_HOVER_COLOR = (100, 160, 210)

UNDO_BTN_RECT = pygame.Rect(WIDTH - 240, HEIGHT - 62, 100, 50)
UNDO_BTN_COLOR = (180, 130, 70)
UNDO_BTN_HOVER_COLOR = (210, 160, 100)

BTN_TEXT_COLOR = (255, 255, 255)

HOME_BTN_RECT = pygame.Rect(WIDTH - 360, HEIGHT - 62, 100, 50)
HOME_BTN_COLOR = (70, 130, 180)          
HOME_BTN_HOVER_COLOR = (100, 160, 210)

INTRO_NEW_GAME_RECT   = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 - 60, 220, 50)

INTRO_CONTINUE_RECT   = pygame.Rect(WIDTH//2 - 110, HEIGHT//2,       220, 50)

EXIT_INTRO_RECT = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 120, 220, 50)
EXIT_INTRO_COLOR = (180, 70, 70)
EXIT_INTRO_HOVER_COLOR = (210, 100, 100)

TUTORIAL_BTN_RECT     = pygame.Rect(WIDTH//2 - 110, HEIGHT//2 + 60,  220, 50)
TUTORIAL_BTN_COLOR        = (100, 100, 180)
TUTORIAL_BTN_HOVER_COLOR  = (130, 130, 210)

EASY_BTN_RECT = pygame.Rect(WIDTH//2 - 160, HEIGHT//2 - 120, 100, 40)
MEDIUM_BTN_RECT = pygame.Rect(WIDTH//2 - 50, HEIGHT//2 - 120, 100, 40)
HARD_BTN_RECT = pygame.Rect(WIDTH//2 + 60, HEIGHT//2 - 120, 100, 40)


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tic Tac Toe 9x9 - Handwriting Style")
font = pygame.font.SysFont(None, 40)

SAVE_FILE = "Storage/saved_game.pkl"

# Load pen image và resize
pen_image = pygame.image.load("Png/pen.png").convert_alpha()
pen_image = pygame.transform.scale(pen_image, (90, 90))

clock = pygame.time.Clock()

def draw_lines():
    for i in range(1, ROWS):
        pygame.draw.line(screen, LINE_COLOR, (0, i * SQUARE_SIZE), (WIDTH, i * SQUARE_SIZE), LINE_WIDTH)
    for i in range(1, COLS):
        pygame.draw.line(screen, LINE_COLOR, (i * SQUARE_SIZE, 0), (i * SQUARE_SIZE, HEIGHT - 40), LINE_WIDTH)

def draw_figures(state, skip=None):
    if skip is None:
        skip = set()
    for r in range(ROWS):
        for c in range(COLS):
            if (r, c) in skip:
                continue
            symbol = state.grid[r][c]
            center_x = c * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = r * SQUARE_SIZE + SQUARE_SIZE // 2

            if symbol == "O":
                for _ in range(6):
                    offset_x = random.randint(-2, 2)
                    offset_y = random.randint(-2, 2)
                    pygame.draw.ellipse(
                        screen, O_COLOR,
                        (
                            center_x - CIRCLE_RADIUS + offset_x,
                            center_y - CIRCLE_RADIUS + offset_y,
                            CIRCLE_RADIUS * 2,
                            CIRCLE_RADIUS * 2
                        ),
                        1
                    )
            elif symbol == "X":
                for _ in range(5):
                    offset1 = random.randint(-2, 2)
                    offset2 = random.randint(-2, 2)
                    start1 = (c * SQUARE_SIZE + SPACE + offset1, r * SQUARE_SIZE + SPACE + offset2)
                    end1 = (c * SQUARE_SIZE + SQUARE_SIZE - SPACE + offset1, r * SQUARE_SIZE + SQUARE_SIZE - SPACE + offset2)
                    start2 = (c * SQUARE_SIZE + SPACE + offset1, r * SQUARE_SIZE + SQUARE_SIZE - SPACE + offset2)
                    end2 = (c * SQUARE_SIZE + SQUARE_SIZE - SPACE + offset1, r * SQUARE_SIZE + SPACE + offset2)
                    pygame.draw.aaline(screen, X_COLOR, start1, end1)
                    pygame.draw.aaline(screen, X_COLOR, start2, end2)

def get_cell_center(r, c):
    x = c * SQUARE_SIZE + SQUARE_SIZE // 2
    y = r * SQUARE_SIZE + SQUARE_SIZE // 2
    return (x, y)

def draw_highlight(line, screen, state, color=(255, 0, 0), width=6, speed=10):
    start_pos = get_cell_center(*line[0])
    end_pos = get_cell_center(*line[-1])

    total_length = ((end_pos[0] - start_pos[0]) ** 2 + (end_pos[1] - start_pos[1]) ** 2) ** 0.5
    progress = 0

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                return

        background_image = pygame.image.load("Png/background.png").convert()
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

        screen.blit(background_image, (0, 0))  # Or redraw the game background
        # Redraw the cells and game states if necessary (or you have a function to redraw the board)
        draw_figures(state)
        draw_lines()

        # Calculate the length of the current segment of the animation
        progress += speed
        if progress > total_length:
            progress = total_length
            running = False

        # Calculate the ending point of the animation line segment
        progress_ratio = progress / total_length
        current_x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress_ratio
        current_y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress_ratio

        # Vẽ đoạn thẳng animation
        pygame.draw.line(screen, color, start_pos, (current_x, current_y), width)

        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    # After the animation is finished, you can display the results table here or call another function.

def draw_status(text, difficulty=None):
    pygame.draw.rect(screen, BG_COLOR, (0, HEIGHT - 80, WIDTH, 80))
    msg = font.render(text, True, TEXT_COLOR)
    screen.blit(msg, (10, HEIGHT - 70))
    
    if difficulty:
        difficulty_text = f"{difficulty}"
        diff_msg = font.render(difficulty_text, True, TEXT_COLOR)
        # Draw to the right or below the main status line
        screen.blit(diff_msg, (10, HEIGHT - 35))


def draw_button(rect, text, mouse_pos, color, hover_color, enabled=True):
    btn_color = color if enabled else (180, 180, 180)
    if enabled and rect.collidepoint(mouse_pos):
        btn_color = hover_color
    pygame.draw.rect(screen, btn_color, rect, border_radius=5)
    txt = font.render(text, True, BTN_TEXT_COLOR)
    txt_rect = txt.get_rect(center=rect.center)
    screen.blit(txt, txt_rect)

def save_game(history, difficulty):
    data = {
        'history': history,
        'difficulty': difficulty
    }
    with open(SAVE_FILE, "wb") as f:
        pickle.dump(data, f)

def load_game():
    try:
        with open(SAVE_FILE, "rb") as f:
            data = pickle.load(f)
            # kiểm tra kiểu dữ liệu và keys
            if isinstance(data, dict) and 'history' in data and 'difficulty' in data:
                return data['history'], data['difficulty']
            else:
                return None, None
    except (FileNotFoundError, EOFError, pickle.UnpicklingError):
        return None, None

def intro_screen(can_continue, ai_stop_event, ai_thread):
    background_image = pygame.image.load("Png/background.png").convert()
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

    while True:
        screen.blit(background_image, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        title = font.render("Tic Tac Toe 9x9", True, TEXT_COLOR)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))

        draw_button(INTRO_NEW_GAME_RECT, "New Game", mouse_pos, RESET_BTN_COLOR, RESET_BTN_HOVER_COLOR)

        # Draw the Continue button with enabled based on can_continue
        draw_button(INTRO_CONTINUE_RECT, "Continue", mouse_pos, UNDO_BTN_COLOR, UNDO_BTN_HOVER_COLOR, enabled=can_continue)

        draw_button(EXIT_INTRO_RECT, "Exit", mouse_pos, EXIT_INTRO_COLOR, EXIT_INTRO_HOVER_COLOR)

        draw_button(TUTORIAL_BTN_RECT, "Tutorial", mouse_pos, TUTORIAL_BTN_COLOR, TUTORIAL_BTN_HOVER_COLOR)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if INTRO_NEW_GAME_RECT.collidepoint(event.pos):
                    difficulty = difficulty_screen()  # call the difficulty selection screen
                    return "new", difficulty  # return tuple
                elif INTRO_CONTINUE_RECT.collidepoint(event.pos) and can_continue:
                    return "continue", None
                elif EXIT_INTRO_RECT.collidepoint(event.pos):
                    ai_stop_event.set()
                    if ai_thread and ai_thread.is_alive():
                        ai_thread.join(timeout=1)
                    pygame.quit()
                    sys.exit()
                elif TUTORIAL_BTN_RECT.collidepoint(event.pos):
                    show_tutorial()

def difficulty_screen():
    background_image = pygame.image.load("Png/background.png").convert()
    background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

    while True:
        screen.blit(background_image, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

        title = font.render("Select Difficulty", True, TEXT_COLOR)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 4))

        easy_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 70, 200, 50)
        medium_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
        hard_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 50)

        draw_button(easy_rect, "Easy", mouse_pos, RESET_BTN_COLOR, RESET_BTN_HOVER_COLOR)
        draw_button(medium_rect, "Medium", mouse_pos, RESET_BTN_COLOR, RESET_BTN_HOVER_COLOR)
        draw_button(hard_rect, "Hard", mouse_pos, RESET_BTN_COLOR, RESET_BTN_HOVER_COLOR)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if easy_rect.collidepoint(event.pos):
                    return 2
                elif medium_rect.collidepoint(event.pos):
                    return 3
                elif hard_rect.collidepoint(event.pos):
                    return 5


def show_tutorial():
    tutorial_text = [
        "Tic Tac Toe 9x9",
        "",
        "- X goes first, O goes after.",
        "- The player are always x.",
        "- Choose an empty box to play.",
        "- The side that creates 4 consecutive characters",
        "  (in rows, columns or diagonals) wins.",
        "",
        "Press ESC or click anywhere to exit the instructions."
    ]

    tutorial_font = pygame.font.Font(None, 24)  # default font Pygame
    text_color = (30, 30, 30)
    box_color = (255, 255, 240)
    box_border_color = (120, 120, 120)

    box_rect = pygame.Rect(WIDTH//2 - 270, HEIGHT//2 - 190, 540, 380)

    running = True
    while running:
        screen.fill((230, 230, 210))

        pygame.draw.rect(screen, box_color, box_rect, border_radius=15)
        pygame.draw.rect(screen, box_border_color, box_rect, 3, border_radius=15)

        for i, line in enumerate(tutorial_text):
            x = box_rect.x + 30
            y = box_rect.y + 30 + i * 35

            # Chỉ vẽ chữ, không vẽ shadow
            text_surf = tutorial_font.render(line, True, text_color)
            screen.blit(text_surf, (x, y))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                running = False

def animate_drawing(row, col, symbol, current_state, winning_line):
    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2

    steps = 15
    for step in range(steps + 1):
        background_image = pygame.image.load("Png/background.png").convert()
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

        screen.blit(background_image, (0, 0))
        draw_lines()
        draw_figures(current_state, skip={(row, col)})
        if winning_line:
            draw_highlight(winning_line, screen, current_state)

        progress = step / steps

        if symbol == "O":
            # Draw a circular arc from angle 0 to progress*2π
            rect = (
                center_x - CIRCLE_RADIUS,
                center_y - CIRCLE_RADIUS,
                CIRCLE_RADIUS * 2,
                CIRCLE_RADIUS * 2
            )
            pygame.draw.arc(screen, O_COLOR, rect, 0, progress * 2 * 3.14159, 2)

            # Calculate the position of the pen on the circular arc at the angle = progress * 2π
            angle = progress * 2 * 3.14159
            pen_x = center_x + CIRCLE_RADIUS * math.cos(angle) - pen_image.get_width() // 2
            pen_y = center_y + CIRCLE_RADIUS * math.sin(angle) - pen_image.get_height() // 2

        elif symbol == "X":
            length = SQUARE_SIZE - 2 * SPACE
            # Diagonal line 1: from start1 to end1, move according to progress.
            start1 = (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SPACE)
            end1 = (start1[0] + length, start1[1] + length)
            offset = int(progress * length)
            current_end1 = (start1[0] + offset, start1[1] + offset)
            pygame.draw.aaline(screen, X_COLOR, start1, current_end1)

            if progress > 0.5:
                # Diagonal line 2: from start2 to end2, move according to progress.
                start2 = (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE)
                end2 = (start2[0] + length, start2[1] - length)
                offset2 = int((progress - 0.5) * 2 * length)
                current_end2 = (start2[0] + offset2, start2[1] - offset2)
                pygame.draw.aaline(screen, X_COLOR, start2, current_end2)

                # The pen is at diagonal line 2, current position.
                pen_x = current_end2[0] - pen_image.get_width() // 2
                pen_y = current_end2[1] - pen_image.get_height() // 2
            else:
                # The pen is at diagonal line 1, current position.
                pen_x = current_end1[0] - pen_image.get_width() // 2
                pen_y = current_end1[1] - pen_image.get_height() // 2

        # Draw pen
        screen.blit(pen_image, (pen_x, pen_y))

        pygame.display.update()
        clock.tick(30)

    # Redraw the entire image after the animation is finished.
    draw_figures(current_state)
    center_x = col * SQUARE_SIZE + SQUARE_SIZE // 2
    center_y = row * SQUARE_SIZE + SQUARE_SIZE // 2

    steps = 15
    for step in range(steps + 1):
        background_image = pygame.image.load("Png/background.png").convert()
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

        screen.blit(background_image, (0, 0))
        draw_lines()
        draw_figures(current_state, skip={(row, col)})
        if winning_line:
            draw_highlight(winning_line, screen, current_state)

        # Bút có thể lắc nhẹ
        pen_x = center_x - 45 + random.randint(-3, 3)  # -45 because the pen is wide 90
        pen_y = center_y - 45 + random.randint(-3, 3)
        screen.blit(pen_image, (pen_x, pen_y))

        progress = step / steps

        if symbol == "O":
            pygame.draw.arc(
                screen,
                O_COLOR,
                (
                    center_x - CIRCLE_RADIUS,
                    center_y - CIRCLE_RADIUS,
                    CIRCLE_RADIUS * 2,
                    CIRCLE_RADIUS * 2
                ),
                0,
                progress * 2 * 3.14159,
                2
            )
        elif symbol == "X":
            offset = int(progress * (SQUARE_SIZE - 2 * SPACE))
            start1 = (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SPACE)
            end1 = (start1[0] + offset, start1[1] + offset)
            pygame.draw.aaline(screen, X_COLOR, start1, end1)

            if progress > 0.5:
                offset2 = int((progress - 0.5) * 2 * (SQUARE_SIZE - 2 * SPACE))
                start2 = (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SQUARE_SIZE - SPACE)
                end2 = (start2[0] + offset2, start2[1] - offset2)
                pygame.draw.aaline(screen, X_COLOR, start2, end2)

        pygame.display.update()
        clock.tick(30)

    # Redraw the entire image after the animation is finished.
    draw_figures(current_state)

def draw_end_screen(winner_text, mouse_pos):
    overlay_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 80, 300, 160)
    pygame.draw.rect(screen, (240, 240, 240), overlay_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), overlay_rect, 3, border_radius=10)

    # Text announces wins and losses
    msg = font.render(winner_text, True, (0, 0, 0))
    screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 - 60))

    # Again button
    again_rect = pygame.Rect(WIDTH//2 - 130, HEIGHT//2 + 20, 100, 40)
    draw_button(again_rect, "Again", mouse_pos, RESET_BTN_COLOR, RESET_BTN_HOVER_COLOR)

    # Home button
    home_rect = pygame.Rect(WIDTH//2 + 30, HEIGHT//2 + 20, 100, 40)
    draw_button(home_rect, "Home", mouse_pos, UNDO_BTN_COLOR, UNDO_BTN_HOVER_COLOR)

    return again_rect, home_rect

def difficulty_name_from_value(value):
    if value == 2:
        return "Easy"
    elif value == 3:
        return "Medium"
    elif value == 5:
        return "Hard"
    else:
        return "Unknown"

def main():
    current_state = None
    problem = None
    ai = None
    game_over = False
    history = []
    winning_line = None

    ai_move = None
    ai_thinking = False
    ai_stop_event = threading.Event()
    ai_thread = None

    show_end_screen = False
    again_rect, home_rect = None, None
    depth_limit = 100
    
    EXIT_BTN_RECT = pygame.Rect(WIDTH - 360, HEIGHT - 45, 100, 35)
    EXIT_BTN_COLOR = (180, 70, 70)
    EXIT_BTN_HOVER_COLOR = (210, 100, 100)


    def reset_game():
        nonlocal current_state, problem, ai, game_over, history, winning_line, ai_move, ai_thinking
        current_state = State()
        problem = TicTacToeProblem(current_state, ai_symbol="O")
        ai = AIPlayer(problem, depth_limit=depth_limit)
        game_over = False
        history.clear()
        history.append(current_state)
        winning_line = None
        ai_move = None
        ai_thinking = False
        background_image = pygame.image.load("Png/background.png").convert()
        background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

        screen.blit(background_image, (0, 0))
        draw_lines()
        difficulty = difficulty_name_from_value(depth_limit)
        draw_status("Your turn (X)", difficulty)
        pygame.display.update()

    def undo_move():
        nonlocal current_state, problem, ai, game_over, history, winning_line
        if len(history) > 1 and not game_over:
            history.pop()
            history.pop()
            current_state = history[-1]
            problem = TicTacToeProblem(current_state, ai_symbol="O")
            ai = AIPlayer(problem, depth_limit=depth_limit)
            winning_line = None
            background_image = pygame.image.load("Png/background.png").convert()
            background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

            screen.blit(background_image, (0, 0))
            draw_lines()
            draw_figures(current_state)
            difficulty = difficulty_name_from_value(depth_limit)
            draw_status("Your turn (X)", difficulty)
            pygame.display.update()

    def ai_think(state):
        nonlocal ai_move, ai_thinking
        if not ai_stop_event.is_set():
            ai_move = ai.get_move(state, ai_stop_event)
        ai_thinking = False


    choice, depth_limit = intro_screen(current_state, ai_stop_event, ai_thread)
    if choice == "new":
        reset_game()
    elif choice == "continue":
        # Load saved game or reset if none
        loaded_history, depth_limit = load_game()
        if loaded_history:
            # ... setup like first
            pass
        else:
            reset_game()

    while True:
        mouse_pos = pygame.mouse.get_pos()
        undo_enabled = len(history) > 1 and not game_over and not ai_thinking
        reset_enabled = not ai_thinking and not game_over

        # Draw the main nodes before finishing
        if not show_end_screen:
            draw_button(HOME_BTN_RECT, "Home", mouse_pos, HOME_BTN_COLOR, HOME_BTN_HOVER_COLOR)
            draw_button(RESET_BTN_RECT, "Reset", mouse_pos, RESET_BTN_COLOR, RESET_BTN_HOVER_COLOR, enabled=reset_enabled)
            draw_button(UNDO_BTN_RECT, "Undo", mouse_pos, UNDO_BTN_COLOR, UNDO_BTN_HOVER_COLOR, enabled=undo_enabled)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game(history, depth_limit)
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    reset_game()
                    show_end_screen = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if show_end_screen:
                    # If you are at the end screen, check and press the Again or Home button.
                    if again_rect and again_rect.collidepoint(event.pos):
                        reset_game()
                        show_end_screen = False
                    elif home_rect and home_rect.collidepoint(event.pos):
                        # Return to the intro screen
                        choice, depth_limit = intro_screen(current_state, ai_stop_event, ai_thread)
                        if choice == "new":
                            reset_game()
                            show_end_screen = False
                        elif choice == "continue":
                            loaded_history, depth_limit = load_game()
                            if loaded_history:
                                history = loaded_history
                                current_state = history[-1]
                                problem = TicTacToeProblem(current_state, ai_symbol="O")
                                ai = AIPlayer(problem, depth_limit=depth_limit)
                                game_over = problem.goal_test(current_state)
                                winning_line = current_state.get_winning_line("X") or current_state.get_winning_line("O") if game_over else None
                                background_image = pygame.image.load("Png/background.png").convert()
                                background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

                                screen.blit(background_image, (0, 0))
                                draw_lines()
                                draw_figures(current_state)
                                if winning_line:
                                    draw_highlight(winning_line, screen, current_state)
                                if ai_thinking:
                                    difficulty = difficulty_name_from_value(depth_limit)
                                    draw_status("AI thinking...", difficulty)
                                else:
                                    player = current_state.current_player
                                    difficulty = difficulty_name_from_value(depth_limit)
                                    draw_status(f"Your turn ({player})", difficulty)
                                pygame.display.update()
                            else:
                                reset_game()
                                show_end_screen = False
                        else:
                            pygame.quit()
                            sys.exit()

                else:
                    # Processing normal nodes before completion
                    if EXIT_BTN_RECT.collidepoint(event.pos):
                        save_game(history, depth_limit)
                        choice, depth_limit = intro_screen(current_state, ai_stop_event, ai_thread)
                        if choice == "new":
                            reset_game()
                            show_end_screen = False
                        elif choice == "continue":
                            loaded_history, depth_limit = load_game()
                            if loaded_history:
                                history = loaded_history
                                current_state = history[-1]
                                problem = TicTacToeProblem(current_state, ai_symbol="O")
                                ai = AIPlayer(problem, depth_limit=depth_limit)
                                game_over = problem.goal_test(current_state)
                                winning_line = current_state.get_winning_line("X") or current_state.get_winning_line("O") if game_over else None
                                background_image = pygame.image.load("Png/background.png").convert()
                                background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

                                screen.blit(background_image, (0, 0))
                                draw_lines()
                                draw_figures(current_state)
                                if winning_line:
                                    draw_highlight(winning_line, screen, current_state)
                                elif ai_thinking:
                                    difficulty = difficulty_name_from_value(depth_limit)
                                    draw_status("AI thinking...", difficulty)
                                else:
                                    player = current_state.current_player
                                    difficulty = difficulty_name_from_value(depth_limit)
                                    draw_status(f"Your turn ({player})", difficulty)
                                pygame.display.update()
                            else:
                                reset_game()
                                show_end_screen = False
                        else:
                            pygame.quit()
                            sys.exit()
                    elif RESET_BTN_RECT.collidepoint(event.pos) and reset_enabled:
                        reset_game()
                        show_end_screen = False
                        continue
                    elif UNDO_BTN_RECT.collidepoint(event.pos) and undo_enabled:
                        undo_move()
                        continue

                    # Player Turn Handling (X)
                    if not game_over and current_state.current_player == "X" and not ai_thinking:
                        x, y = event.pos
                        if y >= HEIGHT - 50:
                            continue
                        row = y // SQUARE_SIZE
                        col = x // SQUARE_SIZE
                        if (row, col) in current_state.get_actions():
                            next_state = current_state.result((row, col))
                            animate_drawing(row, col, "X", current_state, winning_line)
                            current_state = next_state
                            history.append(current_state)
                            background_image = pygame.image.load("Png/background.png").convert()
                            background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

                            screen.blit(background_image, (0, 0))
                            draw_lines()
                            draw_figures(current_state)
                            difficulty = difficulty_name_from_value(depth_limit)
                            draw_status("AI thinking...",difficulty)
                            pygame.display.update()

                            if problem.goal_test(current_state):
                                game_over = True
                                show_end_screen = True
                                winning_line = current_state.get_winning_line("X") or current_state.get_winning_line("O")
                                draw_highlight(winning_line, screen, current_state)
                                draw_status(f"Player {current_state.current_player} wins!")
                                pygame.display.update()
                                continue

                            ai_thinking = True
                            ai_thread = threading.Thread(target=ai_think, args=(current_state,))
                            ai_thread.start()

        if ai_move and not game_over and not ai_thinking:
            animate_drawing(ai_move[0], ai_move[1], "O", current_state, winning_line)
            current_state = current_state.result(ai_move)
            history.append(current_state)
            ai_move = None
            background_image = pygame.image.load("Png/background.png").convert()
            background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

            screen.blit(background_image, (0, 0))
            draw_lines()
            draw_figures(current_state)
            if problem.goal_test(current_state):
                game_over = True
                show_end_screen = True
                winning_line = current_state.get_winning_line("X") or current_state.get_winning_line("O")
                draw_highlight(winning_line, screen, current_state)
                draw_status(f"Player {current_state.current_player} wins!")
            else:
                difficulty = difficulty_name_from_value(depth_limit)
                draw_status("Your turn (X)", difficulty)

            pygame.display.update()

        # If finished, draw an overlay of the end screen
        if show_end_screen:
            winner = "X" if current_state.get_winning_line("X") else "O"
            again_rect, home_rect = draw_end_screen(f"Player {winner} wins!", mouse_pos)

        pygame.display.update()
        clock.tick(60)
if __name__ == "__main__":
    main()
