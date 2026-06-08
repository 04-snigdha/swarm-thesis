import pymunk
import config
import math

def agent_small_post_solve(arbiter, space, data):
    """Latch an agent onto a small object when they collide."""
    shape_a, shape_b = arbiter.shapes
    if shape_a.collision_type == config.COLLISION_TYPE_AGENT:
        agent_shape, small_shape = shape_a, shape_b
    else:
        agent_shape, small_shape = shape_b, shape_a

    agent = getattr(agent_shape, 'agent', None)
    if not agent:
        return

    # Only latch if agent is actively intercepting this small object and not already carrying
    if agent.state != "INTERCEPT_SMALL" or agent.carry_joint:
        return

    # Don't grab an object already being carried by another agent
    if getattr(small_shape.body, 'carried', False):
        return

    small_shape.body.carried = True
    agent.carried_body = small_shape.body

    if len(arbiter.contact_point_set.points) > 0:
        contact = arbiter.contact_point_set.points[0].point_a
        anchor = small_shape.body.world_to_local(contact)
        joint = pymunk.PivotJoint(agent.body, small_shape.body, (0, 0), anchor)
        joint.max_force = 5000
        space.add(joint)
        agent.carry_joint = joint
        agent.state = "CARRYING"


def agent_target_post_solve(arbiter, space, data):
    # Determine which shape is the agent and which is the target
    shape_a, shape_b = arbiter.shapes
    if shape_a.collision_type == config.COLLISION_TYPE_AGENT:
        agent_shape, target_shape = shape_a, shape_b
    else:
        agent_shape, target_shape = shape_b, shape_a

    agent = getattr(agent_shape, 'agent', None)

    if agent and not getattr(agent, 'active_joint', None):
        # Upon contact with Target, switches to RETRIEVING
        agent.state = "RETRIEVING"
        
        target_body = target_shape.body
        
        # Create a PivotJoint at the contact point
        if len(arbiter.contact_point_set.points) > 0:
            contact = arbiter.contact_point_set.points[0].point_a
            anchor_on_target = target_body.world_to_local(contact)
            
            # (a, b, anchor_a, anchor_b)
            joint = pymunk.PivotJoint(agent.body, target_body, (0, 0), anchor_on_target)
            joint.max_force = 1500  # limited grip — heavy payload needs many ants
            space.add(joint)
            agent.active_joint = joint

