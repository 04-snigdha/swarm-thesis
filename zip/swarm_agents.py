# swarm_agents.py
import pymunk
import random
import math
import config

class Agent:
    def __init__(self, space, position):
        # Mechanical Stigmergy setup
        moment = pymunk.moment_for_circle(config.AGENT_MASS, 0, config.AGENT_RADIUS)
        self.body = pymunk.Body(config.AGENT_MASS, moment)
        self.body.position = position
        
        self.shape = pymunk.Circle(self.body, config.AGENT_RADIUS)
        self.shape.elasticity = config.ELASTICITY
        self.shape.friction = config.FRICTION
        
        space.add(self.body, self.shape)
        
        # Chemical Stigmergy / Logic state
        self.state = "SEARCHING"
        self.max_speed = config.AGENT_MAX_SPEED
        
    def apply_movement_logic(self, local_pheromone_gradient):
        """
        Determines the agent's movement force based on stigmergy principles.
        """
        force_x, force_y = 0.0, 0.0
        
        if self.state == "SEARCHING":
            # Chemical Stigmergy: Gradient ascent
            # If gradient is zero (no pheromone), agents rely on random walk
            grad_x, grad_y = local_pheromone_gradient
            
            # Add random noise (Brownian motion / random walk)
            noise_x = random.uniform(-1, 1) * self.max_speed * 0.5
            noise_y = random.uniform(-1, 1) * self.max_speed * 0.5
            
            force_x = (grad_x * self.max_speed) + noise_x
            force_y = (grad_y * self.max_speed) + noise_y
            
        elif self.state == "RETRIEVING":
            # Mechanical Stigmergy: Push towards the target/gap blindly
            # In a true decentralized system with local sensing, they push generally 
            # rightwards towards the gap, interacting via rigid body collisions.
            force_x = self.max_speed
            force_y = random.uniform(-0.2, 0.2) * self.max_speed # slight variation
            
        # Clamp force to max speed
        magnitude = math.sqrt(force_x**2 + force_y**2)
        if magnitude > self.max_speed:
            scale = self.max_speed / magnitude
            force_x *= scale
            force_y *= scale
            
        # Apply force to center of mass
        self.body.apply_force_at_local_point((force_x, force_y), (0, 0))
