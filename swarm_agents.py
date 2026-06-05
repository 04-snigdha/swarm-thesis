# swarm_agents.py
import pymunk
import random
import math
import config

class Agent:
    def __init__(self, space, position):
        self.space = space # Save reference for point queries
        # Mechanical Stigmergy setup
        moment = pymunk.moment_for_circle(config.AGENT_MASS, 0, config.AGENT_RADIUS)
        self.body = pymunk.Body(config.AGENT_MASS, moment)
        self.body.position = position
        
        self.shape = pymunk.Circle(self.body, config.AGENT_RADIUS)
        self.shape.elasticity = config.ELASTICITY
        self.shape.friction = config.FRICTION
        self.shape.collision_type = config.COLLISION_TYPE_AGENT
        self.shape.agent = self # Reference for collision handler
        
        space.add(self.body, self.shape)
        
        # Chemical Stigmergy / Logic state
        self.state = "SEARCHING"
        self.max_speed = config.AGENT_MAX_SPEED
        self.touching_target = False
        self.active_joint = None
        self.state_timer = 0
        
        # For correlated random walk
        self.heading = random.uniform(0, 2 * math.pi)
        
    def vision_query(self, target_body):
        """Checks if the target is within vision radius (150px) using distance."""
        dist = math.sqrt((self.body.position.x - target_body.position.x)**2 + (self.body.position.y - target_body.position.y)**2)
        # Using 150 + target approximate radius ensures it doesn't walk past large shapes
        if dist < 200: 
            return target_body
        return None

    def apply_movement_logic(self, local_pheromone_gradient, target_body, all_agents):
        """
        Determines the agent's movement force based on stigmergy principles.
        """
        search_vec, home_vec, help_vec = local_pheromone_gradient
        force_x, force_y = 0.0, 0.0
        
        if self.state_timer > 0:
            self.state_timer -= 1
        
        # --- 1. Dynamic State Transitions ---
        if self.state == "RETURN_TO_BASE":
            hx, hy = config.HOME_BASE_COORD
            dx, dy = hx - self.body.position.x, hy - self.body.position.y
            if math.sqrt(dx**2 + dy**2) < 20 and self.state_timer <= 0:
                self.state = "RETURNING_TO_TARGET"
                self.state_timer = 60
                
        elif self.state == "RETURNING_TO_TARGET":
            if self.active_joint:
                self.state = "RETRIEVING"
                
        elif self.state == "SEARCHING":
            if self.vision_query(target_body):
                self.state = "INTERCEPT_TARGET"
                self.state_timer = 60
            else:
                help_mag = math.sqrt(help_vec[0]**2 + help_vec[1]**2)
                if help_mag > 0.05 and self.state_timer <= 0:
                    self.state = "INTERCEPT_TARGET"
                    self.state_timer = 60
                else:
                    home_mag = math.sqrt(home_vec[0]**2 + home_vec[1]**2)
                    if home_mag > 0.05 and self.state_timer <= 0:
                        self.state = "INTERCEPT_TARGET"
                        self.state_timer = 60
                    
        elif self.state == "INTERCEPT_TARGET":
            if self.active_joint:
                self.state = "RETRIEVING"
                self.state_timer = 60
            elif self.state_timer <= 0:
                if not self.vision_query(target_body):
                    help_mag = math.sqrt(help_vec[0]**2 + help_vec[1]**2)
                    home_mag = math.sqrt(home_vec[0]**2 + home_vec[1]**2)
                    if home_mag < 0.05 and help_mag < 0.05:
                        self.state = "SEARCHING" # Lost track
                        self.state_timer = 60
                        
        elif self.state == "RETRIEVING":
            if not self.active_joint and self.state_timer <= 0:
                self.state = "SEARCHING"
                self.state_timer = 60
            else:
                num_attached = max(1, len([a for a in all_agents if getattr(a, 'active_joint', None)]))
                if num_attached < 3:
                    if not hasattr(self, 'force_effort_timer'):
                        self.force_effort_timer = 0
                    self.force_effort_timer += 1
                    if self.force_effort_timer > 180: # 3 seconds
                        self.state = "RETURN_TO_BASE"
                        self.state_timer = 60
                        if self.active_joint:
                            self.space.remove(self.active_joint)
                            self.active_joint = None
                        self.force_effort_timer = 0
                else:
                    self.force_effort_timer = 0

        # --- 2. Movement Vector Calculation ---
        hx, hy = config.HOME_BASE_COORD
        
        if self.state == "RETURN_TO_BASE":
            dx, dy = hx - self.body.position.x, hy - self.body.position.y
            mag = math.sqrt(dx**2 + dy**2)
            if mag > 0:
                force_x = (dx/mag) * self.max_speed
                force_y = (dy/mag) * self.max_speed
                
        elif self.state == "RETURNING_TO_TARGET":
            visible_target = self.vision_query(target_body)
            if visible_target:
                dx = visible_target.position.x - self.body.position.x
                dy = visible_target.position.y - self.body.position.y
                mag = math.sqrt(dx**2 + dy**2)
                if mag > 0:
                    force_x = (dx/mag) * self.max_speed
                    force_y = (dy/mag) * self.max_speed
            else:
                help_mag = math.sqrt(help_vec[0]**2 + help_vec[1]**2)
                if help_mag > 0:
                    force_x = help_vec[0] * self.max_speed * 2
                    force_y = help_vec[1] * self.max_speed * 2
                else:
                    self.state = "SEARCHING"
                    self.state_timer = 60
            
        elif self.state == "SEARCHING":
            # Persistent Heading (No Spontaneous Jitter)
            self.heading += random.uniform(-0.1, 0.1) # Smooth curve
            
            # Spawn-Zone Bias: Only at t < 5 seconds, clear the spawn zone
            if not hasattr(self, 'life_timer'):
                self.life_timer = 0
            self.life_timer += 1
            if self.life_timer < 300: # 5 seconds at 60 FPS
                target_heading = math.pi
                diff = (target_heading - self.heading + math.pi) % (2*math.pi) - math.pi
                self.heading += diff * 0.05
                
            heading_x = math.cos(self.heading) * self.max_speed
            heading_y = math.sin(self.heading) * self.max_speed
            
            # Global Nav Weight is 0.0 during SEARCHING to allow pure exploration
            force_x = heading_x
            force_y = heading_y
            
        elif self.state == "INTERCEPT_TARGET":
            visible_target = self.vision_query(target_body)
            if visible_target:
                # ATTRACT_TO_TARGET Vector
                dx = visible_target.position.x - self.body.position.x
                dy = visible_target.position.y - self.body.position.y
                mag = math.sqrt(dx**2 + dy**2)
                if mag > 0:
                    force_x = (dx/mag) * self.max_speed
                    force_y = (dy/mag) * self.max_speed
            else:
                # Follow Pheromone Gradient (Layer 2 or 1)
                help_mag = math.sqrt(help_vec[0]**2 + help_vec[1]**2)
                if help_mag > 0.05:
                    force_x = help_vec[0] * self.max_speed * 2
                    force_y = help_vec[1] * self.max_speed * 2
                else:
                    force_x = -home_vec[0] * self.max_speed * 2
                    force_y = -home_vec[1] * self.max_speed * 2
                
        elif self.state == "RETRIEVING":
            # Attached: Pull target directly towards HOME_BASE_COORD (Weight = 1.0)
            dx, dy = hx - self.body.position.x, hy - self.body.position.y
            mag = math.sqrt(dx**2 + dy**2)
            
            num_attached = max(1, len([a for a in all_agents if getattr(a, 'active_joint', None)]))
            push_mag = (config.AGENT_MAX_SPEED * 10) / num_attached
            
            if mag > 0:
                force_x = (dx/mag) * push_mag
                force_y = (dy/mag) * push_mag
            
            # CVT Repulsion
            rep_x, rep_y = 0.0, 0.0
            sense_radius = config.AGENT_RADIUS * 4
            for neighbor in all_agents:
                if neighbor is not self and getattr(neighbor, 'active_joint', None):
                    ndx = self.body.position.x - neighbor.body.position.x
                    ndy = self.body.position.y - neighbor.body.position.y
                    dist = math.sqrt(ndx**2 + ndy**2)
                    if 0 < dist < sense_radius:
                        weight = 100.0 / (dist**2)
                        rep_x += ndx * weight
                        rep_y += ndy * weight
            
            force_x += rep_x
            force_y += rep_y

        # Clamp force to max speed
        magnitude = math.sqrt(force_x**2 + force_y**2)
        if magnitude > self.max_speed:
            scale = self.max_speed / magnitude
            force_x *= scale
            force_y *= scale
            
        # Apply force to center of mass
        self.body.apply_force_at_local_point((force_x, force_y), (0, 0))
