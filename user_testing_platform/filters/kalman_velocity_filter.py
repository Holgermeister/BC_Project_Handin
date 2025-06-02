import numpy as np
import cv2

class GazeKalmanFilterVelocity:
    def __init__(self):
        self.kf = cv2.KalmanFilter(4, 2)  # State: [x, y, vx, vy]
        self.kf.measurementMatrix = np.array([[1, 0, 0, 0],
                                              [0, 1, 0, 0]], np.float32)
        self.kf.transitionMatrix = np.array([[1, 0, 1, 0],
                                             [0, 1, 0, 1],
                                             [0, 0, 1, 0],
                                             [0, 0, 0, 1]], np.float32)
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * 0.03

    def update(self, gaze_x, gaze_y):
        measurement = np.array([[np.float32(gaze_x)], [np.float32(gaze_y)]])
        self.kf.correct(measurement)
        prediction = self.kf.predict()
        return prediction[0][0], prediction[1][0]
