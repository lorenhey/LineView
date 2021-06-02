import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SpectralCoord
from lineview.core.spectrum import Spectrum
from lineview.core.measure import measure_region, compute_channel_widths
from lineview.core.fit import fit_gaussian
from lineview.core.baseline import fit_baseline

def test_integral():
    # Integral of Gaussian: A * sigma * sqrt(2pi)
    x = np.linspace(-10, 10, 1000)
    amp = 2.0
    sigma = 1.0
    y = amp * np.exp(-x**2 / (2 * sigma**2))
    
    s = Spectrum(
        flux=y * u.Jy,
        spectral_axis=SpectralCoord(x, unit=u.km/u.s)
    )
    
    res = measure_region(s, -10 * u.km/u.s, 10 * u.km/u.s)
    expected_integral = amp * sigma * np.sqrt(2 * np.pi)
    
    # Due to discrete sampling, it will be close
    assert np.isclose(res['integral'].value, expected_integral, rtol=1e-3)
    assert res['integral'].unit == u.Jy * u.km / u.s

def test_fwhm():
    # FWHM = 2 * sqrt(2*ln(2)) * sigma
    x = np.linspace(-10, 10, 1000)
    amp = 2.0
    sigma = 1.0
    y = amp * np.exp(-x**2 / (2 * sigma**2))
    
    s = Spectrum(
        flux=y * u.Jy,
        spectral_axis=SpectralCoord(x, unit=u.km/u.s)
    )
    
    res = measure_region(s, -10 * u.km/u.s, 10 * u.km/u.s)
    expected_fwhm = 2.35482 * sigma
    
    assert np.isclose(res['fwhm'].value, expected_fwhm, rtol=1e-2)

def test_gaussian_fit():
    x = np.linspace(1419, 1421, 1000)
    amp = 5.0
    cen = 1420.4
    sigma = 0.1
    y = amp * np.exp(-(x - cen)**2 / (2 * sigma**2))
    
    # add a tiny bit of noise
    np.random.seed(42)
    y += np.random.normal(0, 0.01, size=len(x))
    
    s = Spectrum(
        flux=y * u.Jy,
        spectral_axis=SpectralCoord(x, unit=u.MHz)
    )
    
    fit = fit_gaussian(s, 1419 * u.MHz, 1421 * u.MHz)
    
    assert np.isclose(fit['amplitude'].value, amp, rtol=1e-2)
    assert np.isclose(fit['center'].value, cen, rtol=1e-4)
    assert np.isclose(fit['sigma'].value, sigma, rtol=1e-2)

def test_baseline_fit():
    x = np.linspace(100, 200, 100)
    # y = 2x + 5
    y = 2.0 * x + 5.0
    
    # Add a fake line in the middle
    y[40:60] += 10.0
    
    s = Spectrum(
        flux=y * u.K,
        spectral_axis=SpectralCoord(x, unit=u.MHz)
    )
    
    # Fit baseline using edges
    regions = [
        (100 * u.MHz, 120 * u.MHz),
        (180 * u.MHz, 200 * u.MHz)
    ]
    
    s_sub = fit_baseline(s, regions, order=1)
    
    # Edges should be close to 0 now
    assert np.allclose(s_sub.flux.value[:20], 0.0, atol=1e-10)
    assert np.allclose(s_sub.flux.value[80:], 0.0, atol=1e-10)
    
    # The line should still be there, amplitude 10
    assert np.isclose(np.max(s_sub.flux.value), 10.0, rtol=1e-2)
