
import os
import sys
import time
import pygame
import numpy as np

from config import WIDTH, HEIGHT, BG_COLOR, METHODS, GAME_MODES, NUMBER_OF_SELECTIONS_PR_METHOD, NUMBER_OF_METHODS_PR_TASK
from task_manager import TaskManager
from logger import Logger
from gaze_listener import start_gaze_listener, get_latest_gaze, get_latest_blink, get_latest_pupil
from selection.hot_corners import HotCornerSelector
from selection.blink_selection import BlinkSelection
from selection.head_turn_selection import Head_Turn_Selector
from filters.one_euro_filter import GazeOneEuroFilter

pygame.init()
# === Get participant ID from command line ===
if len(sys.argv) < 2:
    print("Usage: python3 main.py <participant_id>")
    sys.exit(1)
participant = sys.argv[1] if len(sys.argv) > 1 else "anonymous"
logger = Logger(participant_name=participant)
start_script = None if len(sys.argv) < 3 else sys.argv[2]


# === Init Pygame ===
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Gaze Selection Method Evaluation")
font = pygame.font.SysFont("Arial", 24)
big_font = pygame.font.SysFont("Arial", 48)
clock = pygame.time.Clock()

# === Load AprilTags ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

apriltag_size = int(min(WIDTH, HEIGHT) * 0.2)
apriltags = [
    pygame.transform.scale(pygame.image.load(os.path.join(PROJECT_ROOT ,"assets", f"tag_{i}.jpg")),
                           (apriltag_size, apriltag_size))
    for i in range(1, 5)
]

# === Init Modules ===
one_euro_filter = GazeOneEuroFilter()

# check her efter merge
hotcorner_selector = HotCornerSelector(WIDTH, HEIGHT)
blink_selector = BlinkSelection(blink_duration_selection='long')
head_turn_selector = Head_Turn_Selector()


# === App State ===
selection_method = METHODS[0]
method_index = 0
game_mode = GAME_MODES[0]
game_mode_index = 0
candidate_cell = None
confirmed_cell = None
last_candidate = None
dwell_start = None
selection_time = None
dwell_time = 0.2

# === Task State ===
timer_started = None
highlight_start_time = None
selection_counter = 0
f_h_t_s = None
higligted_cell = None
time_for_new_task = 0
acc_gaze_movement = 0
prev_gaze_pos = None
dist_to_target = None
dwell_off_start = None

# blink stuff
waiting_for_blink_offset = False
blink_initial_ts = None

# === Init Task Manager with game mode ===
task_manager = TaskManager(WIDTH, HEIGHT, rows=5, cols=10)


# === Start Gaze Listener ===
start_gaze_listener(start_script)

