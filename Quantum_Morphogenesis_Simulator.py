import sys
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg
from opensimplex import OpenSimplex
import colorsys

# Initialize OpenSimplex for noise generation
tmp = OpenSimplex(seed=np.random.randint(0, 100000))  # Added seed
def pnoise2(x, y):
    return tmp.noise2(x, y)

class QuantumAutomaton2D:
    def __init__(self, initial_width=128, initial_height=128):
        self.width = initial_width
        self.height = initial_height
        self.grid = np.zeros((self.width, self.height), dtype=np.float32)  # 2D grid for cells
        self.time = 0
        self.environment = np.random.rand(self.width, self.height)  # Environmental noise
        self.params = {
            'entanglement': 0.15,
            'mutation_rate': 0.01,
            'quantum_flux': 0.7,
            'field_strength': 0.5,
            'gravity': 0.1,  # Gravity-like attraction
            'temperature': 0.5,  # Environmental temperature
            'decay_rate': 0.01,  # Energy decay over time
        }
        self.rules = self.generate_quantum_rules()
        self.initialize_cells()

    def initialize_cells(self):
        # Start with a few cells in the center
        center_x, center_y = self.width // 2, self.height // 2
        self.grid[center_x, center_y] = 1.0
        self.grid[center_x + 1, center_y] = 1.0
        self.grid[center_x - 1, center_y] = 1.0
        self.grid[center_x, center_y + 1] = 1.0
        self.grid[center_x, center_y - 1] = 1.0

    def generate_quantum_rules(self):
        return [{
            'birth': np.random.uniform(0, 1, 9),  # Size 9 for 2D (3x3 neighborhood)
            'survival': np.random.uniform(0, 1, 9),  # Size 9 for 2D
            'entanglement': np.random.randn(2),
            'decay': np.random.uniform(0.9, 0.99)
        } for _ in range(40)]

    def quantum_neighborhood(self, x, y):
        # Exclude the center cell (dx=0, dy=0)
        return [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if not (dx == 0 and dy == 0)]

    def expand_grid(self, new_width, new_height):
        # Expand the grid to accommodate new cells
        new_grid = np.zeros((new_width, new_height), dtype=np.float32)
        x_offset = (new_width - self.width) // 2
        y_offset = (new_height - self.height) // 2
        new_grid[x_offset:x_offset + self.width, y_offset:y_offset + self.height] = self.grid
        self.grid = new_grid
        self.width, self.height = new_width, new_height

    def update_universe(self):
        # Check if we need to expand the grid
        if (np.any(self.grid[0, :] > 0) or np.any(self.grid[-1, :] > 0) or
            np.any(self.grid[:, 0] > 0) or np.any(self.grid[:, -1] > 0)):
            self.expand_grid(self.width + 20, self.height + 20)

        new_grid = np.zeros_like(self.grid)
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x, y] > 0:
                    # Cell exists, apply rules
                    neighbors = self.quantum_neighborhood(x, y)
                    neighbor_count = sum(self.grid[nx, ny] > 0 for nx, ny in neighbors if 0 <= nx < self.width and 0 <= ny < self.height)
                    field = pnoise2(x / 64, y / 64 + self.time / 100)
                    rule = self.rules[int((abs(field) + self.time) % 40)]
                    survival_prob = rule['survival'][neighbor_count]  # Now neighbor_count is in [0, 8]
                    survival_prob += self.params['field_strength'] * field

                    # Apply decay
                    new_grid[x, y] = self.grid[x, y] * (1 - self.params['decay_rate'])

                    if np.random.rand() < survival_prob * rule['decay']:
                        new_grid[x, y] += self.params['gravity'] * np.random.randn()

                    # Quantum flux creation
                    if np.random.rand() < self.params['quantum_flux']:
                        for nx, ny in neighbors:
                            if 0 <= nx < self.width and 0 <= ny < self.height and new_grid[nx, ny] == 0:
                                birth_prob = rule['birth'][np.random.randint(9)]
                                if birth_prob > self.params['entanglement']:
                                    new_grid[nx, ny] = np.random.uniform(0.5, 1.0)

        self.grid = new_grid
        self.time += 1

    def get_cell_colors(self):
        colors = np.zeros((self.width, self.height, 4), dtype=np.uint8)
        for x in range(self.width):
            for y in range(self.height):
                if self.grid[x, y] > 0:
                    # Generate a color based on cell state, position, and time
                    hue = (x + y + self.time) % 360 / 360  # Cycle through hues
                    saturation = 1.0
                    lightness = self.grid[x, y]
                    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)

                    # Convert to [0, 255] and clamp values
                    r = int(max(0, min(255, r * 255)))
                    g = int(max(0, min(255, g * 255)))
                    b = int(max(0, min(255, b * 255)))
                    a = 255  # Fully opaque

                    colors[x, y] = (r, g, b, a)
        return colors

class AdvancedWindow2D(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize the automaton FIRST
        self.automaton = QuantumAutomaton2D()
        # Then initialize the UI
        self.initUI()
        # Set up the timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.evolve)
        self.timer.start(100)  # 0.1 sec delay between updates

    def initUI(self):
        self.setWindowTitle("2D Quantum Universe Simulator")
        self.setGeometry(100, 100, 800, 800)

        # 2D viewer
        self.viewer = pg.GraphicsLayoutWidget()
        self.setCentralWidget(self.viewer)
        self.plot = self.viewer.addPlot()
        self.plot.setAspectLocked(True)
        self.plot.setXRange(0, self.automaton.width)
        self.plot.setYRange(0, self.automaton.height)
        self.image = pg.ImageItem()
        self.plot.addItem(self.image)

        # Quantum control panel
        dock = QDockWidget("Quantum Parameters", self)
        panel = QWidget()
        layout = QVBoxLayout()

        self.sliders = {}
        params = self.automaton.params
        for p in params:
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(int(params[p] * 100))
            slider.valueChanged.connect(lambda v, p=p: self.update_param(p, v / 100))
            layout.addWidget(QLabel(p.replace('_', ' ').title()))
            layout.addWidget(slider)
            self.sliders[p] = slider

        panel.setLayout(layout)
        dock.setWidget(panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)

        # Help menu
        help_menu = self.menuBar().addMenu('Help')
        help_action = QAction('Quantum Guide', self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

    def update_param(self, param, value):
        self.automaton.params[param] = value

    def evolve(self):
        self.automaton.update_universe()
        colors = self.automaton.get_cell_colors()
        self.image.setImage(colors, levels=(0, 255))

    def show_help(self):
        help_text = """2D Quantum Universe Simulator

This system evolves using 40 quantum-inspired rules that:
1. Create matter through quantum fluctuations
2. Entangle distant cells through spooky action
3. Interact with environmental noise fields
4. Decay over time unless reinforced

Controls:
- Adjust quantum parameters in right panel
- Rules mutate automatically (mutation rate parameter)
- Patterns emerge from quantum vacuum fluctuations

The system can generate:
- Organic biological-like structures
- Crystal growth patterns
- Fluid dynamics simulations
- Abstract topological manifolds"""
        QMessageBox.information(self, "Quantum Guide", help_text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = AdvancedWindow2D()
    win.show()
    sys.exit(app.exec_())