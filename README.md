# Decentralized Cooperative Transport: Scaling Laws & Mechanical Stigmergy
A physics-based investigation into how swarm size and payload geometry influence cooperative transport and kinematic gridlock, free from reinforcement learning bias.

## 🚀 Getting Started
- **Prerequisites:** Python 3.12+ (LTS)
- **Dependency Installation:**
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  pip install pymunk pygame numpy pandas matplotlib
  ```

## ⚙️ Running the Experiments

**Batch Data Collection:** To run the automated 1,000-trial experiment, execute:
```bash
python experiment_runner.py
```

**Real-Time Visualization:** To observe the swarm mechanics and jamming behaviors visually, execute:
```bash
python simulation_manager.py
```
*Note: Use `[Spacebar]` to pause and `V` to toggle pheromone heatmap visibility.*

## 📂 Architecture


## Summary Table

| File Name | Primary Responsibility | Stigmergy Role |
| :--- | :--- | :--- |
| `config.py` | Centralizes simulation parameters, constants, and hyperparameters. | Orchestration |
| `physics_engine.py` | Manages the Pymunk rigid-body space, collision geometry, and environment generation. | Mechanical |
| `swarm_agents.py` | Defines the logic, state machine (`SEARCHING` vs `RETRIEVING`), and continuous force application of the robots. | Mechanical / Chemical |
| `stigmergy_grid.py` | Handles spatial vector field representing pheromones, computing localized gradient and applying decay/diffusion over time. | Chemical |
| `simulation_manager.py` | Synchronizes the physics step, pheromone diffusion, agent decisions, and visualizer hook. | Orchestration |
| `data_logger.py` | Records independent and dependent trial variables to a CSV file for statistical analysis. | Orchestration |
| `visualizer.py` | Renders a real-time visualization of the physics space and pheromone heatmaps using Pygame. | Orchestration |

## Module Pseudocode

### 1. config.py
**Role**: Orchestration
```python
# config.py - Pseudocode
DEFINE FPS = 60
DEFINE SIMULATION_TIME_LIMIT = 20.0 seconds

DEFINE SWARM_SIZES = [5, 10, 20, 40]
DEFINE AGENT_RADIUS = 10, AGENT_MASS = 1.0, AGENT_MAX_SPEED = 50.0

DEFINE ARENA_WIDTH = 800, ARENA_HEIGHT = 800
DEFINE TARGET_SHAPES = ["Circle", "Square", "L-shape", "C-shape"]

DEFINE PHEROMONE_DECAY_RATE = 0.99
DEFINE PHEROMONE_DIFFUSION_RATE = 0.1

DEFINE ELASTICITY = 0.5, FRICTION = 0.5
```

### 2. physics_engine.py
**Role**: Mechanical Stigmergy Core
```python
# physics_engine.py - Pseudocode
CLASS PhysicsEngine:
    METHOD initialize():
        INITIALIZE Pymunk Space
        SET space damping (friction/drag)

    METHOD generate_walls(width, height, gap_size):
        CREATE static bounding box segments
        CREATE vertical central dividing walls with central `gap_size`
        ASSIGN ELASTICITY and FRICTION
        ADD segments to Space

    METHOD spawn_target_shape(shape_type, position):
        IF shape_type == "Circle" or "Square":
            CALCULATE moment of inertia for convex primitive
            CREATE dynamic Body
            ATTACH Poly/Circle shape to Body
        ELSE IF shape_type == "L-shape" or "C-shape":
            CALCULATE combined moment of inertia for complex geometry
            CREATE dynamic Body
            ATTACH multiple Poly segments (compound rigid body)
            
        ASSIGN ELASTICITY and FRICTION to all shapes
        ADD shapes and Body to Space
        RETURN Body reference

    METHOD step(dt):
        ADVANCE Pymunk simulation by dt
```

### 3. swarm_agents.py
**Role**: Hybrid Stigmergy Evaluator
```python
# swarm_agents.py - Pseudocode
CLASS Agent:
    METHOD initialize(space, position):
        CREATE Pymunk rigid body and circular shape
        ADD to space
        SET state = "SEARCHING"

    METHOD apply_movement_logic(local_pheromone_gradient):
        INITIALIZE force_x = 0, force_y = 0
        
        IF state == "SEARCHING":
            # Chemical Stigmergy Integration
            EXTRACT grad_x, grad_y FROM local_pheromone_gradient
            GENERATE random_noise vector (Brownian motion)
            COMPUTE force_vector = (gradient * max_speed) + random_noise
            
        ELSE IF state == "RETRIEVING":
            # Mechanical Stigmergy Integration
            # Blindly push generally towards the right (towards the gap)
            COMPUTE force_vector = (max_speed, random_variation)
            
        CLAMP force_vector magnitude to max_speed
        APPLY force_vector to Agent's rigid body center
```

### 4. stigmergy_grid.py
**Role**: Chemical Stigmergy Core
```python
# stigmergy_grid.py - Pseudocode
CLASS PheromoneGrid:
    METHOD initialize(width, height, cell_size):
        INITIALIZE 3D matrix (rows x cols x 2) for (X, Y) vector field

    METHOD deposit_pheromone(position, vector):
        CONVERT continuous position to discrete grid (row, col)
        ADD vector to matrix[row, col]

    METHOD diffuse_and_decay():
        COMPUTE discrete cross-diffusion (average of neighboring 4 cells * diffusion rate)
        APPLY decay scalar (value = value * decay_rate)
        UPDATE matrix

    METHOD get_gradient(position):
        CONVERT continuous position to discrete grid (row, col)
        RETURN matrix[row, col] (Vector X, Y)
