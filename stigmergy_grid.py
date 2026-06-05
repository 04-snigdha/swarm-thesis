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
        
        # Grid shape: (rows, cols, 3 layers, 2 vector components)
        # Layer 0: Target Search Vector
        # Layer 1: Home Vector
        # Layer 2: Help-Signal Recruitment Vector
        self.grid = np.zeros((self.rows, self.cols, 3, 2))
        
    def _pos_to_index(self, x, y):
        col = int(max(0, min(x // self.cell_size, self.cols - 1)))
        row = int(max(0, min(y // self.cell_size, self.rows - 1)))
        return row, col

    def deposit_pheromone(self, position, vector, layer=1):
        """Deposits a vector pheromone into the specified layer."""
        row, col = self._pos_to_index(position[0], position[1])
        self.grid[row, col, layer, 0] += vector[0]
        self.grid[row, col, layer, 1] += vector[1]

    def diffuse_and_decay(self):
        """Applies diffusion and decay to all layers independently."""
        decays = [config.LAYER_0_DECAY_RATE, config.LAYER_1_DECAY_RATE, config.LAYER_2_DECAY_RATE]
        diff = config.PHEROMONE_DIFFUSION_RATE
        
        new_grid = np.copy(self.grid) * (1.0 - diff)
        
        # Simple cross diffusion for all layers and components
        for layer in range(3):
            for i in range(2): # X and Y
                padded = np.pad(self.grid[:,:,layer,i], pad_width=1, mode='constant', constant_values=0)
                diffused = (padded[:-2, 1:-1] + padded[2:, 1:-1] + 
                            padded[1:-1, :-2] + padded[1:-1, 2:]) / 4.0
                new_grid[:,:,layer,i] += diffused * diff
                
            new_grid[:,:,layer,:] *= decays[layer]
                
        self.grid = new_grid

    def get_gradient(self, position):
        """Returns the individual vectors from all 3 layers."""
        row, col = self._pos_to_index(position[0], position[1])
        search_vec = self.grid[row, col, 0]
        home_vec = self.grid[row, col, 1]
        help_vec = self.grid[row, col, 2]
        return search_vec, home_vec, help_vec
