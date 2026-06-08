# experiment_runner.py
import config
from simulation_manager import SimulationManager
from data_logger import DataLogger
import random

def run_batch_experiment(total_trials=4000, output_file="results.csv"):
    manager = SimulationManager()

    combinations = [(size, shape) for size in config.SWARM_SIZES for shape in config.TARGET_SHAPES]
    trials_per_combo = (total_trials // len(combinations)) + 1

    trial_count = 1

    print(f"--- Starting Thesis Batch Simulation ({total_trials} Trials) ---")
    print(f"--- Output: {output_file} ---")

    for _ in range(trials_per_combo):
        for size, shape in combinations:
            if trial_count > total_trials:
                break

            random.seed(trial_count)

            print(f"Trial {trial_count}/{total_trials} running... | Shape: {shape} | Size: {size}", end="\r")

            try:
                manager.logger.filename = output_file
                manager.run_trial(size, shape, trial_id=trial_count, quiet=True)

            except Exception as e:
                print(f"\n[ERROR] Trial {trial_count} crashed: {e}. Logging failure and continuing.")
                manager.logger.log_trial(trial_count, size, shape, False, config.SIMULATION_TIME_LIMIT, error=True)

            trial_count += 1

    print(f"\n--- Batch Completion: All {total_trials} trials finished! ---")

if __name__ == "__main__":
    # v1: high agent power   (speed=50, push_mult=10, payload_mass=10,  damping=0.8)
    # v2: calibrated power  (speed=25, push_mult=4,  payload_mass=30,  damping=0.6)
    # v3: realistic physics (speed=25, push_mult=2,  payload_mass=150, damping=0.6, joint_force=1500, levy_walk)
    run_batch_experiment(4000, output_file="results_v3_mass150_joint1500_levywalk.csv")
