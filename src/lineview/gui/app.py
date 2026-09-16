from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFileDialog, QSplitter,
    QFormLayout, QGroupBox, QComboBox
)
from PySide6.QtCore import Qt
from pathlib import Path
import astropy.units as u

from lineview.gui.plot import SpectrumPlotWidget
from lineview.io.reader import read_spectrum
from lineview.core.lines import LineCatalog

class LineViewApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LineView")
        self.resize(1000, 700)
        self.setAcceptDrops(True)
        
        self.spectrum = None
        self.catalog = LineCatalog()
        self.active_rest_frequency = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left side: Plot
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        
        self.plot_widget = SpectrumPlotWidget()
        self.plot_widget.cursor_moved.connect(self._on_cursor_moved)
        plot_layout.addWidget(self.plot_widget)
        
        # Status readout bar under plot
        self.cursor_label = QLabel("Cursor: ")
        self.cursor_label.setStyleSheet("font-family: monospace;")
        plot_layout.addWidget(self.cursor_label)
        
        splitter.addWidget(plot_container)
        
        # Right side: Sidebar
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        
        # File operations
        btn_open = QPushButton("Open Spectrum...")
        btn_open.clicked.connect(self._open_file_dialog)
        sidebar_layout.addWidget(btn_open)
        
        # Metadata group
        meta_group = QGroupBox("Metadata")
        self.meta_layout = QFormLayout(meta_group)
        self.meta_target = QLabel("-")
        self.meta_range = QLabel("-")
        self.meta_frame = QLabel("-")
        self.meta_layout.addRow("Target:", self.meta_target)
        self.meta_layout.addRow("Range:", self.meta_range)
        self.meta_layout.addRow("Frame:", self.meta_frame)
        sidebar_layout.addWidget(meta_group)
        
        # Axis group
        axis_group = QGroupBox("Axis Control")
        axis_layout = QFormLayout(axis_group)
        
        self.cb_axis_type = QComboBox()
        self.cb_axis_type.addItems(["Frequency", "Velocity"])
        self.cb_axis_type.currentTextChanged.connect(self._update_plot)
        axis_layout.addRow("Display:", self.cb_axis_type)
        
        self.cb_rest_line = QComboBox()
        self.cb_rest_line.addItem("None", None)
        for line in self.catalog.lines:
            label = f"{line.species} {line.transition}"
            self.cb_rest_line.addItem(label, line.rest_frequency)
        self.cb_rest_line.currentIndexChanged.connect(self._on_rest_line_changed)
        axis_layout.addRow("Rest Line:", self.cb_rest_line)
        
        self.cb_doppler = QComboBox()
        self.cb_doppler.addItems(["radio", "optical", "relativistic"])
        self.cb_doppler.currentTextChanged.connect(self._update_plot)
        axis_layout.addRow("Doppler:", self.cb_doppler)
        
        # Measurements group
        measure_group = QGroupBox("Measurements")
        measure_layout = QVBoxLayout(measure_group)
        
        self.btn_region = QPushButton("Toggle Region")
        self.btn_region.setCheckable(True)
        self.btn_region.toggled.connect(self._toggle_region)
        measure_layout.addWidget(self.btn_region)
        
        self.btn_measure = QPushButton("Measure Region")
        self.btn_measure.clicked.connect(self._measure_region)
        measure_layout.addWidget(self.btn_measure)
        
        self.btn_fit = QPushButton("Fit Gaussian")
        self.btn_fit.clicked.connect(self._fit_gaussian)
        measure_layout.addWidget(self.btn_fit)
        
        self.measure_results = QLabel("Select a region and measure.")
        self.measure_results.setWordWrap(True)
        measure_layout.addWidget(self.measure_results)
        
        sidebar_layout.addWidget(measure_group)
        sidebar_layout.addStretch()
        
        splitter.addWidget(sidebar)
        splitter.setSizes([700, 300])

        self.region_item = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.open_file(Path(path))

    def _open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Spectrum", "", "Spectra (*.fits *.csv *.txt);;All Files (*)")
        if file_path:
            self.open_file(Path(file_path))
            
    def open_file(self, path: Path):
        try:
            self.spectrum = read_spectrum(path)
            self._update_metadata_ui()
            
            # Check if rest frequency is in metadata
            rest = self.spectrum.metadata.rest_frequency
            if rest is not None:
                self.cb_rest_line.addItem(f"File Header", rest)
                self.cb_rest_line.setCurrentIndex(self.cb_rest_line.count() - 1)
                
            self._update_plot()
        except Exception as e:
            self.cursor_label.setText(f"Error loading file: {e}")
            
    def _update_metadata_ui(self):
        if not self.spectrum:
            return
        
        self.meta_target.setText(self.spectrum.metadata.target or "Unknown")
        ax = self.spectrum.spectral_axis
        min_v = ax.min().value
        max_v = ax.max().value
        unit = ax.unit
        self.meta_range.setText(f"{min_v:.2f} to {max_v:.2f} {unit}")
        
        # Just display whatever specsys is available
        specsys = self.spectrum.metadata._data.get('SPECSYS', 'TOPOCENT')
        self.meta_frame.setText(specsys)

    def _on_rest_line_changed(self, index):
        self.active_rest_frequency = self.cb_rest_line.currentData()
        if self.cb_axis_type.currentText() == "Velocity":
            self._update_plot()

    def _update_plot(self):
        if not self.spectrum:
            return
            
        axis_type = self.cb_axis_type.currentText()
        
        try:
            if axis_type == "Velocity":
                if self.active_rest_frequency is None:
                    raise ValueError("Velocity conversion unavailable: no rest frequency selected.")
                    
                convention = self.cb_doppler.currentText()
                plot_spec = self.spectrum.with_velocity_axis(self.active_rest_frequency, convention)
            else:
                plot_spec = self.spectrum
                
            x = plot_spec.spectral_axis.value
            y = plot_spec.flux.value
            
            xlabel = f"{axis_type} [{plot_spec.spectral_axis.unit}]"
            ylabel = f"Intensity [{plot_spec.flux.unit}]"
            
            self.plot_widget.plot_spectrum(x, y, xlabel, ylabel)
            self.current_plot_spec = plot_spec
            
            self.cursor_label.setText(f"Loaded {len(x)} channels.")
        except Exception as e:
            self.cursor_label.setText(str(e))
            self.plot_widget.plot_item.clear()

    def _toggle_region(self, checked):
        if checked:
            if not self.region_item:
                import pyqtgraph as pg
                self.region_item = pg.LinearRegionItem()
                self.plot_widget.plot_item.addItem(self.region_item)
                
                # set default bounds to middle 20%
                if hasattr(self, 'current_plot_spec'):
                    ax = self.current_plot_spec.spectral_axis.value
                    span = np.max(ax) - np.min(ax)
                    mid = np.mean(ax)
                    self.region_item.setRegion([mid - 0.1 * span, mid + 0.1 * span])
            else:
                self.region_item.show()
        else:
            if self.region_item:
                self.region_item.hide()
                
    def _measure_region(self):
        if not self.region_item or not self.region_item.isVisible() or not hasattr(self, 'current_plot_spec'):
            return
            
        rgn = self.region_item.getRegion()
        unit = self.current_plot_spec.spectral_axis.unit
        min_v = rgn[0] * unit
        max_v = rgn[1] * unit
        
        from lineview.core.measure import measure_region
        res = measure_region(self.current_plot_spec, min_v, max_v)
        
        if not res:
            self.measure_results.setText("No data in region.")
            return
            
        txt = (
            f"Peak: {res['peak']:.4f}\n"
            f"Centroid: {res['centroid']:.4f}\n"
            f"FWHM: {res['fwhm']:.4f}\n"
            f"Integral: {res['integral']:.4e}\n"
            f"RMS: {res['rms']:.4e}"
        )
        self.measure_results.setText(txt)

    def _fit_gaussian(self):
        if not self.region_item or not self.region_item.isVisible() or not hasattr(self, 'current_plot_spec'):
            return
            
        rgn = self.region_item.getRegion()
        unit = self.current_plot_spec.spectral_axis.unit
        min_v = rgn[0] * unit
        max_v = rgn[1] * unit
        
        from lineview.core.fit import fit_gaussian
        try:
            res = fit_gaussian(self.current_plot_spec, min_v, max_v)
            
            txt = (
                f"Amp: {res['amplitude']:.4f} ± {res['amplitude_err']:.4f}\n"
                f"Cen: {res['center']:.4f} ± {res['center_err']:.4f}\n"
                f"FWHM: {res['fwhm']:.4f} ± {res['fwhm_err']:.4f}\n"
                f"Area: {res['area']:.4e} ± {res['area_err']:.4e}\n"
                f"Res. RMS: {res['residual_rms']:.4e}"
            )
            self.measure_results.setText(txt)
            
            # Plot the fit model
            x = res['axis'].value
            y = res['model_flux'].value
            # We add a temporary curve for the fit
            import pyqtgraph as pg
            fit_curve = pg.PlotCurveItem(x, y, pen=pg.mkPen('g', width=2))
            self.plot_widget.plot_item.addItem(fit_curve)
            
        except Exception as e:
            self.measure_results.setText(f"Fit failed: {e}")
        if hasattr(self, 'current_plot_spec') and self.current_plot_spec:
            # Find nearest channel
            ax = self.current_plot_spec.spectral_axis.value
            idx = (np.abs(ax - x)).argmin()
            
            x_val = ax[idx]
            y_val = self.current_plot_spec.flux.value[idx]
            
            x_unit = self.current_plot_spec.spectral_axis.unit
            y_unit = self.current_plot_spec.flux.unit
            
            # Formatted text
            txt = f"Channel: {idx} | X: {x_val:.4f} {x_unit} | Y: {y_val:.4f} {y_unit}"
            self.cursor_label.setText(txt)
