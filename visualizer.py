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
        """Draw the vector pheromone grid as arrows."""
        if not self.show_pheromones:
            return
            
        cell_size = self.pheromones.cell_size
        rows, cols, _, _ = self.pheromones.grid.shape
        
        for r in range(rows):
            for c in range(cols):
                cx = c * cell_size + cell_size / 2
                cy = r * cell_size + cell_size / 2
                
                # Layer 0 (Search Vector) - Red
                svx, svy = self.pheromones.grid[r, c, 0, 0], self.pheromones.grid[r, c, 0, 1]
                smag = math.sqrt(svx**2 + svy**2)
                if smag > 0.05:
                    end_x = cx + (svx/smag) * cell_size
                    end_y = cy + (svy/smag) * cell_size
                    pygame.draw.line(self.screen, (255, 0, 0), (cx, cy), (end_x, end_y), 1)
                    
                # Layer 1 (Home Vector) - Blue
                hvx, hvy = self.pheromones.grid[r, c, 1, 0], self.pheromones.grid[r, c, 1, 1]
                hmag = math.sqrt(hvx**2 + hvy**2)
                if hmag > 0.05:
                    end_x = cx + (hvx/hmag) * cell_size
                    end_y = cy + (hvy/hmag) * cell_size
                    pygame.draw.line(self.screen, (0, 0, 255), (cx, cy), (end_x, end_y), 2)
                    
                # Layer 2 (Help-Signal Vector) - Purple
                helpvx, helpvy = self.pheromones.grid[r, c, 2, 0], self.pheromones.grid[r, c, 2, 1]
                helpmag = math.sqrt(helpvx**2 + helpvy**2)
                if helpmag > 0.05:
                    end_x = cx + (helpvx/helpmag) * cell_size
                    end_y = cy + (helpvy/helpmag) * cell_size
                    pygame.draw.line(self.screen, (128, 0, 128), (cx, cy), (end_x, end_y), 3)
                    
    def _draw_zones(self):
        """Draws faint rectangles for Home and Forage zones."""
        zone_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Forage Zone (Red)
        fx, fy, fw, fh = config.FORAGE_ZONE
        pygame.draw.rect(zone_surface, (255, 0, 0, 30), (fx, fy, fw, fh))
        
        # Home Zone (Green)
        hx, hy, hw, hh = config.HOME_ZONE
        pygame.draw.rect(zone_surface, (0, 255, 0, 30), (hx, hy, hw, hh))
        
        self.screen.blit(zone_surface, (0, 0))
        
    def _draw_agents(self, agents):
        """Draw agents with color coding based on state."""
        for agent in agents:
            pos = int(agent.body.position.x), int(agent.body.position.y)
            if agent.state == "SEARCHING":
                color = (0, 255, 0)
            elif agent.state == "RETURN_TO_BASE":
                color = (255, 165, 0) # Orange
            elif agent.state == "RETURNING_TO_TARGET":
                color = (128, 0, 128) # Purple
            else:
                color = (0, 100, 255) # Retrieving / Intercepting
            pygame.draw.circle(self.screen, color, pos, config.AGENT_RADIUS)
            
            # Heading line
            angle = agent.body.angle
            end_pos = (pos[0] + config.AGENT_RADIUS * math.cos(angle),
                       pos[1] + config.AGENT_RADIUS * math.sin(angle))
            pygame.draw.line(self.screen, (0,0,0), pos, end_pos, 2)

    def update(self, agents, timer):
        """Render a single frame."""
        self.screen.fill((240, 240, 240)) # Light gray background
        
        # 0. Spatial Zones
        self._draw_zones()
        
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
