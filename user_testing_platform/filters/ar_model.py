import numpy as np
from statsmodels.tsa.ar_model import AutoReg

class GazeAutoRegressive:
    def __init__(self, lag=5):
        self.lag = lag
        self.x_data = []
        self.y_data = []

    def update(self, gaze_x, gaze_y):
        self.x_data.append(gaze_x)
        self.y_data.append(gaze_y)

        if len(self.x_data) > self.lag:
            self.x_data.pop(0)
            self.y_data.pop(0)

        if len(self.x_data) >= self.lag:
            model_x = AutoReg(self.x_data, lags=self.lag).fit()
            model_y = AutoReg(self.y_data, lags=self.lag).fit()
            pred_x = model_x.predict(start=len(self.x_data), end=len(self.x_data))[0]
            pred_y = model_y.predict(start=len(self.y_data), end=len(self.y_data))[0]
            return pred_x, pred_y

        return gaze_x, gaze_y  # Default return if no prediction is possible
