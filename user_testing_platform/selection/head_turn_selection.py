import time
import numpy as np

class Head_Turn_Selector:
    def __init__(self, angle_threshold=30, duration=0.3, min_angle=5):
        self.prev_pos = None
        self.prev_vector = None
        self.start_time = None
        self.duration = duration
        self.angle_threshold = angle_threshold  # degrees
        self.smooth_tracking = False
        self.min_angle = min_angle  # degrees

    def _angle_between(self, v1, v2):
        """Returns angle in degrees between two vectors."""
        unit_v1 = v1 / np.linalg.norm(v1)
        unit_v2 = v2 / np.linalg.norm(v2)
        dot = np.clip(np.dot(unit_v1, unit_v2), -1.0, 1.0)
        return np.degrees(np.arccos(dot))

    def update(self, center_pos, candidate_cell):
        new_pos = np.array(center_pos, dtype=np.float32)
        current_time = time.time()

        if self.prev_pos is None:
            self.prev_pos = new_pos
            return None

        movement_vector = new_pos - self.prev_pos
        
        if np.linalg.norm(movement_vector) < 1e-6:
            # Eye barely moved
            self.prev_vector = None
            self.start_time = None
            self.smooth_tracking = False
            return None

        if self.prev_vector is not None:
            angle = self._angle_between(movement_vector, self.prev_vector)
            #print(f"Angle between vectors: {angle:.2f} degrees")
            if angle < self.angle_threshold:
                if self.start_time is None:
                    self.start_time = current_time
                    #print(f"Started directional tracking: angle {angle:.2f}")
                elif current_time - self.start_time >= self.duration:
                    if not self.smooth_tracking:
                        print(f"Smooth movement confirmed (angle {angle:.2f})")
                    self.smooth_tracking = True
            else:
                print(f"Direction changed too much: angle {angle:.2f}")
                self.start_time = None
                self.smooth_tracking = False
        else:
            self.start_time = current_time

        self.prev_pos = new_pos
        self.prev_vector = movement_vector

        # If smooth movement confirmed, return the candidate
        if self.smooth_tracking:
            return candidate_cell

        return None
