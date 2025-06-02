from OneEuroFilter import OneEuroFilter

class GazeOneEuroFilter:
    def __init__(self, freq=120, min_cutoff=1.0, beta=0.05, d_cutoff=1.0):
        """
        One Euro Filter Parameter Tuning:

        freq: Sampling frequency (Hz). Adjust based on tracker.
        min_cutoff: Lower = more smoothing, Higher = more responsive.
        beta: Higher = faster reaction, Lower = more stability.
        d_cutoff: Higher = better noise rejection, Lower = more flexibility.
        """
        self.one_euro_x = OneEuroFilter(freq, min_cutoff, beta, d_cutoff)
        self.one_euro_y = OneEuroFilter(freq, min_cutoff, beta, d_cutoff)

    def update(self, x, y, timestamp):
        """Apply One Euro filtering."""
        euro_filtered_x = self.one_euro_x(x, timestamp)
        euro_filtered_y = self.one_euro_y(y, timestamp)
        return int(euro_filtered_x), int(euro_filtered_y)