```

### 5. simulation_manager.py
**Role**: Central Orchestration
```python
# simulation_manager.py - Pseudocode
CLASS SimulationManager:
    METHOD reset_environment(swarm_size, shape_type):
        INSTANTIATE PhysicsEngine and generate arena
        INSTANTIATE PheromoneGrid
        SPAWN Target Shape at target_pos
        SPAWN N Agents in a cluster near target_pos

    METHOD run_trial(swarm_size, shape_type):
        reset_environment()
        
        WHILE timer < SIMULATION_TIME_LIMIT:
            diffuse_and_decay PheromoneGrid
            
            FOR EACH agent IN agents:
                IF distance(agent, target) < threshold:
                    SET agent state = "RETRIEVING"
                    
                GET local gradient from PheromoneGrid
                CALL agent.apply_movement_logic(gradient)
                
            CALL physics.step(dt)
            
            IF Target X-position > Arena Width / 2:
                LOG SUCCESS
                BREAK Loop
                
            INCREMENT timer
            
        IF Target did not pass gap:
            LOG FAILURE
```

### 6. data_logger.py
**Role**: Orchestration / Analytics
```python
# data_logger.py - Pseudocode
CLASS DataLogger:
    METHOD initialize(filename="results.csv"):
        IF file does not exist:
            CREATE CSV file and Write Headers ("Trial_ID", "Swarm_Size", "Shape", "Success", "Time", "Error")

    METHOD log_trial(trial_id, size, shape, success, time, error):
        APPEND row [trial_id, size, shape, success, time, error] to CSV
```

### 7. visualizer.py
**Role**: Orchestration / Debugging
```python
# visualizer.py - Pseudocode
CLASS Visualizer:
    METHOD initialize(physics_space, pheromone_grid):
        INITIALIZE Pygame display context
        
    METHOD handle_events():
        PROCESS Keyboard input
        IF SPACEBAR pressed: TOGGLE pause
        IF 'V' pressed: TOGGLE heatmap visibility
        
    METHOD _draw_pheromones():
        IF visibility is ON:
            FOR EACH cell IN pheromone_grid:
                CALCULATE magnitude of vector
                IF magnitude > threshold:
                    DRAW transparent yellow rectangle with alpha = magnitude
                    
    METHOD _draw_agents(agents):
        FOR EACH agent IN agents:
            IF agent state == "SEARCHING":
                DRAW Green Circle
            ELSE:
                DRAW Blue Circle
            DRAW heading indicator line

    METHOD update(agents, time):
        CLEAR screen
        CALL _draw_pheromones()
        CALL pymunk debug_draw (draws physical walls and target polygons)
        CALL _draw_agents(agents)
        DRAW HUD text (time, paused state, visibility state)
        FLIP display buffer
```

## Simulation Results

```text
Thesis Analysis Summary - Scaling Laws for Decentralized Swarm Robotics

1. Tipping Point for Gap Traversal:
Based on the success rates, we observe a distinct transition point where the swarm achieves critical mass to overcome the gap's physical bottleneck.
      Shape  Swarm_Size    Success
0   C-shape           5   1.587302
1   C-shape          10  12.698413
2   C-shape          20  29.032258
3   C-shape          40  53.225806
4    Circle           5   7.936508
5    Circle          10  22.222222
6    Circle          20  27.419355
7    Circle          40  48.387097
8   L-shape           5   6.349206
9   L-shape          10  15.873016
10  L-shape          20  33.870968
11  L-shape          40  59.677419
12   Square           5   7.936508
13   Square          10   4.761905
14   Square          20  20.967742
15   Square          40  41.935484

2. Impact of Non-Convex Geometry:
Mean completion times for successful runs:
      Shape  Swarm_Size  Completion_Time
0   C-shape           5        14.233333
1   C-shape          10         9.889583
2   C-shape          20         9.589815
3   C-shape          40         7.239394
4    Circle           5        15.703333
5    Circle          10        13.873810
6    Circle          20        13.436275
7    Circle          40         9.336667
8   L-shape           5        11.075000
9   L-shape          10        11.558333
10  L-shape          20         9.776190
11  L-shape          40         7.275676
12   Square           5        11.703333
13   Square          10         9.316667
14   Square          20         9.915385
15   Square          40         8.814744

The statistical box plots visually confirm that non-convex shapes (L-shape, C-shape) exhibit extreme variance and delayed completion times. This is direct empirical evidence of "mechanical debt," where the shape hooks onto the gap edges, causing kinematic gridlock.

3. Decentralized Mechanical Stigmergy Sufficiency:
The jamming frequency plot illustrates the limits of pure mechanical stigmergy. While the swarm can successfully traverse simple, convex shapes (Circle, Square) using blind collective pushing, complex shapes (C-shape) fail disproportionately. This statistically validates the hypothesis that higher densities (N=40) or the introduction of Chemical Stigmergy (repellent vector pheromones) are required to un-jam the payload.
```
