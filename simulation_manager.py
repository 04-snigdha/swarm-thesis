# simulation_manager.py
import config
from physics_engine import PhysicsEngine
from stigmergy_grid import PheromoneGrid
from swarm_agents import Agent
from data_logger import DataLogger
import random
import math
import collections

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
        self.target_velocities = collections.deque(maxlen=60)
        
        # Pass agents reference to space for physics engine callbacks
        self.physics.space.agents = self.agents
        
        # Spawn Target in FORAGE_ZONE (Left)
        fx, fy, fw, fh = config.FORAGE_ZONE
        target_pos = (fx + fw/2, fy + fh/2)
        self.physics.spawn_target_shape(shape_type, target_pos)
        
        # Spawn Agents in HOME_ZONE (Right)
        hx, hy, hw, hh = config.HOME_ZONE
        for _ in range(swarm_size):
            ax = random.uniform(hx, hx + hw)
            ay = random.uniform(hy, hy + hh)
            agent = Agent(self.physics.space, (ax, ay))
            self.agents.append(agent)

    def is_trial_successful(self):
        if self.physics.target_body:
            target_pos = self.physics.target_body.position
            hx, hy = config.HOME_BASE_COORD
            dist = math.sqrt((target_pos.x - hx)**2 + (target_pos.y - hy)**2)
            if dist < 100:
                return True
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
        
        import math
        while True:
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
            
            # 2. Agent Decisions & Vector Deposition
            num_attached = len([a for a in self.agents if getattr(a, 'active_joint', None)])
            for agent in self.agents:
                # Conditional Stigmergy: First agent acts as beacon.
                if agent.state == "RETRIEVING" and num_attached > 0 and getattr(agent, 'active_joint', None):
                    hx = config.HOME_BASE_COORD[0]
                    hy = config.HOME_BASE_COORD[1]
                    target_pos = self.physics.target_body.position
                    dx, dy = hx - target_pos.x, hy - target_pos.y
                    mag = math.sqrt(dx**2 + dy**2)
                    if mag > 0:
                        # Vector strength increases proportionally to num_attached
                        self.pheromones.deposit_pheromone(agent.body.position, (dx/mag * num_attached, dy/mag * num_attached), layer=1)
                
                elif agent.state == "RETURN_TO_BASE":
                    target_pos = self.physics.target_body.position
                    dx, dy = target_pos.x - agent.body.position.x, target_pos.y - agent.body.position.y
                    mag = math.sqrt(dx**2 + dy**2)
                    if mag > 0:
                        self.pheromones.deposit_pheromone(agent.body.position, (dx/mag, dy/mag), layer=2)
                        
                local_grad = self.pheromones.get_gradient(agent.body.position)
                agent.apply_movement_logic(local_grad, self.physics.target_body, self.agents)
                
                # Cleanup detached joints if any logic error caused a state flip
                if agent.state != "RETRIEVING" and getattr(agent, 'active_joint', None):
                    self.physics.space.remove(agent.active_joint)
                    agent.active_joint = None
                
            # 3. Physics Step (Mechanical Stigmergy)
            self.physics.step(dt)
            
            # 4. Jam Detection (Stochastic Shuffling)
            if self.physics.target_body:
                vel = self.physics.target_body.velocity
                speed = math.sqrt(vel.x**2 + vel.y**2)
                self.target_velocities.append(speed)
                
                if len(self.target_velocities) == 60:
                    avg_speed = sum(self.target_velocities) / 60.0
                    if avg_speed < 5.0:
                        # Jam Detected! Trigger Return to Base logic
                        for agent in self.agents:
                            if agent.state == "RETRIEVING" and getattr(agent, 'active_joint', None):
                                self.physics.space.remove(agent.active_joint)
                                agent.active_joint = None
                                agent.state = "RETURN_TO_BASE"
                                agent.state_timer = 60
                        self.target_velocities.clear()
            
            if vis:
                vis.update(self.agents, self.timer)
                clock.tick(config.FPS)
            
            # 4. Check Trial End Conditions
            if self.is_trial_successful():
                if not quiet:
                    print(f"  -> SUCCESS! Time: {self.timer:.2f}s")
                self.logger.log_trial(self.trial_count, swarm_size, shape_type, True, self.timer)
                return True
                
            self.timer += dt
        
if __name__ == "__main__":
    # Small test run with visualization enabled
    manager = SimulationManager()
    manager.run_trial(20, "L-shape", visualize=True)
