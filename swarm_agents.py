# swarm_agents.py
import pymunk
import random
import math
import config

class Agent:
    def __init__(self, space, position):
        self.space = space
        # Infinite moment of inertia prevents physics collisions from spinning the agent
        self.body = pymunk.Body(config.AGENT_MASS, float('inf'))
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
        self.life_timer = 0
        self.force_effort_timer = 0
        self.carry_joint = None
        self.carried_body = None

        # For correlated random walk
        self.heading = random.uniform(0, 2 * math.pi)
        
    VISION_RADIUS = 200  # px — distance to target CoM at which agent switches to INTERCEPT
    SMALL_VISION_RADIUS = 80  # px — range at which agent notices a small object

    def vision_query(self, target_body):
        """Returns target_body if it is within VISION_RADIUS, else None."""
        dx = self.body.position.x - target_body.position.x
        dy = self.body.position.y - target_body.position.y
        return target_body if math.sqrt(dx**2 + dy**2) < self.VISION_RADIUS else None

    def nearest_small_object(self, small_objects):
        """Returns the nearest uncarried small object within SMALL_VISION_RADIUS, or None."""
        best, best_dist = None, self.SMALL_VISION_RADIUS
        for body in small_objects:
            if getattr(body, 'carried', False):
                continue
            dx = body.position.x - self.body.position.x
            dy = body.position.y - self.body.position.y
            d = math.sqrt(dx**2 + dy**2)
            if d < best_dist:
                best, best_dist = body, d
        return best

    def _detach(self):
        """Severs the active PivotJoint if one exists."""
        if self.active_joint:
            self.space.remove(self.active_joint)
            self.active_joint = None

    def apply_movement_logic(self, local_pheromone_gradient, target_body, all_agents, small_objects=None):
        """Determines the agent's velocity based on stigmergy principles."""
        if small_objects is None:
            small_objects = []
        search_vec, home_vec, help_vec = local_pheromone_gradient
        vx, vy = 0.0, 0.0

        if self.state_timer > 0:
            self.state_timer -= 1

        # ------------------------------------------------------------------ #
        # 1. State Transitions                                                 #
        # ------------------------------------------------------------------ #
        if self.state == "SEARCHING":
            # Main payload takes priority over small objects
            if self.vision_query(target_body):
                self.state = "INTERCEPT_TARGET"
                self.state_timer = 90
            else:
                help_mag = math.sqrt(help_vec[0]**2 + help_vec[1]**2)
                home_mag = math.sqrt(home_vec[0]**2 + home_vec[1]**2)
                if (help_mag > 0.05 or home_mag > 0.05) and self.state_timer <= 0:
                    self.state = "INTERCEPT_TARGET"
                    self.state_timer = 90
                elif self.nearest_small_object(small_objects) and self.state_timer <= 0:
                    self.state = "INTERCEPT_SMALL"
                    self.state_timer = 90

        elif self.state == "INTERCEPT_SMALL":
            # Drop small object pursuit if main payload comes into view
            if self.vision_query(target_body):
                self.state = "INTERCEPT_TARGET"
                self.state_timer = 90
            elif self.carry_joint:
                self.state = "CARRYING"
            elif self.state_timer <= 0 and not self.nearest_small_object(small_objects):
                self.state = "SEARCHING"
                self.state_timer = 60

        elif self.state == "CARRYING":
            # Delivery is handled by simulation_manager; nothing to check here
            pass

        elif self.state == "INTERCEPT_TARGET":
            if self.active_joint:
                self.state = "RETRIEVING"
                self.state_timer = 0
            elif self.state_timer <= 0 and not self.vision_query(target_body):
                help_mag = math.sqrt(help_vec[0]**2 + help_vec[1]**2)
                home_mag = math.sqrt(home_vec[0]**2 + home_vec[1]**2)
                if help_mag < 0.05 and home_mag < 0.05:
                    self.state = "SEARCHING"
                    self.state_timer = 60

        elif self.state == "RETRIEVING":
            if not self.active_joint and self.state_timer <= 0:
                self.state = "SEARCHING"
                self.state_timer = 60
            else:
                num_attached = len([a for a in all_agents if a.active_joint])
                if num_attached < 3:
                    self.force_effort_timer += 1
                    if self.force_effort_timer > 180:
                        self._detach()
                        self.state = "RETURN_TO_BASE"
                        self.state_timer = 60
                        self.force_effort_timer = 0
                else:
                    self.force_effort_timer = 0

        elif self.state == "SHUFFLING":
            if self.state_timer <= 0:
                # Done shuffling — try to re-engage the target
                self.state = "INTERCEPT_TARGET"
                self.state_timer = 90

        elif self.state == "RETURN_TO_BASE":
            hx, hy = config.HOME_BASE_COORD
            dx, dy = hx - self.body.position.x, hy - self.body.position.y
            if math.sqrt(dx**2 + dy**2) < 20 and self.state_timer <= 0:
                self.state = "RETURNING_TO_TARGET"
                self.state_timer = 60

        elif self.state == "RETURNING_TO_TARGET":
            if self.active_joint:
                self.state = "RETRIEVING"
            elif self.state_timer <= 0 and not self.vision_query(target_body):
                self.state = "SEARCHING"
                self.state_timer = 60

        # ------------------------------------------------------------------ #
        # 2. Movement                                                          #
        # ------------------------------------------------------------------ #
        hx, hy = config.HOME_BASE_COORD

        if self.state == "SEARCHING":
            # Correlated random walk — gentle heading drift, no spontaneous spins
            self.life_timer += 1
            self.heading += random.uniform(-0.03, 0.03)

            # First 5 s: nudge heading leftward to clear the home zone
            if self.life_timer < 300:
                target_h = math.pi
                diff = (target_h - self.heading + math.pi) % (2 * math.pi) - math.pi
                self.heading += diff * 0.05

            vx = math.cos(self.heading) * self.max_speed
            vy = math.sin(self.heading) * self.max_speed

        elif self.state == "INTERCEPT_TARGET":
            visible = self.vision_query(target_body)
            if visible:
                dx = visible.position.x - self.body.position.x
                dy = visible.position.y - self.body.position.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    # Slow down as we get close so we don't overshoot
                    approach_speed = min(self.max_speed, self.max_speed * (dist / self.VISION_RADIUS) + 10)
                    vx = (dx / dist) * approach_speed
                    vy = (dy / dist) * approach_speed
            else:
                help_mag = math.sqrt(help_vec[0]**2 + help_vec[1]**2)
                if help_mag > 0.05:
                    vx = (help_vec[0] / help_mag) * self.max_speed
                    vy = (help_vec[1] / help_mag) * self.max_speed
                else:
                    home_mag = math.sqrt(home_vec[0]**2 + home_vec[1]**2)
                    if home_mag > 0.05:
                        vx = -(home_vec[0] / home_mag) * self.max_speed
                        vy = -(home_vec[1] / home_mag) * self.max_speed

        elif self.state == "RETRIEVING":
            dx, dy = hx - self.body.position.x, hy - self.body.position.y
            mag = math.sqrt(dx**2 + dy**2)
            num_attached = max(1, len([a for a in all_agents if a.active_joint]))
            push_mag = (self.max_speed * 10) / num_attached

            if mag > 0:
                vx = (dx / mag) * push_mag
                vy = (dy / mag) * push_mag

            # CVT repulsion among attached agents
            sense_r = config.AGENT_RADIUS * 4
            for neighbor in all_agents:
                if neighbor is not self and neighbor.active_joint:
                    ndx = self.body.position.x - neighbor.body.position.x
                    ndy = self.body.position.y - neighbor.body.position.y
                    d = math.sqrt(ndx**2 + ndy**2)
                    if 0 < d < sense_r:
                        w = 100.0 / (d**2)
                        vx += ndx * w
                        vy += ndy * w

        elif self.state == "SHUFFLING":
            # Orbital component: tangent to the circle around the target
            tx, ty = target_body.position.x, target_body.position.y
            dx, dy = self.body.position.x - tx, self.body.position.y - ty
            dist = math.sqrt(dx**2 + dy**2)
            if dist > 0:
                # Tangent vector (perpendicular, consistent direction = counter-clockwise)
                orbital_x = -dy / dist
                orbital_y =  dx / dist
            else:
                orbital_x, orbital_y = 1.0, 0.0

            # Random component
            rand_x = random.uniform(-1, 1)
            rand_y = random.uniform(-1, 1)
            rand_mag = math.sqrt(rand_x**2 + rand_y**2)
            if rand_mag > 0:
                rand_x /= rand_mag
                rand_y /= rand_mag

            r = config.SHUFFLE_RANDOMNESS
            blend_x = (1 - r) * orbital_x + r * rand_x
            blend_y = (1 - r) * orbital_y + r * rand_y

            vx = blend_x * self.max_speed
            vy = blend_y * self.max_speed

        elif self.state == "INTERCEPT_SMALL":
            target_small = self.nearest_small_object(small_objects)
            if target_small:
                dx = target_small.position.x - self.body.position.x
                dy = target_small.position.y - self.body.position.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    approach_speed = min(self.max_speed, self.max_speed * (dist / self.SMALL_VISION_RADIUS) + 10)
                    vx = (dx / dist) * approach_speed
                    vy = (dy / dist) * approach_speed

        elif self.state == "CARRYING":
            # Drag small object straight home
            dx, dy = hx - self.body.position.x, hy - self.body.position.y
            mag = math.sqrt(dx**2 + dy**2)
            if mag > 0:
                vx = (dx / mag) * self.max_speed
                vy = (dy / mag) * self.max_speed

        elif self.state == "RETURN_TO_BASE":
            dx, dy = hx - self.body.position.x, hy - self.body.position.y
            mag = math.sqrt(dx**2 + dy**2)
            if mag > 0:
                vx = (dx / mag) * self.max_speed
                vy = (dy / mag) * self.max_speed

        elif self.state == "RETURNING_TO_TARGET":
            visible = self.vision_query(target_body)
            if visible:
                dx = visible.position.x - self.body.position.x
                dy = visible.position.y - self.body.position.y
                dist = math.sqrt(dx**2 + dy**2)
                if dist > 0:
                    vx = (dx / dist) * self.max_speed
                    vy = (dy / dist) * self.max_speed
            else:
                help_mag = math.sqrt(help_vec[0]**2 + help_vec[1]**2)
                if help_mag > 0.05:
                    vx = (help_vec[0] / help_mag) * self.max_speed
                    vy = (help_vec[1] / help_mag) * self.max_speed
                else:
                    self.state = "SEARCHING"
                    self.state_timer = 60

        # Clamp to max speed
        speed = math.sqrt(vx**2 + vy**2)
        if speed > self.max_speed:
            vx = vx / speed * self.max_speed
            vy = vy / speed * self.max_speed

        # Set velocity directly — avoids force accumulation drift
        self.body.velocity = (vx, vy)