class PhysicsEngine:
    def __init__(self):
        # Create pymunk space
        self.space = pymunk.Space()
        self.space.damping = config.DAMPING # Simulate friction/drag
        self.target_body = None
        
        self.space.on_collision(config.COLLISION_TYPE_AGENT, config.COLLISION_TYPE_TARGET, post_solve=agent_target_post_solve)
        self.space.on_collision(config.COLLISION_TYPE_AGENT, config.COLLISION_TYPE_SMALL, post_solve=agent_small_post_solve)
        
    def generate_walls(self, width=config.ARENA_WIDTH, height=config.ARENA_HEIGHT, gap_size=config.GAP_WIDTH, wall_thickness=config.WALL_THICKNESS):
        """Generates the static arena boundaries with a central wall that has a gap."""
        static_body = self.space.static_body
        
        # Outer boundaries (Top, Bottom, Left, Right)
        boundaries = [
            pymunk.Segment(static_body, (0, 0), (width, 0), wall_thickness),
            pymunk.Segment(static_body, (0, height), (width, height), wall_thickness),
            pymunk.Segment(static_body, (0, 0), (0, height), wall_thickness),
            pymunk.Segment(static_body, (width, 0), (width, height), wall_thickness)
        ]
        
        # Central wall with one payload gap (centre) and two narrow ant passages
        mid_x = width / 2
        gap_start_y = (height / 2) - (gap_size / 2)
        gap_end_y   = (height / 2) + (gap_size / 2)

        p = config.ANT_PASSAGE_WIDTH / 2
        # Ant passage 1: ~20 % down the wall (y ≈ 160)
        ap1 = height * 0.20
        # Ant passage 2: ~80 % down the wall (y ≈ 640)
        ap2 = height * 0.80

        central_walls = [
            # Upper section — split by ant passage 1
            pymunk.Segment(static_body, (mid_x, 0),          (mid_x, ap1 - p), wall_thickness),
            pymunk.Segment(static_body, (mid_x, ap1 + p),    (mid_x, gap_start_y), wall_thickness),
            # Lower section — split by ant passage 2
            pymunk.Segment(static_body, (mid_x, gap_end_y),  (mid_x, ap2 - p), wall_thickness),
            pymunk.Segment(static_body, (mid_x, ap2 + p),    (mid_x, height),  wall_thickness),
        ]
        
        for wall in boundaries + central_walls:
            wall.elasticity = config.ELASTICITY
            wall.friction = config.FRICTION
            self.space.add(wall)

    def spawn_target_shape(self, shape_type, position, mass=config.TARGET_MASS):
        """Spawns a dynamic target shape for the swarm to manipulate."""
        if shape_type == "Circle":
            radius = 30
            moment = pymunk.moment_for_circle(mass, 0, radius)
            body = pymunk.Body(mass, moment)
            body.position = position
            shape = pymunk.Circle(body, radius)
            shapes = [shape]
            
        elif shape_type == "Square":
            size = (60, 60)
            moment = pymunk.moment_for_box(mass, size)
            body = pymunk.Body(mass, moment)
            body.position = position
            shape = pymunk.Poly.create_box(body, size)
            shapes = [shape]
            
        elif shape_type == "L-shape":
            # Compound shape
            vertices = [(0,0), (20,0), (20,60), (60,60), (60,80), (0,80)]
            # Translate vertices to be centered around (0,0) for better physics behavior
            centroid = sum([v[0] for v in vertices])/len(vertices), sum([v[1] for v in vertices])/len(vertices)
            centered_verts = [(v[0]-centroid[0], v[1]-centroid[1]) for v in vertices]
            
            moment = pymunk.moment_for_poly(mass, centered_verts)
            body = pymunk.Body(mass, moment)
            body.position = position
            
            shape1 = pymunk.Poly(body, [(0-centroid[0], 0-centroid[1]), (20-centroid[0], 0-centroid[1]), (20-centroid[0], 80-centroid[1]), (0-centroid[0], 80-centroid[1])])
            shape2 = pymunk.Poly(body, [(20-centroid[0], 60-centroid[1]), (60-centroid[0], 60-centroid[1]), (60-centroid[0], 80-centroid[1]), (20-centroid[0], 80-centroid[1])])
            shapes = [shape1, shape2]
            
        elif shape_type == "C-shape":
            # Compound shape
            vertices = [(0,0), (60,0), (60,20), (20,20), (20,60), (60,60), (60,80), (0,80)]
            centroid = sum([v[0] for v in vertices])/len(vertices), sum([v[1] for v in vertices])/len(vertices)
            
            moment = pymunk.moment_for_poly(mass, [(v[0]-centroid[0], v[1]-centroid[1]) for v in vertices])
            body = pymunk.Body(mass, moment)
            body.position = position
            
            shape1 = pymunk.Poly(body, [(0-centroid[0], 0-centroid[1]), (20-centroid[0], 0-centroid[1]), (20-centroid[0], 80-centroid[1]), (0-centroid[0], 80-centroid[1])])
            shape2 = pymunk.Poly(body, [(20-centroid[0], 0-centroid[1]), (60-centroid[0], 0-centroid[1]), (60-centroid[0], 20-centroid[1]), (20-centroid[0], 20-centroid[1])])
            shape3 = pymunk.Poly(body, [(20-centroid[0], 60-centroid[1]), (60-centroid[0], 60-centroid[1]), (60-centroid[0], 80-centroid[1]), (20-centroid[0], 80-centroid[1])])
            shapes = [shape1, shape2, shape3]
            
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")
            
        for s in shapes:
            s.elasticity = config.ELASTICITY
            s.friction = config.FRICTION
            s.collision_type = config.COLLISION_TYPE_TARGET
            
        self.space.add(body, *shapes)
        self.target_body = body
        return body

    def spawn_scattered_objects(self, count=config.SMALL_OBJECT_COUNT):
        """Spawns small foraging objects randomly across the full arena."""
        import random
        margin = config.WALL_THICKNESS + config.SMALL_OBJECT_RADIUS + 5
        bodies = []
        for _ in range(count):
            x = random.uniform(margin, config.ARENA_WIDTH - margin)
            y = random.uniform(margin, config.ARENA_HEIGHT - margin)
            body = pymunk.Body(config.SMALL_OBJECT_MASS, float('inf'))
            body.position = (x, y)
            body.carried = False
            shape = pymunk.Circle(body, config.SMALL_OBJECT_RADIUS)
            shape.elasticity = config.ELASTICITY
            shape.friction = config.FRICTION
            shape.collision_type = config.COLLISION_TYPE_SMALL
            self.space.add(body, shape)
            bodies.append(body)
        return bodies

    def spawn_small_objects(self, count=config.SMALL_OBJECT_COUNT, zone=None):
        """Spawns small foraging objects randomly inside zone (defaults to FORAGE_ZONE)."""
        import random
        fx, fy, fw, fh = zone if zone else config.FORAGE_ZONE
        bodies = []
        for _ in range(count):
            x = random.uniform(fx + config.SMALL_OBJECT_RADIUS, fx + fw - config.SMALL_OBJECT_RADIUS)
            y = random.uniform(fy + config.SMALL_OBJECT_RADIUS, fy + fh - config.SMALL_OBJECT_RADIUS)
            body = pymunk.Body(config.SMALL_OBJECT_MASS, float('inf'))
            body.position = (x, y)
            body.carried = False
            shape = pymunk.Circle(body, config.SMALL_OBJECT_RADIUS)
            shape.elasticity = config.ELASTICITY
            shape.friction = config.FRICTION
            shape.collision_type = config.COLLISION_TYPE_SMALL
            self.space.add(body, shape)
            bodies.append(body)
        return bodies

    def step(self, dt):
        """Advances the physics simulation by dt seconds."""
        if self.target_body:
            # Simulate viscosity of the environment
            self.target_body.angular_velocity *= 0.95
            self.target_body.velocity = self.target_body.velocity * 0.98
        self.space.step(dt)
