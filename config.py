# config.py

# --- Simulation Parameters ---
FPS = 60
SIMULATION_TIME_LIMIT = 180.0 # 180 seconds per trial

# --- Swarm Parameters ---
SWARM_SIZES = [5, 10, 20, 40]
AGENT_RADIUS = 5
AGENT_MASS = 1.0
AGENT_MAX_SPEED = 25.0
TARGET_MASS = 150.0        # heavier payload — requires coordinated group effort
ANT_HOLE = (720, 350)      # single spawn point (simulates colony entrance)

# --- Stochastic Shuffling ---
# 0.0 = pure orbital redistribution around target (CVT-like)
# 1.0 = full Brownian random walk during shuffle
SHUFFLE_RANDOMNESS = 0.5
SHUFFLE_DURATION_FRAMES = 120  # 2 seconds at 60 FPS

# --- Global Navigation Parameters ---
HOME_BASE_COORD = (700, 350)
HOME_NAV_WEIGHT = 0.40

# --- Geometry & Arena ---
ARENA_WIDTH = 800
ARENA_HEIGHT = 800
HUD_WIDTH = 280          # sidebar panel width (window = ARENA_WIDTH + HUD_WIDTH)
TARGET_SHAPES = ["Circle", "Square", "L-shape", "C-shape"]
GAP_WIDTH = 150
WALL_THICKNESS = 20
ANT_PASSAGE_WIDTH = 15   # narrow holes ants fit through; payload (60 px+) cannot

# --- Pheromone (Chemical) --- Stigmergy Parameters ---
LAYER_0_DECAY_RATE = 0.90  # Fast decay (Search)
LAYER_1_DECAY_RATE = 0.98  # Slow decay (Transport/Home) — trail must persist long enough to recruit
LAYER_2_DECAY_RATE = 0.999  # Very slow decay — trail must persist the full home-to-target journey
PHEROMONE_DIFFUSION_RATE = 0.05  # lower diffusion = narrower, more directed trail
GRID_CELL_SIZE = 10

# --- Physics Constants ---
DAMPING = 0.6
ELASTICITY = 0.5
FRICTION = 0.5

# --- Home/Forage Spatial Zones ---
HOME_ZONE = (650, 100, 100, 600)  # (x, y, width, height)
FORAGE_ZONE = (50, 100, 150, 600)

# --- Small Foraging Objects ---
SMALL_OBJECT_COUNT = 20       # scattered across the full arena
SMALL_OBJECT_RADIUS = 6
SMALL_OBJECT_MASS = 1.5

# --- Collision Types ---
COLLISION_TYPE_AGENT = 1
COLLISION_TYPE_TARGET = 2
COLLISION_TYPE_SMALL = 3
