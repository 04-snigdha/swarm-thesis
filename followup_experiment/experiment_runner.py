# experiment_runner.py  (lives in followup_experiment/)
#
# Follow-up experiment: B+C combined sweep.
#
# Independent variables:
#   - Shape type        : L-shape, C-shape
#   - Swarm size        : 25, 30, 35
#   - Shuffle randomness: 0.0 … 1.0 in steps of 0.1  (11 levels)
#   - Shuffle duration  : 60, 120, 240, 480 frames    (1s / 2s / 4s / 8s at 60 FPS)
#
# 50 trials per condition → 2 × 3 × 11 × 4 × 50 = 13 200 total trials
#
# Time limit raised to 240 s (C-shape successes averaged 155–163 s under 180 s limit).
# Each worker process creates its own SimulationManager so there is no shared state.

import sys, os
# Allow imports from the parent swarmthesis directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import json
import random
import numpy as np
from datetime import datetime
from multiprocessing import Pool
from simulation_manager import SimulationManager
from followup_experiment.data_logger import DataLoggerFollowup

# ---------------------------------------------------------------------------
# Experiment parameters
# ---------------------------------------------------------------------------

SHAPES = ["L-shape", "C-shape"]
SWARM_SIZES = [25, 30, 35]
SHUFFLE_RANDOMNESS_LEVELS = [round(x * 0.1, 1) for x in range(11)]  # 0.0 … 1.0
SHUFFLE_DURATION_LEVELS = [60, 120, 240, 480]                        # frames
TRIALS_PER_CONDITION = 50
SIMULATION_TIME_LIMIT = 240.0   # seconds — raised from 180 s

# Number of parallel worker processes.  None → os.cpu_count().
WORKER_PROCESSES = None

# ---------------------------------------------------------------------------
# Pilot mode — run a small subset first to catch setup errors before
# committing to the full 13 200-trial run (supervisor recommendation).
# Set PILOT_MODE = False once the pilot looks clean.
# ---------------------------------------------------------------------------
PILOT_MODE = True       # True = run PILOT_REPLICATES reps per condition (~528 trials)
PILOT_REPLICATES = 2    # replicates per condition in pilot mode


# ---------------------------------------------------------------------------
# Worker function (runs in a separate process)
# ---------------------------------------------------------------------------

def _run_trial(args):
    """
    Execute a single trial and return a result dict.

    Each call creates its own SimulationManager so processes are fully
    isolated — no shared pygame/pymunk state.

    Parameters (packed into args tuple for Pool.imap_unordered):
        trial_id          : int
        swarm_size        : int
        shape_type        : str
        shuffle_randomness: float
        shuffle_duration  : int   (frames)
    """
    trial_id, swarm_size, shape_type, shuffle_randomness, shuffle_duration = args

    # Seed both RNGs for this trial so results are fully reproducible.
    random.seed(trial_id)
    np.random.seed(trial_id)

    # Apply per-trial config overrides before the manager starts the simulation.
    config.SHUFFLE_RANDOMNESS = shuffle_randomness
    config.SHUFFLE_DURATION_FRAMES = shuffle_duration
    config.SIMULATION_TIME_LIMIT = SIMULATION_TIME_LIMIT

    try:
        manager = SimulationManager()
        result = manager.run_trial(
            swarm_size=swarm_size,
            shape_type=shape_type,
            shuffle_randomness=shuffle_randomness,
            trial_id=trial_id,
            quiet=True,
        )
        return {
            "trial_id": trial_id,
            "swarm_size": swarm_size,
            "shape_type": shape_type,
            "shuffle_randomness": shuffle_randomness,
            "shuffle_duration": shuffle_duration,
            "success": bool(result),
            "completion_time": manager.timer,
            "peak_attached": manager.peak_attached,
            "num_jams": manager.num_jams,
            "total_shuffles": manager.total_shuffles,
            "time_to_first_attachment": manager.time_to_first_attachment,
            "final_payload_distance": manager.final_payload_distance,
            "error": False,
        }
    except Exception as e:
        print(f"\n[ERROR] Trial {trial_id} crashed: {e}", flush=True)
        return {
            "trial_id": trial_id,
            "swarm_size": swarm_size,
            "shape_type": shape_type,
            "shuffle_randomness": shuffle_randomness,
            "shuffle_duration": shuffle_duration,
            "success": False,
            "completion_time": SIMULATION_TIME_LIMIT,
            "peak_attached": 0,
            "num_jams": 0,
            "total_shuffles": 0,
            "time_to_first_attachment": None,
            "final_payload_distance": 0.0,
            "error": True,
        }


# ---------------------------------------------------------------------------
# Main experiment runner
# ---------------------------------------------------------------------------

