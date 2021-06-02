import pandas as pd
from pathlib import Path
from astropy import units as u
from astropy.coordinates import SpectralCoord
from lineview.core.spectrum import Spectrum
import numpy as np

def read_csv(path: str | Path) -> Spectrum:
    """
    Reads a CSV, TSV, or TXT file and attempts to auto-detect the frequency/flux columns.
    """
    df = pd.read_csv(path, sep=None, engine='python')
    
    # Heuristics for column names
    cols = [c.lower().strip() for c in df.columns]
    
    x_col = None
    y_col = None
    
    # Try to find x axis
    for name in ['frequency', 'freq', 'wavelength', 'wave', 'velocity', 'x', '#frequency']:
        for c in cols:
            if name in c:
                x_col = c
                break
        if x_col:
            break
            
    # Try to find y axis
    for name in ['flux', 'intensity', 'power', 'ta*', 'y', 'data', 'amplitude']:
        for c in cols:
            if name in c:
                y_col = c
                break
        if y_col:
            break
            
    if not x_col and not y_col:
        if len(cols) >= 2:
            x_col, y_col = df.columns[0], df.columns[1]
        else:
            raise ValueError("Could not find enough columns in CSV")
            
    elif not x_col:
        x_col = [c for c in df.columns if c != y_col][0]
    elif not y_col:
        y_col = [c for c in df.columns if c != x_col][0]
        
    x_data = df[x_col].values
    y_data = df[y_col].values
    
    # Detect units from column name
    x_unit = u.dimensionless_unscaled
    unit_map = {
        'hz': 'Hz', 'khz': 'kHz', 'mhz': 'MHz', 'ghz': 'GHz', 'thz': 'THz',
        'm/s': 'm/s', 'km/s': 'km/s', 'm': 'm', 'cm': 'cm', 'mm': 'mm', 'nm': 'nm', 'um': 'um',
        'jy': 'Jy', 'k': 'K', 'dbm': 'dBm'
    }
    for unit_str, astropy_unit in unit_map.items():
        if unit_str in x_col:
            x_unit = u.Unit(astropy_unit)
            break
            
    y_unit = u.dimensionless_unscaled
    for unit_str, astropy_unit in unit_map.items():
        if unit_str in y_col:
            if unit_str == 'dbm':
                pass
            else:
                try:
                    y_unit = u.Unit(astropy_unit)
                except ValueError:
                    y_unit = u.dimensionless_unscaled
            break
            
    spectral_axis = SpectralCoord(x_data, unit=x_unit)
    flux = y_data * y_unit
    
    meta = {
        'SOURCE_FILE': str(path),
        'X_COL': x_col,
        'Y_COL': y_col
    }
    
    return Spectrum(flux=flux, spectral_axis=spectral_axis, metadata=meta)
