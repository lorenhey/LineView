import numpy as np
from astropy import units as u
from typing import Dict, Any, Tuple
from .spectrum import Spectrum

def compute_channel_widths(axis: u.Quantity) -> u.Quantity:
    """
    Compute width of each channel.
    For interior points, uses distance between midpoints of adjacent channels.
    For edges, extrapolates.
    """
    if len(axis) < 2:
        return np.array([1.0]) * axis.unit
        
    vals = axis.value
    diffs = np.diff(vals)
    
    widths = np.empty_like(vals)
    widths[1:-1] = (diffs[:-1] + diffs[1:]) / 2.0
    widths[0] = diffs[0]
    widths[-1] = diffs[-1]
    
    # Abs because axis might be decreasing
    return np.abs(widths) * axis.unit

def extract_region(s: Spectrum, min_val: u.Quantity, max_val: u.Quantity) -> Tuple[Spectrum, np.ndarray]:
    """
    Returns a cropped spectrum and the boolean mask applied to the original data.
    """
    axis = s.spectral_axis
    # ensure same units
    min_v = min_val.to_value(axis.unit)
    max_v = max_val.to_value(axis.unit)
    
    if min_v > max_v:
        min_v, max_v = max_v, min_v
        
    in_region = (axis.value >= min_v) & (axis.value <= max_v)
    
    # Also exclude masked data
    valid = in_region & ~s.mask
    
    s_sub = Spectrum(
        flux=s.flux[valid],
        spectral_axis=s.spectral_axis[valid],
        uncertainty=s.uncertainty[valid] if s.uncertainty is not None else None,
        mask=s.mask[valid],
        metadata=s.metadata._data
    )
    return s_sub, valid

def measure_region(s: Spectrum, min_val: u.Quantity, max_val: u.Quantity) -> Dict[str, Any]:
    """
    Calculates basic statistics over a specified region.
    """
    s_sub, valid = extract_region(s, min_val, max_val)
    
    if len(s_sub.flux) == 0:
        return {}
        
    flux = s_sub.flux
    axis = s_sub.spectral_axis
    widths = compute_channel_widths(axis)
    
    # Peak and Min
    idx_max = np.argmax(flux)
    idx_min = np.argmin(flux)
    
    peak = flux[idx_max]
    peak_pos = axis[idx_max]
    
    minimum = flux[idx_min]
    min_pos = axis[idx_min]
    
    # Centroid
    # Wait, centroid of negative lines? Centroid is usually sum(x*y)/sum(y).
    # If the line is an absorption line, this fails. 
    # Let's subtract the baseline (assuming ends of region are baseline) or just compute raw moment.
    # We will provide a simple centroid based on positive flux above a floor, to make it robust, 
    # but the user asked to "Define exactly".
    # Let's use raw moment. 
    total_flux = np.sum(flux * widths)
    if total_flux.value != 0:
        centroid = np.sum(axis * flux * widths) / total_flux
    else:
        centroid = np.nan * axis.unit
        
    # RMS
    mean_flux = np.mean(flux)
    rms = np.sqrt(np.mean((flux - mean_flux)**2))
    
    # Non-parametric FWHM
    # Find points above half-max. This only works for emission.
    half_max = peak / 2
    above_half = flux >= half_max
    if np.any(above_half):
        fwhm_pos = axis[above_half]
        fwhm = np.max(fwhm_pos) - np.min(fwhm_pos)
        # If it's a single pixel, FWHM is the width of that pixel
        if fwhm.value == 0:
            fwhm = widths[idx_max]
    else:
        fwhm = np.nan * axis.unit
        
    # Integral
    integral = np.sum(flux * widths)
    
    return {
        "channels": len(flux),
        "peak": peak,
        "peak_pos": peak_pos,
        "minimum": minimum,
        "min_pos": min_pos,
        "centroid": centroid,
        "integral": integral,
        "fwhm": abs(fwhm),
        "rms": rms,
        "mean": mean_flux,
        "median": np.median(flux)
    }
