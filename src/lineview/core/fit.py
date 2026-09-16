import numpy as np
from astropy import units as u
from typing import Tuple, List, Optional
from scipy.optimize import curve_fit
from .spectrum import Spectrum
from .measure import extract_region

def gaussian(x, amp, cen, sigma):
    return amp * np.exp(-(x - cen)**2 / (2 * sigma**2))

def fit_gaussian(s: Spectrum, min_val: u.Quantity, max_val: u.Quantity) -> dict:
    """
    Fits a single Gaussian to the specified region.
    Returns parameters and uncertainties, plus the residual.
    """
    s_sub, valid = extract_region(s, min_val, max_val)
    if len(s_sub.flux) < 4:
        raise ValueError("Not enough points to fit a Gaussian")
        
    x = s_sub.spectral_axis.value
    y = s_sub.flux.value
    
    # Guess parameters
    amp_guess = np.max(y)
    cen_guess = x[np.argmax(y)]
    # Estimate sigma from FWHM ~ 2.355 * sigma
    half_max = amp_guess / 2.0
    above = y >= half_max
    if np.sum(above) > 1:
        fwhm_guess = np.max(x[above]) - np.min(x[above])
    else:
        fwhm_guess = np.abs(x[-1] - x[0]) / 4.0
    sigma_guess = np.abs(fwhm_guess / 2.355)
    
    p0 = [amp_guess, cen_guess, sigma_guess]
    
    try:
        popt, pcov = curve_fit(gaussian, x, y, p0=p0)
        perr = np.sqrt(np.diag(pcov))
    except RuntimeError:
        raise RuntimeError("Gaussian fit failed to converge")
        
    amp, cen, sigma = popt
    amp_err, cen_err, sigma_err = perr
    
    sigma = abs(sigma) # Sigma is positive
    
    fwhm = 2.35482 * sigma
    fwhm_err = 2.35482 * sigma_err
    
    # Integral = amp * sigma * sqrt(2*pi)
    area = amp * sigma * np.sqrt(2 * np.pi)
    # Error propagation for area: A = a * s * sqrt(2pi)
    # (dA/A)^2 = (da/a)^2 + (ds/s)^2 + 2*cov(a,s)/(a*s)
    cov_as = pcov[0, 2]
    area_err = area * np.sqrt((amp_err/amp)**2 + (sigma_err/sigma)**2 + 2*cov_as/(amp*sigma))
    
    model_y = gaussian(x, *popt)
    residual = y - model_y
    rms = np.sqrt(np.mean(residual**2))
    
    return {
        "amplitude": amp * s.flux.unit,
        "amplitude_err": amp_err * s.flux.unit,
        "center": cen * s.spectral_axis.unit,
        "center_err": cen_err * s.spectral_axis.unit,
        "sigma": sigma * s.spectral_axis.unit,
        "sigma_err": sigma_err * s.spectral_axis.unit,
        "fwhm": fwhm * s.spectral_axis.unit,
        "fwhm_err": fwhm_err * s.spectral_axis.unit,
        "area": area * (s.flux.unit * s.spectral_axis.unit),
        "area_err": area_err * (s.flux.unit * s.spectral_axis.unit),
        "residual_rms": rms * s.flux.unit,
        "model_flux": model_y * s.flux.unit,
        "residual_flux": residual * s.flux.unit,
        "axis": s_sub.spectral_axis
    }
