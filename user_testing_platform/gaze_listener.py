# gaze_listener.py
import zmq
import threading
from msgpack import loads
import sys

# Shared data accessible from outside
latest_gaze_data = None  
latest_blink_data = None
latest_fixation_data = None
latest_pupil_data = None

def start_gaze_listener(start_script):
    def listener():
        global latest_gaze_data, latest_blink_data, latest_fixation_data, latest_pupil_data

        context = zmq.Context()

        # Request SUB port from Pupil
        req = context.socket(zmq.REQ)
        req.connect("tcp://localhost:50020")
        req.send_string("SUB_PORT")
        sub_port = req.recv_string()

        # request for starting back bone api replica 
        if start_script == "r" or start_script == "R":
            req.send_string('R')
            _ = req.recv_string()

        # SUB socket for gaze surface
        sub_surface = context.socket(zmq.SUB)
        sub_surface.connect(f"tcp://localhost:{sub_port}")
        sub_surface.setsockopt_string(zmq.SUBSCRIBE, "surface")

        # SUB socket for blinks
        sub_blink = context.socket(zmq.SUB)
        sub_blink.connect(f"tcp://localhost:{sub_port}")
        sub_blink.setsockopt_string(zmq.SUBSCRIBE, "blinks")

        #sub on pupil data
        sub_pupil = context.socket(zmq.SUB)
        sub_pupil.connect(f"tcp://localhost:{sub_port}")
        sub_pupil.setsockopt_string(zmq.SUBSCRIBE, "pupil.0.2d")

        surface_name = "monitor_overlay"

        print("[gaze_listener] Listening for gaze, blink, and fixation data...")

        while True:
            try:
                # Receive gaze surface data (non-blocking style)
                try:
                    topic = sub_surface.recv_string(zmq.NOBLOCK)
                    msg = sub_surface.recv(zmq.NOBLOCK)
                    surfaces = loads(msg)

                    if surfaces.get("name") == surface_name:
                        gaze_positions = surfaces.get("gaze_on_surfaces", [])
                        if gaze_positions:
                            latest = gaze_positions[-1]
                            if latest.get("confidence", 0) > 0.89:
                                norm_x, norm_y = latest["norm_pos"]
                                timestamp = latest["timestamp"]
                                latest_gaze_data = ((norm_x, norm_y), timestamp)

                        fixations = surfaces.get("fixations_on_surfaces", [])
                        if fixations:
                            latest_fixation_data = fixations
                except zmq.Again:
                    pass  # No gaze data right now

                # Receive blink data
                try:
                    topic_blink = sub_blink.recv_string(zmq.NOBLOCK)
                    msg_blink = sub_blink.recv(zmq.NOBLOCK)
                    latest_blink_data = loads(msg_blink)
                except zmq.Again:
                    pass  # No blink data right now
                
                try:
                    topic_pupil = sub_pupil.recv_string(zmq.NOBLOCK)
                    msg_pupil = sub_pupil.recv(zmq.NOBLOCK)
                    latest_pupil_data = loads(msg_pupil)
                except zmq.Again:
                    pass

            except Exception as e:
                print("[gaze_listener] Error:", e)

    thread = threading.Thread(target=listener, daemon=True)
    thread.start()


# === Interface ===
def get_latest_gaze():
    return latest_gaze_data

def get_latest_blink():
    return latest_blink_data

def get_latest_fixation():
    return latest_fixation_data

def get_latest_pupil():
    return latest_pupil_data
