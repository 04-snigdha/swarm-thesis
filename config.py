# config.py

# --- Simulation Parameters ---
FPS = 60
SIMULATION_TIME_LIMIT = 20.0 # 20 seconds search timer

# --- Swarm Parameters ---
SWARM_SIZES = [5, 10, 20, 40]
AGENT_RADIUS = 10
AGENT_MASS = 1.0
AGENT_MAX_SPEED = 50.0

# --- Geometry & Arena ---
ARENA_WIDTH = 800
ARENA_HEIGHT = 800
TARGET_SHAPES = ["Circle", "Square", "L-shape", "C-shape"]
GAP_WIDTH = 150
WALL_THICKNESS = 20

# --- Pheromone (Chemical Stigmergy) ---
PHEROMONE_DECAY_RATE = 0.99
PHEROMONE_DIFFUSION_RATE = 0.1
GRID_CELL_SIZE = 10

# --- Physics Constants ---
DAMPING = 0.8
ELASTICITY = 0.5
FRICTION = 0.5
