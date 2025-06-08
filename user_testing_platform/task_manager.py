import pygame
import random
import os

class TaskManager:

    def __init__(self, width, height, rows=5, cols=10):
        self.width = width
        self.height = height
        self.rows = rows
        self.cols = cols
        self.cell_width = width // cols
        self.cell_height = height // rows
        self.targets = [
            (r, c) for r in range(1, rows - 1) for c in range(3, cols - 4)
        ]
        random.shuffle(self.targets)
        print(f"[Chase order]: {self.targets}")
        self.index = 0

        # images for memeory game
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PROJECT_ROOT = os.path.dirname(BASE_DIR)

        self.images = [pygame.transform.scale(pygame.image.load(os.path.join(PROJECT_ROOT ,"assets", "better_waves", f"Crop-Ocean-{i}.png")),
                                (self.cell_width, self.cell_height))
            for i in range(0, 9)]
        print(f"len of images: {len(self.images)}")
        self.images_pos_index = dict()
        
        # target queue for memory game
        self.image_target_queue = list(range(len(self.images))) 
        random.shuffle(self.image_target_queue) 
        print(f"image_target_queue: {self.image_target_queue}")
        self.grid_pos_memory_game = []
        self.shuffle_grid_pos_memory_game()
    
    def current_target(self,game_mode):
        
        if game_mode == "chase":
            return self.targets[self.index % len(self.targets)] 
        
        elif game_mode == "memory":
            current_target_idnex = self.image_target_queue[0]
            for pos, index in self.images_pos_index.items():
                
                if index == current_target_idnex:
                    return pos
        return None

    def next_task(self):
        self.index += 1

    def draw(self, screen, font,game_mode, highlight):
        if game_mode == "chase":
            for r in range(1, 4):  # Center rows (1 to 3)
                for c in range(3, 6):  # Center columns (3 to 5)
                    rect = pygame.Rect(c * self.cell_width, r * self.cell_height,
                                    self.cell_width, self.cell_height)

                    pygame.draw.rect(screen, (100, 100, 100), rect, 1)

                    # Highlight target
                    if (r, c) == self.current_target(game_mode):
                        pygame.draw.rect(screen, (0, 255, 0), rect, 3)

                    elif highlight and (r, c) == highlight:
                        pygame.draw.rect(screen, (255, 0, 0), rect, 3)

        elif game_mode == "memory":
            grid_start_x = (self.width - self.cols * self.cell_width) // 2
            grid_start_y = (self.height - self.rows * self.cell_height) // 2

            # Assign images to randomized positions
            for idx, (r, c) in enumerate(self.grid_pos_memory_game):
                rect = pygame.Rect(
                    grid_start_x + c * self.cell_width,
                    grid_start_y + r * self.cell_height,
                    self.cell_width,
                    self.cell_height
                )
                if idx < len(self.images):
                    self.images_pos_index[(r, c)] = idx
                    screen.blit(self.images[idx], rect.topleft)
                else:
                    pygame.draw.rect(screen, (0, 0, 0), rect)  # Black fill for other cells
                    pygame.draw.rect(screen, (100, 100, 100), rect, 1)

            self.show_to_match(screen)
                

    def show_to_match(self, screen):
        index = self.image_target_queue[0]
        rect = pygame.Rect(7 * self.cell_width, 2 * self.cell_height, self.cell_width, self.cell_height)
        screen.blit(self.images[index], rect.topleft)

    def check_match(self, random_index, confirmed_cell):
        # Check if the confirmed cell matches the random index
        target_index = self.image_target_queue[0]
        if self.images_pos_index.get(confirmed_cell) == target_index:
            self.image_target_queue.append(self.image_target_queue.pop(0))
            print(f"image_target_queue updated: {self.image_target_queue}")
            print(f"[match] confirmed_cell: {confirmed_cell}, target_index: {target_index}")
            self.reset_memory_game()
            return True
        else:
            self.image_target_queue.append(self.image_target_queue.pop(0))
            print(f"image_target_queue updated: {self.image_target_queue}")
            print(f"[not match] confirmed_cell: {confirmed_cell}, target_index: {target_index}")
            self.reset_memory_game()
            return False
   
    def reset_memory_game(self):
        self.images_pos_index.clear()
        self.shuffle_grid_pos_memory_game()

    def shuffle_grid_pos_memory_game(self):
        self.grid_pos_memory_game = [(r, c) for r in range(1, 4) for c in range(3, 6)]
        random.shuffle(self.grid_pos_memory_game)
        
