# data_logger.py
import csv
import os


class DataLogger:
    """
    Writes one CSV per shape into a timestamped results folder.

    Folder layout:
        results/<run_id>/
            Circle.csv
            Square.csv
            L-shape.csv
            C-shape.csv

    Columns: Trial_ID, Swarm_Size, Shuffle_Randomness, Success, Completion_Time, Error
    """

    HEADERS = ["Trial_ID", "Swarm_Size", "Shuffle_Randomness", "Success", "Outcome", "Completion_Time", "Peak_Attached", "Error"]

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
                  success, completion_time, peak_attached=0, outcome="UNKNOWN", error=False):
        self._ensure_header(shape_type)
        with open(self._path(shape_type), mode='a', newline='') as f:
            csv.writer(f).writerow(
                [trial_id, swarm_size, shuffle_randomness, success, outcome, completion_time, peak_attached, error]
            )
