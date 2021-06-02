import numpy as np
from astropy import units as u
from typing import List, Tuple
from .spectrum import Spectrum

def fit_baseline(s: Spectrum, regions: List[Tuple[u.Quantity, u.Quantity]], order: int = 1) -> Spectrum:
    """
    Fits a polynomial baseline to the specified regions and returns a new 
    Spectrum with the baseline subtracted.
    """
    if not regions:
        raise ValueError("No baseline regions specified")
        
    x_unit = s.spectral_axis.unit
    y_unit = s.flux.unit
    
    x_all = s.spectral_axis.value
    y_all = s.flux.value
    
    # Build mask for fitting regions
    fit_mask = np.zeros(len(x_all), dtype=bool)
    for (rmin, rmax) in regions:
        rmin_v = rmin.to_value(x_unit)
        rmax_v = rmax.to_value(x_unit)
        if rmin_v > rmax_v:
            rmin_v, rmax_v = rmax_v, rmin_v
        fit_mask |= (x_all >= rmin_v) & (x_all <= rmax_v)
        
    # Exclude global mask
    fit_mask &= ~s.mask
    
    if np.sum(fit_mask) <= order:
        raise ValueError(f"Not enough points ({np.sum(fit_mask)}) in regions to fit polynomial of order {order}")
        
    x_fit = x_all[fit_mask]
    y_fit = y_all[fit_mask]
    
    # Fit polynomial
    coeffs = np.polyfit(x_fit, y_fit, order)
    poly = np.poly1d(coeffs)
    
    # Evaluate over entire axis
    baseline_model = poly(x_all)
    
    # Subtract
    new_flux = (y_all - baseline_model) * y_unit
    
    # Provenance metadata
    meta = s.metadata._data.copy()
    meta['LINEVIEW_BASELINE_ORDER'] = order
    meta['LINEVIEW_BASELINE_METHOD'] = 'polynomial'
    
    return Spectrum(
        flux=new_flux,
        spectral_axis=s.spectral_axis,
        uncertainty=s.uncertainty.copy() if s.uncertainty is not None else None,
        mask=s.mask.copy(),
        metadata=meta
    )
