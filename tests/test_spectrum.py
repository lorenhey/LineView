import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SpectralCoord
from lineview.core.spectrum import Spectrum

def test_doppler_radio():
    nu0 = 1420.405751 * u.MHz
    # Create spectral axis
    nu = SpectralCoord([1420.405751, 1419.0], unit=u.MHz)
    flux = np.array([1.0, 2.0]) * u.Jy
    
    s = Spectrum(flux=flux, spectral_axis=nu)
    s_vel = s.with_velocity_axis(rest_value=nu0, convention='radio')
    
    # At rest frequency, velocity should be 0
    assert np.isclose(s_vel.spectral_axis[0].value, 0.0)
    
    # For a lower frequency, velocity should be positive (source moving away)
    # v = c * (nu0 - nu)/nu0
    import astropy.constants as const
    c_km_s = const.c.to('km/s').value
    expected_v1 = c_km_s * (1420.405751 - 1419.0) / 1420.405751
    assert np.isclose(s_vel.spectral_axis[1].value, expected_v1)
    assert s_vel.spectral_axis.unit == u.km / u.s

def test_doppler_optical():
    nu0 = 1420.405751 * u.MHz
    nu = SpectralCoord([1420.405751, 1419.0], unit=u.MHz)
    flux = np.array([1.0, 2.0]) * u.Jy
    
    s = Spectrum(flux=flux, spectral_axis=nu)
    s_vel = s.with_velocity_axis(rest_value=nu0, convention='optical')
    
    # At rest frequency, velocity should be 0
    assert np.isclose(s_vel.spectral_axis[0].value, 0.0)
    
    # Optical: v = c * (lambda - lambda0)/lambda0 = c * (nu0 - nu)/nu
    import astropy.constants as const
    c_km_s = const.c.to('km/s').value
    expected_v1 = c_km_s * (1420.405751 - 1419.0) / 1419.0
    assert np.isclose(s_vel.spectral_axis[1].value, expected_v1)

def test_zero_velocity_mapping():
    nu0 = 1420.405751 * u.MHz
    nu = SpectralCoord([nu0.value], unit=u.MHz)
    flux = np.array([1.0]) * u.Jy
    s = Spectrum(flux=flux, spectral_axis=nu)
    
    for conv in ['radio', 'optical', 'relativistic']:
        s_vel = s.with_velocity_axis(rest_value=nu0, convention=conv)
        assert np.isclose(s_vel.spectral_axis[0].value, 0.0)
