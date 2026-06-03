# physics_engine.py
import pymunk
import config

class PhysicsEngine:
    def __init__(self):
        # Create pymunk space
        self.space = pymunk.Space()
        self.space.damping = config.DAMPING # Simulate friction/drag
        self.target_body = None
        
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
        
        # Central wall with gap (split arena vertically)
        mid_x = width / 2
        gap_start_y = (height / 2) - (gap_size / 2)
        gap_end_y = (height / 2) + (gap_size / 2)
        
        central_walls = [
            pymunk.Segment(static_body, (mid_x, 0), (mid_x, gap_start_y), wall_thickness),
            pymunk.Segment(static_body, (mid_x, gap_end_y), (mid_x, height), wall_thickness)
        ]
        
        for wall in boundaries + central_walls:
            wall.elasticity = config.ELASTICITY
            wall.friction = config.FRICTION
            self.space.add(wall)

    def spawn_target_shape(self, shape_type, position, mass=10.0):
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
            
        self.space.add(body, *shapes)
        self.target_body = body
        return body

    def step(self, dt):
        """Advances the physics simulation by dt seconds."""
        self.space.step(dt)
