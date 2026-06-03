# stigmergy_grid.py
import numpy as np
import config

class PheromoneGrid:
    def __init__(self, width=config.ARENA_WIDTH, height=config.ARENA_HEIGHT, cell_size=config.GRID_CELL_SIZE):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = width // cell_size
        self.rows = height // cell_size
        
        # Vector pheromone (X, Y components)
        self.grid = np.zeros((self.rows, self.cols, 2))
        
    def _pos_to_index(self, x, y):
        col = int(max(0, min(x // self.cell_size, self.cols - 1)))
        row = int(max(0, min(y // self.cell_size, self.rows - 1)))
        return row, col

    def deposit_pheromone(self, position, vector):
        """Deposits a vector pheromone at the given continuous position."""
        row, col = self._pos_to_index(position[0], position[1])
        self.grid[row, col, 0] += vector[0]
        self.grid[row, col, 1] += vector[1]

    def diffuse_and_decay(self):
        """Applies diffusion and decay over the vector grid field."""
        decay = config.PHEROMONE_DECAY_RATE
        diff = config.PHEROMONE_DIFFUSION_RATE
        
        new_grid = np.copy(self.grid) * (1.0 - diff)
        
        # Simple cross diffusion approximation (discrete)
        for i in range(2): # For X and Y components
            padded = np.pad(self.grid[:,:,i], pad_width=1, mode='constant', constant_values=0)
            diffused = (padded[:-2, 1:-1] + padded[2:, 1:-1] + 
                        padded[1:-1, :-2] + padded[1:-1, 2:]) / 4.0
            new_grid[:,:,i] += diffused * diff
            
        # Apply decay to prevent runaway values
        self.grid = new_grid * decay

    def get_gradient(self, position):
        """Reads the vector pheromone value at the given continuous position."""
        row, col = self._pos_to_index(position[0], position[1])
        return self.grid[row, col, 0], self.grid[row, col, 1]
