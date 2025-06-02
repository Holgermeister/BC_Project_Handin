import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF

class GazeGPRFilter:
    def __init__(self):
        kernel = 1.0 * RBF(length_scale=10.0)  # Radial Basis Function Kernel
        self.gpr_x = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5)
        self.gpr_y = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5)

        self.time_window = []
        self.gaze_x_history = []
        self.gaze_y_history = []

    def update(self, gaze_x, gaze_y, timestamp):
        # Store data
        self.time_window.append(timestamp)
        self.gaze_x_history.append(gaze_x)
        self.gaze_y_history.append(gaze_y)

        # Keep only recent 10 points
        if len(self.time_window) > 10:
            self.time_window.pop(0)
            self.gaze_x_history.pop(0)
            self.gaze_y_history.pop(0)

        # Train model when enough data points exist
        if len(self.time_window) >= 5:
            time_np = np.array(self.time_window).reshape(-1, 1)
            gaze_x_np = np.array(self.gaze_x_history).reshape(-1, 1)
            gaze_y_np = np.array(self.gaze_y_history).reshape(-1, 1)

            self.gpr_x.fit(time_np, gaze_x_np)
            self.gpr_y.fit(time_np, gaze_y_np)

            # Predict future gaze position (0.1 sec ahead)
            future_time = np.array([[self.time_window[-1] + 0.1]])
            pred_x = self.gpr_x.predict(future_time)[0]
            pred_y = self.gpr_y.predict(future_time)[0]

            return (pred_x, pred_y)

        return (gaze_x, gaze_y)  # Return current position if no prediction is available
