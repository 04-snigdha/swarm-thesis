"""
GIF recorder for illustrative simulation trials.

Runs handpicked conditions headlessly (no display window shown to user),
captures frames, and saves one GIF per trial into recordings/gifs/.

Usage:
    python recordings/record_runner.py

Output:
    recordings/gifs/<shape>_sz<size>_sr<sr>[_dur<dur>]_trial<n>.gif

Each condition is run REPS_PER_CONDITION times so you can pick the
best-looking GIF. Existing files are skipped automatically.
"""

import os, sys, math, random, collections
import numpy as np
import pygame
from PIL import Image

# ── path setup ───────────────────────────────────────────────────────────────
_here   = os.path.dirname(os.path.abspath(__file__))
_root   = os.path.dirname(_here)
sys.path.insert(0, _root)

import config
from physics_engine    import PhysicsEngine
from stigmergy_grid    import PheromoneGrid
from swarm_agents      import Agent
from simulation_manager import SimulationManager

GIF_DIR = os.path.join(_here, "gifs")
os.makedirs(GIF_DIR, exist_ok=True)

# ── recording parameters ─────────────────────────────────────────────────────
FPS_CAPTURE   = 6         # frames captured per second (simulation runs at config.FPS)
CAPTURE_EVERY = max(1, config.FPS // FPS_CAPTURE)   # capture 1 frame every N sim frames
GIF_SPEED_MS  = 120       # ms per GIF frame  (~8 fps playback)
SCALE         = 0.4       # downscale factor to keep file sizes small
REPS          = 3         # trials recorded per condition

# ── conditions to record ─────────────────────────────────────────────────────
# Each entry: (shape, swarm_size, shuffle_randomness, shuffle_duration_s | None)
# duration=None means use whatever config.SHUFFLE_DURATION_FRAMES is set to (main experiment default)
CONDITIONS = [
    # --- Convex baselines ---
    ("Circle",  25, 0.0,  None),
    ("Circle",  35, 0.0,  None),
    ("Square",  25, 0.0,  None),
    ("Square",  35, 0.0,  None),
    # --- L-shape ---
    ("L-shape", 25, 0.0,  None),   # success case
    ("L-shape", 35, 1.0,  None),   # failure case
    # --- C-shape main experiment ---
    ("C-shape", 25, 0.0,  None),   # rare success
    ("C-shape", 35, 0.0,  None),   # classic stuck failure
    ("C-shape", 35, 1.0,  None),   # worst case
    # --- C-shape follow-up: duration effect ---
    ("C-shape", 35, 0.0,  1.0),    # short duration failure
    ("C-shape", 35, 0.0,  8.0),    # long duration success
]


# ── offscreen pygame surface ─────────────────────────────────────────────────
def _init_offscreen():
    """Initialise pygame in offscreen (no window) mode."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    total_w = config.ARENA_WIDTH + config.HUD_WIDTH
    total_h = config.ARENA_HEIGHT
    screen  = pygame.display.set_mode((total_w, total_h))
    return screen


def _surface_to_pil(surface, scale=SCALE):
    """Convert a pygame surface to a PIL Image, optionally downscaled."""
    raw  = pygame.surfarray.array3d(surface)   # (W, H, 3) uint8
    img  = Image.fromarray(raw.transpose(1, 0, 2))   # PIL wants (H, W, 3)
    if scale != 1.0:
        w, h = img.size
        img  = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return img.convert("P", palette=Image.ADAPTIVE, colors=256)


# ── single trial recorder ─────────────────────────────────────────────────────
def record_trial(screen, shape, size, sr, duration_s, trial_n, seed):
    """Run one trial, capture frames, return list of PIL images."""
    # Apply config overrides
    config.SHUFFLE_RANDOMNESS = sr
    if duration_s is not None:
        config.SHUFFLE_DURATION_FRAMES = int(duration_s * config.FPS)

    from visualizer import Visualizer

    # Fresh simulation
    manager = SimulationManager(logger=None)
    manager.reset_environment(size, shape)
    manager.peak_attached = 0

    random.seed(seed)
    np.random.seed(seed)

    vis = Visualizer(manager.physics.space, manager.pheromones)

    frames   = []
    frame_n  = 0
    dt       = 1.0 / config.FPS

    while manager.timer < config.SIMULATION_TIME_LIMIT:
        # Pump events so pygame doesn't freeze
        pygame.event.pump()

        # ── simulation step (copy of SimulationManager inner loop) ────────
        manager.pheromones.diffuse_and_decay()

        num_attached = len([a for a in manager.agents if getattr(a, "active_joint", None)])
        if num_attached > manager.peak_attached:
            manager.peak_attached = num_attached
        if num_attached > 0 and manager.time_to_first_attachment is None:
            manager.time_to_first_attachment = manager.timer

        for agent in manager.agents:
            if agent.state == "RETRIEVING" and num_attached > 0 and getattr(agent, "active_joint", None):
                hx, hy = config.HOME_BASE_COORD
                tp      = manager.physics.target_body.position
                dx, dy  = hx - tp.x, hy - tp.y
                mag     = math.sqrt(dx**2 + dy**2)
                if mag > 0:
                    manager.pheromones.deposit_pheromone(
                        agent.body.position,
                        (dx/mag * num_attached, dy/mag * num_attached), layer=1)
            elif agent.state == "RETURN_TO_BASE":
                tp     = manager.physics.target_body.position
                dx, dy = tp.x - agent.body.position.x, tp.y - agent.body.position.y
                mag    = math.sqrt(dx**2 + dy**2)
                if mag > 0:
                    manager.pheromones.deposit_pheromone(
                        agent.body.position, (dx/mag, dy/mag), layer=2)

            local_grad = manager.pheromones.get_gradient(agent.body.position)
            agent.apply_movement_logic(
                local_grad, manager.physics.target_body,
                manager.agents, manager.small_objects)

            if agent.state != "RETRIEVING" and agent.active_joint:
                manager.physics.space.remove(agent.active_joint)
                agent.active_joint = None

            if agent.state == "CARRYING" and agent.carry_joint:
                hx, hy = config.HOME_BASE_COORD
                dx = agent.body.position.x - hx
                dy = agent.body.position.y - hy
                if math.sqrt(dx**2 + dy**2) < 30:
                    carried = agent.carried_body
                    manager.physics.space.remove(agent.carry_joint)
                    agent.carry_joint = None
                    if carried in manager.small_objects:
                        manager.small_objects.remove(carried)
                        for s in list(carried.shapes):
                            manager.physics.space.remove(s)
                        manager.physics.space.remove(carried)
                    agent.carried_body = None
                    manager.pheromones.deposit_pheromone(
                        agent.body.position,
                        (hx - agent.body.position.x, hy - agent.body.position.y), layer=1)
                    agent.state = "SEARCHING"
                    agent.state_timer = 30

        manager.physics.step(dt)

        # Jam detection
        if manager.physics.target_body:
            vel   = manager.physics.target_body.velocity
            speed = math.sqrt(vel.x**2 + vel.y**2)
            manager.target_velocities.append(speed)
            if len(manager.target_velocities) == 60:
                avg_speed = sum(manager.target_velocities) / 60.0
                if avg_speed < 5.0:
                    jam_agents = [a for a in manager.agents
                                  if a.state == "RETRIEVING" and a.active_joint]
                    if jam_agents:
                        manager.num_jams    += 1
                        manager.total_shuffles += len(jam_agents)
                    for a in jam_agents:
                        a._detach()
                        a.state       = "SHUFFLING"
                        a.state_timer = config.SHUFFLE_DURATION_FRAMES
                    manager.target_velocities.clear()

        # Capture frame
        if frame_n % CAPTURE_EVERY == 0:
            vis.update(manager.agents, manager.timer,
                       manager.small_objects, manager.physics.target_body)
            frames.append(_surface_to_pil(screen))

        frame_n      += 1
        manager.timer += dt

        if manager.is_trial_successful():
            # Capture a few extra frames on success so the end is visible
            for _ in range(FPS_CAPTURE * 2):
                vis.update(manager.agents, manager.timer,
                           manager.small_objects, manager.physics.target_body)
                frames.append(_surface_to_pil(screen))
            break

    pygame.quit()
    pygame.init()                        # re-init for next trial
    screen = pygame.display.set_mode(
        (config.ARENA_WIDTH + config.HUD_WIDTH, config.ARENA_HEIGHT))
    return frames, screen


# ── GIF writer ────────────────────────────────────────────────────────────────
def save_gif(frames, path):
    if not frames:
        print(f"  [skip] no frames captured")
        return
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        loop=0,
        duration=GIF_SPEED_MS,
        optimize=True,
    )
    size_kb = os.path.getsize(path) // 1024
    print(f"  Saved ({len(frames)} frames, {size_kb} KB): {os.path.basename(path)}")


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    screen = _init_offscreen()

    for (shape, size, sr, dur) in CONDITIONS:
        dur_tag = f"_dur{int(dur)}s" if dur is not None else ""
        prefix  = f"{shape.replace('-','')}_sz{size}_sr{str(sr).replace('.','')}{dur_tag}"

        for rep in range(1, REPS + 1):
            fname = os.path.join(GIF_DIR, f"{prefix}_trial{rep}.gif")
            if os.path.exists(fname):
                print(f"  [exists] {os.path.basename(fname)}")
                continue

            seed = hash((shape, size, sr, dur, rep)) % (2**31)
            print(f"Recording: {shape} sz={size} sr={sr} dur={dur}s rep={rep}/{REPS}")
            frames, screen = record_trial(screen, shape, size, sr, dur, rep, seed)
            save_gif(frames, fname)

    pygame.quit()
    print("\nDone. GIFs saved to:", GIF_DIR)


if __name__ == "__main__":
    main()
