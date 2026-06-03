# visualizer.py
import pygame
import pymunk
import pymunk.pygame_util
import config
import math

class Visualizer:
    def __init__(self, space, pheromones):
        pygame.init()
        self.width = config.ARENA_WIDTH
        self.height = config.ARENA_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Swarm Robotics Simulation - Mechanical Stigmergy")
        
        self.space = space
        self.pheromones = pheromones
        
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        
        self.font = pygame.font.SysFont("Arial", 16)
        
        self.show_pheromones = True
        self.paused = False
        
    def handle_events(self):
        """Handle keyboard and window events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False # Signal to quit
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_v:
                    self.show_pheromones = not self.show_pheromones
        return True

    def _draw_pheromones(self):
        """Draw the vector pheromone grid as a heatmap."""
        if not self.show_pheromones:
            return
            
        cell_size = self.pheromones.cell_size
        rows, cols, _ = self.pheromones.grid.shape
        
        heatmap_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for r in range(rows):
            for c in range(cols):
                vx, vy = self.pheromones.grid[r, c, 0], self.pheromones.grid[r, c, 1]
                magnitude = math.sqrt(vx**2 + vy**2)
                
                if magnitude > 0.01:
                    # Normalize alpha based on magnitude
                    alpha = min(255, int(magnitude * 50))
                    color = (255, 255, 0, alpha) # Yellow heat
                    rect = (c * cell_size, r * cell_size, cell_size, cell_size)
                    pygame.draw.rect(heatmap_surface, color, rect)
                    
        self.screen.blit(heatmap_surface, (0, 0))
        
    def _draw_agents(self, agents):
        """Draw agents with color coding based on state."""
        for agent in agents:
            pos = int(agent.body.position.x), int(agent.body.position.y)
            color = (0, 255, 0) if agent.state == "SEARCHING" else (0, 100, 255)
            pygame.draw.circle(self.screen, color, pos, config.AGENT_RADIUS)
            
            # Heading line
            angle = agent.body.angle
            end_pos = (pos[0] + config.AGENT_RADIUS * math.cos(angle),
                       pos[1] + config.AGENT_RADIUS * math.sin(angle))
            pygame.draw.line(self.screen, (0,0,0), pos, end_pos, 2)

    def update(self, agents, timer):
        """Render a single frame."""
        self.screen.fill((240, 240, 240)) # Light gray background
        
        # 1. Stigmergy Layer (Pheromones)
        self._draw_pheromones()
        
        # 2. Physics Layer (Walls and Target Shapes)
        self.space.debug_draw(self.draw_options)
        
        # 3. Agent Layer
        self._draw_agents(agents)
        
        # 4. HUD
        time_text = self.font.render(f"Time: {timer:.2f}s", True, (0, 0, 0))
        state_text = self.font.render(f"Paused: {self.paused} | Pheromones (V): {self.show_pheromones}", True, (0,0,0))
        self.screen.blit(time_text, (10, 10))
        self.screen.blit(state_text, (10, 30))
        
        pygame.display.flip()
