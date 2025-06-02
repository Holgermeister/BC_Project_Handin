import numpy as np

class GazeLinearExtrapolation:
    def __init__(self):
        self.prev_positions = []

    def update(self, gaze_x, gaze_y, timestamp):
        # Store last two gaze points
        self.prev_positions.append((timestamp, gaze_x, gaze_y))
        if len(self.prev_positions) > 2:
            self.prev_positions.pop(0)

        # If we have two points, extrapolate forward
        if len(self.prev_positions) == 2:
            (t1, x1, y1), (t2, x2, y2) = self.prev_positions
            dt = t2 - t1
            if dt > 0:
                vx = (x2 - x1) / dt  # Velocity in x
                vy = (y2 - y1) / dt  # Velocity in y
                predicted_x = x2 + vx * 0.1  # Predict 100ms ahead
                predicted_y = y2 + vy * 0.1
                return predicted_x, predicted_y

        return gaze_x, gaze_y  # Default return if no prediction is possible
