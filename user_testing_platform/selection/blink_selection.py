import zmq
import threading
import msgpack as serializer
import numpy as np
import time 

class BlinkSelection:
    ''''
    Blink detection class for eye-tracking system.
    This class detects blinks and determines if the blink duration is long or short.
    Blink_duration_selection can be set to either long or short. depending on the duration of blink you want to select. Default is long.
    
    Blkink detection is based on the time between blink onset and offset events.
    '''
    def __init__(self, long_blink_threshold=0.4, 
                       short_blink_threshold=0.2,
                       blink_duration_selection = "long"):
        # blink shit
        self.long_blink_threshold = long_blink_threshold
        self.short_blink_threshold = short_blink_threshold
        self.start_time = None
        self.end_time = None
        self.blink_in_progress = False

        
        # blink duration selection either long or short else default to long 
        if blink_duration_selection == "long":
            self.blink_duration_selection = "long"
        elif blink_duration_selection == "short":
            self.blink_duration_selection = "short"
        else:
            print("Invalid blink duration selection. Defaulting to long blink duration.")
            self.blink_duration_selection = False

    def blink_detection_update(self, blink_data):
        if blink_data is not None and blink_data['type'] == 'onset' and not self.blink_in_progress:
            self.start_time = time.time()
            self.blink_in_progress = True
            print("Blink Onset Detected")
            return False, None 
        
        elif blink_data is not None and blink_data['type'] == 'offset' and self.blink_in_progress:
            print("Blink Offset detected")
            self.end_time = time.time()
            self.blink_in_progress = False
            if self.start_time is not None and self.end_time is not None:
                blink_duration = self.end_time - self.start_time
                if blink_duration > self.long_blink_threshold and self.blink_duration_selection == "long":
                    print(f"Long Blink Duration: {blink_duration:.4f} seconds")
                    self.reset_state()
                    return True
                
                elif blink_duration < self.short_blink_threshold and self.blink_duration_selection == "short":
                    print(f"Short Blink Duration: {blink_duration:.4f} seconds")
                    self.reset_state()
                    return True
                
                #use this case for testing, to figure out a good duration for a blink blink
                else:
                    print(f"Medium Blink Duration: {blink_duration:.4f} seconds")
                    self.reset_state()
                    return False

        return False
        
    def reset_state(self):
        self.start_time = None
        self.end_time = None
        self.blink_in_progress = False