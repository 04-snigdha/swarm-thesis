# simulation_manager.py
import config
from physics_engine import PhysicsEngine
from stigmergy_grid import PheromoneGrid
from swarm_agents import Agent
from data_logger import DataLogger
import random

try:
    from visualizer import Visualizer
except ImportError:
    Visualizer = None

class SimulationManager:
    def __init__(self):
        self.physics = PhysicsEngine()
        self.pheromones = PheromoneGrid()
        self.agents = []
        self.logger = DataLogger()
        self.timer = 0.0
        self.trial_count = 0
        self.target_shape_type = None

    def reset_environment(self, swarm_size, shape_type):
        """Resets the simulation state for a new trial."""
        self.physics = PhysicsEngine()
        self.physics.generate_walls()
        self.pheromones = PheromoneGrid()
        self.agents = []
        self.timer = 0.0
        self.target_shape_type = shape_type
        
        # Spawn Target
        target_pos = (config.ARENA_WIDTH / 4, config.ARENA_HEIGHT / 2) # Left side
        self.physics.spawn_target_shape(shape_type, target_pos)
        
        # Spawn Agents around the target
        for _ in range(swarm_size):
            # Spawn in a cluster near the target
            ax = target_pos[0] + random.uniform(-100, 100)
            ay = target_pos[1] + random.uniform(-100, 100)
            agent = Agent(self.physics.space, (ax, ay))
            self.agents.append(agent)

    def shape_through_gap(self):
        """Checks if the target body has passed through the central gap (x > width/2)."""
        if self.physics.target_body:
            return self.physics.target_body.position.x > config.ARENA_WIDTH / 2
        return False

    def run_trial(self, swarm_size, shape_type, trial_id=None, quiet=False, visualize=False):
        """Runs a single simulation trial."""
        self.reset_environment(swarm_size, shape_type)
        if trial_id is not None:
            self.trial_count = trial_id
        else:
            self.trial_count += 1
        
        if not quiet:
            print(f"Starting Trial {self.trial_count}: Size {swarm_size}, Shape {shape_type}")
        
        dt = 1.0 / config.FPS
        
        vis = None
        if visualize and Visualizer:
            import pygame
            vis = Visualizer(self.physics.space, self.pheromones)
            clock = pygame.time.Clock()
        
        while self.timer < config.SIMULATION_TIME_LIMIT:
            if vis:
                running = vis.handle_events()
                if not running:
                    break
                if vis.paused:
                    vis.update(self.agents, self.timer)
                    clock.tick(config.FPS)
                    continue
                    
            # 1. Update Pheromones (Chemical Stigmergy)
            self.pheromones.diffuse_and_decay()
            
            # 2. Agent Decisions
            for agent in self.agents:
                # Simple logic wrapper for the thesis:
                # Switch to RETRIEVING if they are close to the target
                dist_to_target = agent.body.position.get_distance(self.physics.target_body.position)
                if dist_to_target < 100:
                    agent.state = "RETRIEVING"
                    
                local_grad = self.pheromones.get_gradient(agent.body.position)
                agent.apply_movement_logic(local_grad)
                
            # 3. Physics Step (Mechanical Stigmergy)
            self.physics.step(dt)
            
            if vis:
                vis.update(self.agents, self.timer)
                clock.tick(config.FPS)
            
            # 4. Check Trial End Conditions
            if self.shape_through_gap():
                if not quiet:
                    print(f"  -> SUCCESS! Time: {self.timer:.2f}s")
                self.logger.log_trial(self.trial_count, swarm_size, shape_type, True, self.timer)
                return True
                
            self.timer += dt
            
        # Failed to push through in time
        if not quiet:
            print(f"  -> FAILED. Time limit reached.")
        self.logger.log_trial(self.trial_count, swarm_size, shape_type, False, config.SIMULATION_TIME_LIMIT)
        return False
        
if __name__ == "__main__":
    # Small test run with visualization enabled
    manager = SimulationManager()
    manager.run_trial(20, "L-shape", visualize=True)
