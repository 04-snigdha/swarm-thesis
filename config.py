# config.py

# --- Simulation Parameters ---
FPS = 60
SIMULATION_TIME_LIMIT = 60.0 # 60 seconds search timer

# --- Swarm Parameters ---
SWARM_SIZES = [5, 10, 20, 40]
AGENT_RADIUS = 5
AGENT_MASS = 1.0
AGENT_MAX_SPEED = 50.0

# --- Global Navigation Parameters ---
HOME_BASE_COORD = (700, 350)
HOME_NAV_WEIGHT = 0.40

# --- Geometry & Arena ---
ARENA_WIDTH = 800
ARENA_HEIGHT = 800
TARGET_SHAPES = ["Circle", "Square", "L-shape", "C-shape"]
GAP_WIDTH = 150
WALL_THICKNESS = 20

# --- Pheromone (Chemical) --- Stigmergy Parameters ---
LAYER_0_DECAY_RATE = 0.90  # Fast decay (Search)
LAYER_1_DECAY_RATE = 0.95  # Medium decay (Transport/Home)
LAYER_2_DECAY_RATE = 0.99  # Low decay (Help-Signal)
PHEROMONE_DIFFUSION_RATE = 0.1
GRID_CELL_SIZE = 10

# --- Physics Constants ---
DAMPING = 0.8
ELASTICITY = 0.5
FRICTION = 0.5

# --- Home/Forage Spatial Zones ---
HOME_ZONE = (650, 100, 100, 600)  # (x, y, width, height)
FORAGE_ZONE = (50, 100, 150, 600)

# --- Collision Types ---
COLLISION_TYPE_AGENT = 1
COLLISION_TYPE_TARGET = 2
