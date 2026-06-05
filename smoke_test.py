from simulation_manager import SimulationManager
import config

for shape in config.TARGET_SHAPES:
    m = SimulationManager()
    r = m.run_trial(20, shape, trial_id=1, quiet=True)
    print(shape, "SUCCESS" if r else "FAILED")
