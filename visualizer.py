# visualizer.py
import pygame
import pymunk
import pymunk.pygame_util
import config
import math


class Visualizer:
    def __init__(self, space, pheromones):
        pygame.init()
        self.sim_w = config.ARENA_WIDTH
        self.sim_h = config.ARENA_HEIGHT
        self.hud_w = config.HUD_WIDTH
        self.screen = pygame.display.set_mode((self.sim_w + self.hud_w, self.sim_h))
        pygame.display.set_caption("Swarm Robotics Simulation - Mechanical Stigmergy")

        self.space = space
        self.pheromones = pheromones
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)

        self.font   = pygame.font.SysFont("Arial", 17)
        self.font_b = pygame.font.SysFont("Arial", 17, bold=True)
        self.font_s = pygame.font.SysFont("Arial", 14)

        self.show_pheromones = True
        self.paused = False

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_v:
                    self.show_pheromones = not self.show_pheromones
        return True

    # ------------------------------------------------------------------
    # Simulation-grid drawing helpers
    # ------------------------------------------------------------------
    def _draw_pheromones(self):
        if not self.show_pheromones:
            return
        cell = self.pheromones.cell_size
        rows, cols, _, _ = self.pheromones.grid.shape
        for r in range(rows):
            for c in range(cols):
                cx = c * cell + cell / 2
                cy = r * cell + cell / 2

                hvx, hvy = self.pheromones.grid[r, c, 1, 0], self.pheromones.grid[r, c, 1, 1]
                hmag = math.sqrt(hvx**2 + hvy**2)
                if hmag > 0.05:
                    ex = cx + (hvx / hmag) * cell
                    ey = cy + (hvy / hmag) * cell
                    pygame.draw.line(self.screen, (0, 0, 220), (cx, cy), (ex, ey), 2)

                helpvx, helpvy = self.pheromones.grid[r, c, 2, 0], self.pheromones.grid[r, c, 2, 1]
                helpmag = math.sqrt(helpvx**2 + helpvy**2)
                if helpmag > 0.05:
                    ex = cx + (helpvx / helpmag) * cell
                    ey = cy + (helpvy / helpmag) * cell
                    pygame.draw.line(self.screen, (140, 0, 160), (cx, cy), (ex, ey), 3)

    def _draw_zones(self):
        # Only show the HOME target marker — no zone rectangles
        hbx, hby = config.HOME_BASE_COORD
        pygame.draw.circle(self.screen, (0, 180, 0), (hbx, hby), 10)
        pygame.draw.circle(self.screen, (0, 180, 0), (hbx, hby), 50, 2)
        lf = pygame.font.SysFont("Arial", 13, bold=True)
        self.screen.blit(lf.render("HOME", True, (0, 140, 0)), (hbx - 14, hby + 14))

    def _draw_agents(self, agents):
        STATE_COL = {
            "SEARCHING":          (0, 200, 0),
            "INTERCEPT_TARGET":   (0, 200, 255),
            "INTERCEPT_SMALL":    (255, 100, 160),   # pink
            "CARRYING":           (140, 80,  40),    # brown
            "RETRIEVING":         (0, 80, 255),
            "SHUFFLING":          (255, 220, 0),
            "RETURN_TO_BASE":     (255, 140, 0),
            "RETURNING_TO_TARGET":(180, 0, 220),
        }
        for agent in agents:
            pos = int(agent.body.position.x), int(agent.body.position.y)
            color = STATE_COL.get(agent.state, (160, 160, 160))
            pygame.draw.circle(self.screen, color, pos, config.AGENT_RADIUS)
            angle = agent.body.angle
            ep = (pos[0] + config.AGENT_RADIUS * math.cos(angle),
                  pos[1] + config.AGENT_RADIUS * math.sin(angle))
            pygame.draw.line(self.screen, (0, 0, 0), pos, ep, 2)

    def _draw_small_objects(self, small_objects):
        for body in small_objects:
            pos = int(body.position.x), int(body.position.y)
            color = (255, 200, 0) if getattr(body, 'carried', False) else (180, 140, 0)
            pygame.draw.circle(self.screen, color, pos, config.SMALL_OBJECT_RADIUS)

    # ------------------------------------------------------------------
    # HUD sidebar
    # ------------------------------------------------------------------
    def _draw_hud(self, agents, timer, target_body):
        from collections import Counter

        sc = Counter(a.state for a in agents)
        attached = sum(1 for a in agents if a.active_joint)
        total = len(agents)

        # Payload distance to home
        if target_body:
            hbx, hby = config.HOME_BASE_COORD
            dx = target_body.position.x - hbx
            dy = target_body.position.y - hby
            dist = math.sqrt(dx**2 + dy**2)
            dist_str  = f"{dist:.0f} px"
            delivered = dist < 50
        else:
            dist_str  = "—"
            delivered = False

        # --- Panel background ---
        px = self.sim_w + 1          # left edge of sidebar
        pygame.draw.rect(self.screen, (30, 30, 40), (px, 0, self.hud_w, self.sim_h))
        pygame.draw.line(self.screen, (80, 80, 100), (px, 0), (px, self.sim_h), 2)

        WHITE  = (240, 240, 240)
        GREY   = (160, 160, 170)
        GREEN  = (80, 220, 80)
        YELLOW = (255, 220, 60)
        f, fb, fs = self.font, self.font_b, self.font_s
        x0 = px + 12
        y  = 14
        ROW = 20

        def txt(surface, text, color, bold=False, small=False):
            nonlocal y
            fn = fb if bold else (fs if small else f)
            surface.blit(fn.render(text, True, color), (x0, y))
            y += ROW

        def gap(n=6):
            nonlocal y
            y += n

        def hline():
            nonlocal y
            pygame.draw.line(self.screen, (70, 70, 85),
                             (px + 8, y), (px + self.hud_w - 8, y), 1)
            y += 8

        # --- Title ---
        txt(self.screen, "SWARM STATUS", WHITE, bold=True)
        hline()

        # --- Trial info ---
        txt(self.screen, f"Time:  {timer:.1f} s", WHITE)
        txt(self.screen, f"Ants:  {total}", WHITE)
        if delivered:
            txt(self.screen, "STATUS:  DELIVERED!", GREEN, bold=True)
        else:
            txt(self.screen, "STATUS:  transporting...", GREY)
        txt(self.screen, f"Payload dist to HOME:  {dist_str}", WHITE)
        gap()
        hline()

        # --- Attachment ---
        txt(self.screen, f"Attached to payload:  {attached} / {total}", YELLOW, bold=True)
        gap()
        hline()

        # --- State breakdown ---
        txt(self.screen, "AGENT STATES", WHITE, bold=True)
        gap(4)

        STATES = [
            ("Searching",           "SEARCHING",           (0, 200, 0)),
            ("Intercept payload",   "INTERCEPT_TARGET",    (0, 200, 255)),
            ("Retrieving (push)",   "RETRIEVING",          (0, 80, 255)),
            ("Shuffling",           "SHUFFLING",           (255, 220, 0)),
            ("Return to base",      "RETURN_TO_BASE",      (255, 140, 0)),
            ("Return to payload",   "RETURNING_TO_TARGET", (180, 0, 220)),
            ("Intercept small obj", "INTERCEPT_SMALL",     (255, 100, 160)),
            ("Carrying small obj",  "CARRYING",            (140, 80,  40)),
        ]
        for label, key, col in STATES:
            n = sc.get(key, 0)
            pygame.draw.circle(self.screen, col, (x0 + 5, y + 7), 5)
            self.screen.blit(fs.render(f"{label}: {n}", True, WHITE), (x0 + 16, y))
            y += 18

        gap()
        hline()

        # --- Pheromone legend ---
        txt(self.screen, "PHEROMONE LAYERS", WHITE, bold=True)
        gap(2)

        pygame.draw.circle(self.screen, (0, 80, 220), (x0 + 5, y + 7), 5)
        self.screen.blit(fs.render("Blue  =  Home trail", True, WHITE), (x0 + 16, y)); y += 17
        self.screen.blit(fs.render("  Deposited by ants pushing", True, GREY), (x0 + 8, y)); y += 15
        self.screen.blit(fs.render("  the payload. Points toward", True, GREY), (x0 + 8, y)); y += 15
        self.screen.blit(fs.render("  home. Strength ∝ # attached.", True, GREY), (x0 + 8, y)); y += 18

        pygame.draw.circle(self.screen, (140, 0, 160), (x0 + 5, y + 7), 5)
        self.screen.blit(fs.render("Purple  =  Recruit signal", True, WHITE), (x0 + 16, y)); y += 17
        self.screen.blit(fs.render("  Deposited by ants that", True, GREY), (x0 + 8, y)); y += 15
        self.screen.blit(fs.render("  gave up — calls for help.", True, GREY), (x0 + 8, y)); y += 18

        self.screen.blit(fs.render("Arrows pulse as ants deposit", True, GREY), (x0, y)); y += 15
        self.screen.blit(fs.render("and decay between deposits.", True, GREY), (x0, y)); y += 18

        hline()

        # --- Controls ---
        txt(self.screen, "CONTROLS", WHITE, bold=True)
        gap(2)
        txt(self.screen, "[SPACE]  pause / resume", GREY, small=True)
        txt(self.screen, f"[V]  pheromones: {'ON' if self.show_pheromones else 'OFF'}", GREY, small=True)

    # ------------------------------------------------------------------
    # Main render entry point
    # ------------------------------------------------------------------
    def update(self, agents, timer, small_objects=None, target_body=None):
        # Arena background (left side only)
        pygame.draw.rect(self.screen, (240, 240, 240), (0, 0, self.sim_w, self.sim_h))

        self._draw_zones()
        self._draw_pheromones()
        self.space.debug_draw(self.draw_options)
        if small_objects:
            self._draw_small_objects(small_objects)
        self._draw_agents(agents)
        self._draw_hud(agents, timer, target_body)

        pygame.display.flip()