# === Main Loop ===
running = True
while running:
    screen.fill(BG_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                method_index = (method_index + 1) % len(METHODS)
                selection_method = METHODS[method_index]
                
            elif event.key == pygame.K_n:
                game_mode_index = (game_mode_index + 1) % len(GAME_MODES)
                game_mode = GAME_MODES[game_mode_index]
            elif event.key == pygame.K_SPACE:
                logger.change_log()
                logger.save()
               

    # === Gaze Processing ===
    gaze = get_latest_gaze()
    blink = get_latest_blink()
    pupil = get_latest_pupil()


    if gaze: 
        (gx_norm, gy_norm), timestamp = gaze
        raw_x = int(gx_norm * WIDTH)
        raw_y = int((1 - gy_norm) * HEIGHT)
        smooth = one_euro_filter.update(raw_x, raw_y, timestamp)
        gx, gy = smooth
        
        row = int(gy // task_manager.cell_height)
        col = int(gx // task_manager.cell_width)
        current_cell = (row, col)
        in_bounds = (
            1 <= row < task_manager.rows - 1 and 
            3 <= col < task_manager.cols - 4
        )
        # check if gaze is in bounds so nothing is highlighted when out of bounds
        if selection_method != "head_turn":
            if not in_bounds:
                if dwell_off_start is None:
                    dwell_off_start = time.time()
                elif time.time() - dwell_off_start >= dwell_time:
                    candidate_cell = None
                    higligted_cell = None
                    dwell_start = None
            else:
                dwell_off_start = None

        if prev_gaze_pos is not None:
            gaze_movement = np.linalg.norm(np.array((gx, gy)) - np.array(prev_gaze_pos))
            acc_gaze_movement += gaze_movement

        prev_gaze_pos = (gx, gy)
        if selection_method == "head_turn":
            dwell_time = 0.4
        else:
            dwell_time = 0.2

        if confirmed_cell is None and in_bounds:
            if current_cell == last_candidate:
                if dwell_start is None:
                    dwell_start = time.time()
                elif time.time() - dwell_start >= dwell_time:
                    if candidate_cell != current_cell:
                        candidate_cell = current_cell
            else:
                dwell_start = time.time()
                last_candidate = current_cell
        elif confirmed_cell:
            candidate_cell = None

        if selection_method == "hotcorner":
            new_confirmed, action = hotcorner_selector.process_selection((gx, gy), current_cell, candidate_cell, confirmed_cell)

            if action == "selected":
                confirmed_cell = new_confirmed
                selection_time = time.time()
                print(f"[HotCorner] Confirmed {confirmed_cell}")
                candidate_cell = None


        elif selection_method == "blink":
            
            if blink:
                triggered = blink_selector.blink_detection_update(blink)
                
                if triggered == (False, None):
                    initial_ts = blink.get("timestamp")
                    new_blink = None
                    
                    while True:
                        new_blink = get_latest_blink()
                        if new_blink.get("timestamp") != initial_ts and new_blink.get("type") == "offset":
                            break

                    if new_blink.get("type") == "offset":
                        blink_final_res = blink_selector.blink_detection_update(new_blink)

                        if blink_final_res == True and confirmed_cell is None:
                            confirmed_cell = candidate_cell
                            selection_time = time.time()
                            
                            print(f"[Blink] Confirmed {confirmed_cell}")
                            candidate_cell = None  # reset candidate cell

        elif selection_method == "head_turn":
            action = head_turn_selector.update(pupil['norm_pos'], candidate_cell)
            if action is not None:
                confirmed_cell = action
                selection_time = time.time()
                
                print(f"[Head Turn] Confirmed {confirmed_cell}")

        # === Drawing ===
        task_manager.draw(screen, font, highlight=confirmed_cell,game_mode=GAME_MODES[game_mode_index])

        if timer_started is None:
            timer_started = time.time()

        if candidate_cell and not confirmed_cell:
            crow, ccol = candidate_cell
            # Make the red highlight fit within the cell by adding a margin
            margin = 6  # Adjust margin as needed
            rect = pygame.Rect(
                ccol * task_manager.cell_width + margin,
                crow * task_manager.cell_height + margin,
                task_manager.cell_width - 2 * margin,
                task_manager.cell_height - 2 * margin
            )
            if game_mode == "chase":
                pygame.draw.rect(screen, (255, 0, 0), rect, 3)
            else: 
                rect = pygame.Rect(
                    ccol * task_manager.cell_width,
                    crow * task_manager.cell_height,
                    task_manager.cell_width,
                    task_manager.cell_height
                )
                pygame.draw.rect(screen, (255, 0, 0), rect, 5)
            
            # highlight timer started
            if candidate_cell != higligted_cell or highlight_start_time is None:
                highlight_start_time = time.time()
                higligted_cell = candidate_cell
                logger.log_event("highlighted_cell", 
                         None, 
                         (task_manager.current_target(game_mode,)),
                         higligted_cell,
                         None,
                         None, 
                         acc_gaze_movement, 
                         selection_method,
                         game_mode)
                logger.save()

        if confirmed_cell:
            srow, scol = confirmed_cell
            color = (255, 255, 0)

            rect = pygame.Rect(
                scol * task_manager.cell_width,
                srow * task_manager.cell_height,
                task_manager.cell_width,
                task_manager.cell_height
            )
            pygame.draw.rect(screen, color, rect, 5)

        # draw UI for hotcorners when in use 
        if selection_method == "hotcorner":
            hotcorner_selector.draw(screen, font, gaze_pos=(gx, gy))

    # === Draw AprilTags ===
    screen.blit(apriltags[0], (0, 0))
    screen.blit(apriltags[1], (WIDTH - apriltag_size, 0))
    screen.blit(apriltags[2], (0, HEIGHT - apriltag_size))
    screen.blit(apriltags[3], (WIDTH - apriltag_size, HEIGHT - apriltag_size))

    screen.blit(font.render(f"Selection_counter: {selection_counter}", True, (255, 255, 255)), (10, 300))

    screen.blit(font.render(f"Method: {selection_method}", True, (255, 255, 255)), (10, 350))

    screen.blit(font.render(f"Game Mode: {game_mode}", True, (255, 255, 255)), (10, 400))
    screen.blit(font.render(f"Participant: {participant}", True, (255, 255, 255)), (10, 450))
    screen.blit(font.render(f"higligted time: {highlight_start_time}, highligted cell {higligted_cell}", True, (255, 255, 255)), (10, 500))

    
    if game_mode == "memory":
        screen.blit(font.render(f"Find this image among the other images!", True, (255, 0, 0)), (1770,860))


    pygame.display.flip()
    clock.tick(60)

    # === keyboard shortcuts ===
    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        running = False

    # == auto state control ==
    
    if confirmed_cell:
        if highlight_start_time is not None and higligted_cell == confirmed_cell:
            elapsed_time = time.time() - highlight_start_time
            f_h_t_s = elapsed_time
            highlight_start_time = None

        selection_counter += 1
        task_time = time.time() - timer_started
        logger.log_event("TaskCompleted", 
                         confirmed_cell, 
                         (task_manager.current_target(game_mode,)), 
                         higligted_cell,
                         task_time,f_h_t_s, 
                         acc_gaze_movement, 
                         selection_method,
                         game_mode)
        logger.save()

        target_center = task_manager.current_target(game_mode)
        target_center_px = (
            target_center[0] * task_manager.cell_width + task_manager.cell_width / 2,
            target_center[1] * task_manager.cell_height + task_manager.cell_height / 2
        )
        
        if confirmed_cell == target_center:
            logger.log_fitts(dist_to_target, task_time, selection_method, game_mode)
        
        dist_to_target = np.linalg.norm(np.array((gx, gy)) - np.array(target_center_px))
        task_manager.check_match(confirmed_cell)
        
        time.sleep(1)
        task_manager.next_task()
        timer_started = time.time()
        # fitts law distance from target center to gaze position

        confirmed_cell = None
        candidate_cell = None
        last_candidate = None
        higligted_cell = None
    
        
    
    if selection_counter == NUMBER_OF_SELECTIONS_PR_METHOD:
        time_for_new_task += 1
        acc_gaze_movement = 0
        # Transition screen loop
        while True:
            screen.fill(BG_COLOR)
            
            # Display transition text
            text = big_font.render(f"Next method: {METHODS[(method_index + 1) % len(METHODS)]}", True, (255, 255, 255))
            subtext = font.render("Press RIGHT ARROW to continue...", True, (200, 200, 200))
            screen.blit(text, ((WIDTH - text.get_width()) // 2, HEIGHT // 2 - 50))
            screen.blit(subtext, ((WIDTH - subtext.get_width()) // 2, HEIGHT // 2 + 10))
            
            if time_for_new_task == NUMBER_OF_METHODS_PR_TASK:
                text = big_font.render(f"End of task, beginning new task", True, (255, 255, 255))
                subtext = font.render(f"next gamemode: {GAME_MODES[(game_mode_index + 1) % len(GAME_MODES)]}", True, (200, 200, 200))
                screen.blit(text, ((WIDTH - text.get_width()) // 2, HEIGHT // 2 - 100))
                screen.blit(subtext, ((WIDTH - subtext.get_width()) // 2, HEIGHT // 2 + 30))
            pygame.display.flip()
            clock.tick(60)

            # Check for events to break the loop
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT:
                    selection_counter = 0
                    method_index = (method_index + 1) % len(METHODS)
                    selection_method = METHODS[method_index]
                    if time_for_new_task == NUMBER_OF_METHODS_PR_TASK:
                        time_for_new_task = 0
                        game_mode_index = (game_mode_index + 1) % len(GAME_MODES)
                        game_mode = GAME_MODES[game_mode_index]
                    break
            else:
                continue
            break
        timer_started = time.time()
pygame.quit()
