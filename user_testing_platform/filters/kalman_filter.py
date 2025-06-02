import numpy as np
from filterpy.kalman import KalmanFilter

class GazeKalmanFilter:
    def __init__(self):
        self.kf = KalmanFilter(dim_x=4, dim_z=2)  # 4 state variables (x, y, vx, vy), 2 measurements (x, y)

        # State transition matrix (models constant velocity)
        self.kf.F = np.array([[1, 0, 1, 0],  
                              [0, 1, 0, 1],  
                              [0, 0, 1, 0],  
                              [0, 0, 0, 1]])  

        # Measurement matrix (we directly observe x, y)
        self.kf.H = np.array([[1, 0, 0, 0],
                              [0, 1, 0, 0]])

        # Process noise covariance (assumes small acceleration changes)
        self.kf.Q *= np.array([[0.05, 0, 0, 0],
                                [0, 0.05, 0, 0],
                                [0, 0, 0.02, 0],
                                [0, 0, 0, 0.02]])

        # Measurement noise covariance (depends on sensor accuracy)
        self.kf.R *= np.array([[0.5, 0], [0, 0.5]])  
        self.kf.P *= 100  # Initial state covariance (uncertainty)
        self.kf.x = np.array([0, 0, 0, 0])  # Initial state (x, y, vx, vy)

    def update(self, x, y):
        """Apply Kalman filtering."""
        self.kf.predict()
        self.kf.update([x, y])
        return int(self.kf.x[0]), int(self.kf.x[1])  # Return filtered position

