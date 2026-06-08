# experiment_runner.py
import config
import os
import random
from datetime import datetime
from simulation_manager import SimulationManager
from data_logger import DataLogger

# ---------------------------------------------------------------------------
# Experiment version history
# ---------------------------------------------------------------------------
# v1: high agent power   (speed=50, push_mult=10, payload_mass=10,  damping=0.8)
# v2: calibrated power   (speed=25, push_mult=4,  payload_mass=30,  damping=0.6)
# v3: realistic physics  (speed=25, push_mult=2,  payload_mass=150, joint_force=1500, levy_walk)
# v4: full 3-IV sweep    (v3 physics + SHUFFLE_RANDOMNESS_LEVELS, per-shape CSV output)
# ---------------------------------------------------------------------------

def run_batch_experiment(trials_per_condition: int = 50):
    """
    Sweeps all three independent variables:
        - Swarm size         : config.SWARM_SIZES       (e.g. [5, 10, 20, 40])
        - Shape type         : config.TARGET_SHAPES     (Circle, Square, L-shape, C-shape)
        - Shuffle randomness : config.SHUFFLE_RANDOMNESS_LEVELS (e.g. [0.0, 0.25, 0.5, 0.75, 1.0])

    Results are written to:
        results/<run_id>/
            Circle.csv
            Square.csv
            L-shape.csv
            C-shape.csv

    Each CSV row: Trial_ID, Swarm_Size, Shuffle_Randomness, Success, Completion_Time, Error
    """

    # --- Create timestamped run folder ---
    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_folder = os.path.join("results", run_id)
    logger = DataLogger(run_folder)

    # --- Build condition list ---
    conditions = [
        (size, shape, sr)
        for shape in config.TARGET_SHAPES
        for size  in config.SWARM_SIZES
        for sr    in config.SHUFFLE_RANDOMNESS_LEVELS
    ]
    total_trials = len(conditions) * trials_per_condition

    print(f"=== Batch Experiment v4 ===")
    print(f"Conditions : {len(conditions)}  ({len(config.TARGET_SHAPES)} shapes × "
          f"{len(config.SWARM_SIZES)} sizes × {len(config.SHUFFLE_RANDOMNESS_LEVELS)} shuffle levels)")
    print(f"Trials/cond: {trials_per_condition}")
    print(f"Total      : {total_trials}")
    print(f"Output     : {run_folder}/")
    print()

    manager = SimulationManager(logger=logger)
    trial_count = 1

    for size, shape, sr in conditions:
        successes = 0
        for rep in range(trials_per_condition):
            random.seed(trial_count)

            print(
                f"[{trial_count:>5}/{total_trials}]  shape={shape:<8}  "
                f"size={size:>2}  shuffle={sr:.2f}  rep={rep+1}/{trials_per_condition}",
                end="\r"
            )

            try:
                result = manager.run_trial(
                    swarm_size=size,
                    shape_type=shape,
                    shuffle_randomness=sr,
                    trial_id=trial_count,
                    quiet=True,
                )
                if result:
                    successes += 1
            except Exception as e:
                print(f"\n[ERROR] Trial {trial_count} crashed: {e}")
                logger.log_trial(trial_count, size, shape, sr, False,
                                 config.SIMULATION_TIME_LIMIT, error=True)

            trial_count += 1

        success_rate = successes / trials_per_condition
        print(f"\n  -> {shape:<8} size={size:>2}  shuffle={sr:.2f}  "
              f"success_rate={success_rate:.0%}  ({successes}/{trials_per_condition})")

    print(f"\n=== Complete. Results in: {run_folder}/ ===")


if __name__ == "__main__":
    # trials_per_condition=50 gives 4000 total trials (4 shapes × 4 sizes × 5 levels × 50)
    run_batch_experiment(trials_per_condition=50)
