# data_logger.py
import csv
import os

class DataLogger:
    def __init__(self, filename="results.csv"):
        self.filename = filename
        self.file_exists = os.path.exists(self.filename)
        
        # Initialize CSV with headers if it doesn't exist
        if not self.file_exists:
            with open(self.filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Trial_ID", "Swarm_Size", "Shape", "Success", "Completion_Time", "Error"])
                
    def log_trial(self, trial_id, swarm_size, shape_type, success, completion_time, error=False):
        """Logs the results of a single trial."""
        with open(self.filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([trial_id, swarm_size, shape_type, success, completion_time, error])
