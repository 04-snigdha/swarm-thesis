# data_logger.py  (lives in followup_experiment/)
#
# Variant of the main data_logger.py for the follow-up experiment (B+C sweep).
# Adds a Shuffle_Duration column (stored as seconds, not frames).
#
# Columns: Trial_ID, Shape_Type, Swarm_Size, Shuffle_Randomness, Shuffle_Duration,
#          Success, Completion_Time, Peak_Attached, Num_Jams, Total_Shuffles,
#          Time_To_First_Attachment, Final_Payload_Distance, Error
import csv
import os


class DataLoggerFollowup:
    """
    Writes one CSV per shape into a timestamped results folder.

    Folder layout:
        results/<run_id>/
            L-shape.csv
            C-shape.csv

    Columns: Trial_ID, Shape_Type, Swarm_Size, Shuffle_Randomness, Shuffle_Duration,
             Success, Completion_Time, Peak_Attached, Num_Jams, Total_Shuffles,
             Time_To_First_Attachment, Final_Payload_Distance, Error

    Shuffle_Duration is stored as seconds (duration_frames / 60), not raw frames,
    so the CSV is directly readable without a lookup table.
    Shape_Type is included explicitly so both CSVs can be concatenated.
    """

    HEADERS = [
        "Trial_ID",
        "Shape_Type",
        "Swarm_Size",
        "Shuffle_Randomness",
        "Shuffle_Duration",            # seconds, e.g. 1.0 / 2.0 / 4.0 / 8.0
        "Success",
        "Completion_Time",
        "Peak_Attached",
        "Num_Jams",                    # how many times jam detection triggered
        "Total_Shuffles",              # total agent-shuffles across all jams
        "Time_To_First_Attachment",    # seconds until first agent attached (None if never)
        "Final_Payload_Distance",      # 0–1, fraction of total distance traveled toward goal
        "Error",
    ]

    def __init__(self, run_folder: str):
        """
        Parameters
        ----------
        run_folder : str
            Path to the timestamped folder for this experiment run.
            Created automatically if it does not exist.
        """
        self.run_folder = run_folder
        os.makedirs(run_folder, exist_ok=True)
        self._initialised_shapes: set = set()

    def _path(self, shape: str) -> str:
        return os.path.join(self.run_folder, f"{shape}.csv")

    def _ensure_header(self, shape: str):
        path = self._path(shape)
        if shape not in self._initialised_shapes:
            if not os.path.exists(path):
                with open(path, mode='w', newline='') as f:
                    csv.writer(f).writerow(self.HEADERS)
            self._initialised_shapes.add(shape)

    def log_trial(self, trial_id, swarm_size, shape_type, shuffle_randomness,
                  shuffle_duration_frames, success, completion_time,
                  peak_attached=0, num_jams=0, total_shuffles=0,
                  time_to_first_attachment=None, final_payload_distance=0.0,
                  error=False):
        """
        Parameters
        ----------
        trial_id                  : int
        swarm_size                : int
        shape_type                : str   e.g. "L-shape" or "C-shape"
        shuffle_randomness        : float 0.0–1.0
        shuffle_duration_frames   : int   raw frame count (60 / 120 / 240 / 480)
        success                   : bool
        completion_time           : float seconds
        peak_attached             : int   peak simultaneous attached agents
        num_jams                  : int   times jam detection triggered
        total_shuffles            : int   total agent-shuffles summed across all jams
        time_to_first_attachment  : float|None  seconds until first attachment
        final_payload_distance    : float 0–1 fraction of distance traveled toward goal
        error                     : bool  True if the trial crashed
        """
        self._ensure_header(shape_type)
        shuffle_duration_secs = shuffle_duration_frames / 60.0
        with open(self._path(shape_type), mode='a', newline='') as f:
            csv.writer(f).writerow([
                trial_id,
                shape_type,
                swarm_size,
                shuffle_randomness,
                shuffle_duration_secs,
                success,
                completion_time,
                peak_attached,
                num_jams,
                total_shuffles,
                time_to_first_attachment,
                final_payload_distance,
                error,
            ])