def run_followup_experiment():
    # --- Timestamped output folder ---
    run_id = datetime.now().strftime("followup_run_%Y%m%d_%H%M%S")
    # Store results inside followup_experiment/results/ for easy tracking
    _here = os.path.dirname(os.path.abspath(__file__))
    run_folder = os.path.join(_here, "results", run_id)
    logger = DataLoggerFollowup(run_folder)

    # --- Write locked parameter snapshot alongside results ---
    params_snapshot = {
        "pilot_mode": PILOT_MODE,
        "pilot_replicates": PILOT_REPLICATES if PILOT_MODE else None,
        "shapes": SHAPES,
        "swarm_sizes": SWARM_SIZES,
        "shuffle_randomness_levels": SHUFFLE_RANDOMNESS_LEVELS,
        "shuffle_duration_levels_frames": SHUFFLE_DURATION_LEVELS,
        "shuffle_duration_levels_seconds": [d / 60 for d in SHUFFLE_DURATION_LEVELS],
        "trials_per_condition": TRIALS_PER_CONDITION,
        "simulation_time_limit_s": SIMULATION_TIME_LIMIT,
        "agent_radius_px": config.AGENT_RADIUS,
        "agent_vision_radius_px": config.AGENT_VISION_RADIUS,
        "agent_vision_radius_pct_arena": round(config.AGENT_VISION_RADIUS / config.ARENA_WIDTH * 100, 2),
        "agent_max_speed": config.AGENT_MAX_SPEED,
        "target_mass": config.TARGET_MASS,
        "damping": config.DAMPING,
        "arena_width_px": config.ARENA_WIDTH,
        "arena_height_px": config.ARENA_HEIGHT,
        "small_object_count": config.SMALL_OBJECT_COUNT,
        "layer_1_decay_rate": config.LAYER_1_DECAY_RATE,
        "layer_2_decay_rate": config.LAYER_2_DECAY_RATE,
        "pheromone_diffusion_rate": config.PHEROMONE_DIFFUSION_RATE,
    }
    with open(os.path.join(run_folder, "params.json"), "w") as f:
        json.dump(params_snapshot, f, indent=2)

    # --- Build the full trial list ---
    # Outer loops define condition order; inner loop is the 50 repetitions.
    # trial_id starts at 1 and increments globally across all conditions.
    reps = PILOT_REPLICATES if PILOT_MODE else TRIALS_PER_CONDITION
    trial_args = []
    trial_id = 1
    for shape in SHAPES:
        for size in SWARM_SIZES:
            for sr in SHUFFLE_RANDOMNESS_LEVELS:
                for dur in SHUFFLE_DURATION_LEVELS:
                    for _ in range(reps):
                        trial_args.append((trial_id, size, shape, sr, dur))
                        trial_id += 1

    total_trials = len(trial_args)

    # --- Print experiment summary ---
    print("=" * 60)
    print("Follow-up Experiment  (B+C sweep)")
    print("=" * 60)
    print(f"  Shapes      : {SHAPES}")
    print(f"  Swarm sizes : {SWARM_SIZES}")
    print(f"  SR levels   : {SHUFFLE_RANDOMNESS_LEVELS}  ({len(SHUFFLE_RANDOMNESS_LEVELS)} levels)")
    print(f"  Durations   : {SHUFFLE_DURATION_LEVELS} frames  ({len(SHUFFLE_DURATION_LEVELS)} levels)")
    print(f"  Trials/cond : {TRIALS_PER_CONDITION}")
    print(f"  Total trials: {total_trials}{'  [PILOT]' if PILOT_MODE else ''}")
    print(f"  Time limit  : {SIMULATION_TIME_LIMIT} s")
    print(f"  Output      : {run_folder}/")
    print("=" * 60)
    print()

    # --- Per-condition progress tracking ---
    # Map (shape, size, sr, dur) → [successes, total]
    condition_stats: dict = {}

    completed = 0
    with Pool(processes=WORKER_PROCESSES) as pool:
        for res in pool.imap_unordered(_run_trial, trial_args):
            completed += 1

            # Log to CSV immediately.
            logger.log_trial(
                trial_id=res["trial_id"],
                swarm_size=res["swarm_size"],
                shape_type=res["shape_type"],
                shuffle_randomness=res["shuffle_randomness"],
                shuffle_duration_frames=res["shuffle_duration"],
                success=res["success"],
                completion_time=res["completion_time"],
                peak_attached=res["peak_attached"],
                num_jams=res["num_jams"],
                total_shuffles=res["total_shuffles"],
                time_to_first_attachment=res["time_to_first_attachment"],
                final_payload_distance=res["final_payload_distance"],
                error=res["error"],
            )

            # Update per-condition running totals.
            key = (res["shape_type"], res["swarm_size"],
                   res["shuffle_randomness"], res["shuffle_duration"])
            if key not in condition_stats:
                condition_stats[key] = [0, 0]
            condition_stats[key][1] += 1
            if res["success"]:
                condition_stats[key][0] += 1

            # Progress line — overwrite in place with \r.
            shape, size, sr, dur = key
            s, n = condition_stats[key]
            print(
                f"[{completed:>6}/{total_trials}]  "
                f"shape={shape:<8}  size={size:>2}  "
                f"SR={sr:.1f}  dur={dur:>3}fr  "
                f"({s}/{n} success in cond)",
                end="\r",
                flush=True,
            )

            # When a condition finishes all 50 reps, print a summary line.
            if n == reps:
                rate = s / TRIALS_PER_CONDITION
                print(
                    f"\n  DONE  shape={shape:<8}  size={size:>2}  "
                    f"SR={sr:.1f}  dur={dur:>3}fr  "
                    f"success={rate:.0%}  ({s}/{TRIALS_PER_CONDITION})",
                    flush=True,
                )

    print(f"\n\n=== Complete. Results saved to: {run_folder}/ ===")


if __name__ == "__main__":
    run_followup_experiment()
