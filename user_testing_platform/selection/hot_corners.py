import time
import pygame

class HotCornerSelector:
    def __init__(self, width, height, radius=150, trigger_radius=200, trigger_delay=0.2, timeout=1.5):
        self.WIDTH = width
        self.HEIGHT = height
        self.radius = radius
        self.trigger_radius = trigger_radius
        self.trigger_delay = trigger_delay
        self.timeout = timeout
        self.last_gaze_time = 0
        self.trigger_delay = 0.3

        self.hot_corners = {

            "top_right": {
                "pos": (self.WIDTH * 0.75, self.HEIGHT * 0.2),
                "label": "Select",
                "color": (255, 255, 0),
                "action": "select"
            }
        }

        self.last_candidate_time = None
        self.last_candidate_cell = None

    def update(self, gaze_pos, current_cell, candidate_cell):
        now = time.time()

        # Step 1: Record a candidate
        if candidate_cell and candidate_cell != self.last_candidate_cell:
            self.last_candidate_cell = candidate_cell
            self.last_candidate_time = now

        # Step 2: Confirm if within hot corner and within time window
        if self.last_candidate_time and (now - self.last_candidate_time <= self.timeout):
            for corner in self.hot_corners.values():
                cx, cy = corner["pos"]
                dx = gaze_pos[0] - cx
                dy = gaze_pos[1] - cy
                dist = (dx ** 2 + dy ** 2) ** 0.5

                if dist < self.trigger_radius and corner["action"] == "select":
                    self.last_candidate_cell = None
                    self.last_candidate_time = None
                    return True, candidate_cell  # Confirm the selection

        return False, None  # No trigger yet

    def draw(self, screen, font, gaze_pos=None):
        for corner in self.hot_corners.values():
            x, y = corner["pos"]

            # Ring if gaze near
            if gaze_pos:
                dx, dy = gaze_pos[0] - x, gaze_pos[1] - y
                if (dx**2 + dy**2)**0.5 < self.trigger_radius:
                    pygame.draw.circle(screen, (0, 255, 255), (int(x), int(y)), self.trigger_radius, 3)

            pygame.draw.circle(screen, corner["color"], (int(x), int(y)), self.radius)
            label_surface = font.render(corner["label"], True, (0, 0, 0))
            rect = label_surface.get_rect(center=(int(x), int(y)))
            screen.blit(label_surface, rect)
    
    def check_gaze_trigger(self, gaze_pos):
        now = time.time()
        if now - self.last_gaze_time < self.trigger_delay:
            return None
        self.last_gaze_time = now

        for key, corner in self.hot_corners.items():
            cx, cy = corner["pos"]
            dx = gaze_pos[0] - cx
            dy = gaze_pos[1] - cy
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance < self.trigger_radius:  # Slightly larger trigger radius
                return corner["action"]
        return None

    def process_selection(self, gaze_pos, current_cell, candidate_cell, confirmed_cell):
        """
        Handles selection and cancellation logic internally.
        Returns updated confirmed_cell and action (e.g., "cancel" or None).
        """
        now = time.time()

        # Handle selection
        if candidate_cell and confirmed_cell is None:
            if candidate_cell: #!= self.last_candidate_cell: her er det jeg ændrede
                self.last_candidate_cell = candidate_cell
                self.last_candidate_time = now

            if self.last_candidate_time and (now - self.last_candidate_time <= self.timeout):
                for corner in self.hot_corners.values():
                    cx, cy = corner["pos"]
                    dx = gaze_pos[0] - cx
                    dy = gaze_pos[1] - cy
                    dist = (dx**2 + dy**2)**0.5
                    if dist < self.trigger_radius and corner["action"] == "select":
                        self.last_candidate_cell = None
                        self.last_candidate_time = None
                        return candidate_cell, "selected"
        
        # Handle cancel
        if now - self.last_gaze_time >= self.trigger_delay:
            self.last_gaze_time = now
            for corner in self.hot_corners.values():
                if corner["action"] == "cancel":
                    cx, cy = corner["pos"]
                    dx = gaze_pos[0] - cx
                    dy = gaze_pos[1] - cy
                    dist = (dx**2 + dy**2)**0.5
                    if dist < self.trigger_radius:
                        return None, "cancel"

        return confirmed_cell, None
