import os
import csv
import time
from datetime import datetime

class Logger:
    def __init__(self, participant_name="anonymous", base_dir="user_testing_platform/logs"):
        timestamp = int(time.time())
        self.start_time = time.time()
        self.participant = participant_name
        self.task_index = 0
        self.events = []
        self.fitts_events = []

        better_timestamop = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{participant_name}_{better_timestamop}.csv"
        self.filename = os.path.join(base_dir, filename)
        
        fitts_filename = f"{participant_name}_FITTS_{better_timestamop}.csv"
        self.fitts_filename = os.path.join(base_dir, f"fitts_{fitts_filename}")

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)

    def log_event(self, event_type, result,target,highlighted_cell, elapsed_task_time,f_h_t_s,gaze_movement, method,game_mode):
        now = time.time()
        entry = {
            "event_type": event_type,
            "timestamp": datetime.fromtimestamp(now),
            "participant": self.participant,
            "task_index": self.task_index,
            "index": len(self.events),
            "result": result,
            "target": target,
            "highlighted_cell": highlighted_cell,
            "correct_res": result == target,
            "elapsed_task_time": elapsed_task_time,
            "from_highlighted_to_selected": f_h_t_s,
            "gaze_movement_pr_task": gaze_movement,
            "method": method,
            "game_mode": game_mode,
            "useLess": False
        }
        if event_type == "TaskCompleted":
            self.task_index += 1
        
        if event_type == "highlighted_cell":
            entry['correct_res'] = None
        
        if event_type == "dist_to_center_target":
            entry['correct_res'] = None
        # Logs the entry
        self.events.append(entry)

    def log_fitts(self,start_dist_to_target, elapsed_task_time, method, game_mode):
        now = time.time()
        entry = {
            "timestamp": datetime.fromtimestamp(now),
            "participant": self.participant,
            "task_index": self.task_index,
            "start_dist_to_target": start_dist_to_target,
            "elapsed_task_time": elapsed_task_time,
            "method": method,
            "game_mode": game_mode,
            "useLess": False
        }
        self.fitts_events.append(entry)

    def change_log(self):
        # Find the last event with event_type == "TaskCompleted"
        for event in reversed(self.events):
            if event.get('event_type') == "TaskCompleted":
                event['useLess'] = True
                break


    def save(self):
        if not self.events:
            return

        keys = sorted(set().union(*(e.keys() for e in self.events)))
        with open(self.filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.events)

        keys2 = sorted(set().union(*(e.keys() for e in self.fitts_events)))
        with open(self.fitts_filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys2)
            writer.writeheader()
            writer.writerows(self.fitts_events)
