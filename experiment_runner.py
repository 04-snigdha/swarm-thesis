# experiment_runner.py
import config
from simulation_manager import SimulationManager
from data_logger import DataLogger
import random

def run_batch_experiment(total_trials=4000):
    manager = SimulationManager()
    
    # We have 4 sizes and 4 shapes = 16 combinations
    # 1000 trials / 16 combinations = 62.5, we will round up to run evenly
    combinations = [(size, shape) for size in config.SWARM_SIZES for shape in config.TARGET_SHAPES]
    trials_per_combo = (total_trials // len(combinations)) + 1
    
    trial_count = 1
    
    print(f"--- Starting Thesis Batch Simulation ({total_trials} Trials) ---")
    
    for _ in range(trials_per_combo):
        for size, shape in combinations:
            if trial_count > total_trials:
                break
                
            # [Thesis Data Integrity] - Reset random seed per trial for reproducibility
            random.seed(trial_count)
            
            # Terminal Progress Indicator
            print(f"Trial {trial_count}/{total_trials} running... | Current Shape: {shape} | Current Size: {size}", end="\r")
            
            try:
                # We enforce the new "results.csv" log output inside manager
                manager.logger.filename = "results.csv"
                # Run quietly so it doesn't flood the console
                manager.run_trial(size, shape, trial_id=trial_count, quiet=True)
                
            except Exception as e:
                # Catch physics crashes (e.g. kinematic locks, body overlaps)
                print(f"\n[ERROR] Trial {trial_count} crashed: {e}. Logging failure and continuing.")
                manager.logger.log_trial(trial_count, size, shape, False, config.SIMULATION_TIME_LIMIT, error=True)
                
            trial_count += 1
            
    print(f"\n--- Batch Completion: All {total_trials} trials finished! ---")

if __name__ == "__main__":
    run_batch_experiment(1000)
