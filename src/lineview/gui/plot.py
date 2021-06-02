import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal
import numpy as np

# Use a technical, quiet theme
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
pg.setConfigOptions(antialias=True)

class SpectrumPlotWidget(QWidget):
    # Signal emitted when cursor moves, sending (x, y)
    cursor_moved = Signal(float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.setMouseEnabled(x=True, y=True)
        self.plot_item.showGrid(x=True, y=True, alpha=0.3)
        
        # Crosshair
        self.v_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color='r', style=Qt.DashLine))
        self.h_line = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen(color='r', style=Qt.DashLine))
        self.plot_item.addItem(self.v_line, ignoreBounds=True)
        self.plot_item.addItem(self.h_line, ignoreBounds=True)
        
        self.proxy = pg.SignalProxy(self.plot_item.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)
        
        self.spectrum_curve = None
        
    def plot_spectrum(self, x, y, xlabel="", ylabel=""):
        self.plot_item.clear()
        
        # Re-add crosshairs
        self.plot_item.addItem(self.v_line, ignoreBounds=True)
        self.plot_item.addItem(self.h_line, ignoreBounds=True)
        
        self.spectrum_curve = self.plot_item.plot(x, y, pen=pg.mkPen(color='b', width=1.5))
        
        self.plot_item.setLabel('bottom', xlabel)
        self.plot_item.setLabel('left', ylabel)
        
        # Auto range
        self.plot_item.enableAutoRange()
        
    def mouse_moved(self, evt):
        pos = evt[0]
        if self.plot_item.sceneBoundingRect().contains(pos):
            mouse_point = self.plot_item.vb.mapSceneToView(pos)
            self.v_line.setPos(mouse_point.x())
            self.h_line.setPos(mouse_point.y())
            self.cursor_moved.emit(mouse_point.x(), mouse_point.y())
