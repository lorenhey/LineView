from pathlib import Path
from astropy.io import fits
from astropy.wcs import WCS
from astropy import units as u
from astropy.coordinates import SpectralCoord
from lineview.core.spectrum import Spectrum
import numpy as np

def read_fits(path: str | Path) -> Spectrum:
    with fits.open(path) as hdul:
        # Find the first HDU with data
        for hdu in hdul:
            if hdu.data is not None and hdu.is_image:
                return _parse_image_hdu(hdu)
            elif isinstance(hdu, fits.BinTableHDU):
                # Simple implementation for binary tables if they contain spectrum
                # (e.g. SDFITS or similar single-row multi-column)
                return _parse_bintable_hdu(hdu)
                
        raise ValueError("No suitable data found in FITS file")

def _parse_image_hdu(hdu) -> Spectrum:
    header = hdu.header
    data = hdu.data
    
    # Squeeze empty dimensions (e.g., 1x1xN)
    data = np.squeeze(data)
    
    if data.ndim != 1:
        raise NotImplementedError(f"LineView only supports 1D spectra currently. Found {data.ndim}D data after squeezing.")
        
    wcs = WCS(header)
    
    # If WCS has multiple axes, we squeezed the data, so we need to get the spectral axis
    if wcs.naxis > 1:
        wcs = wcs.spectral
        
    if not wcs.has_spectral:
        # Fallback if WCS is malformed but it's 1D
        print("Warning: WCS has no spectral axis defined. Assuming pixel coordinates.")
        # Try to manually construct if CRVAL1, CDELT1 exist
        crval = header.get('CRVAL1', 1.0)
        cdelt = header.get('CDELT1', 1.0)
        crpix = header.get('CRPIX1', 1.0)
        cunit = header.get('CUNIT1', '')
        
        try:
            unit = u.Unit(cunit)
        except ValueError:
            unit = u.dimensionless_unscaled
            
        freqs = crval + (np.arange(len(data)) + 1 - crpix) * cdelt
        spectral_axis = SpectralCoord(freqs, unit=unit)
    else:
        # Generate coordinates
        pixels = np.arange(len(data))
        coords = wcs.pixel_to_world(pixels)
        spectral_axis = SpectralCoord(coords)
        
    # Get flux unit
    bunit = header.get('BUNIT', '')
    try:
        flux_unit = u.Unit(bunit)
    except ValueError:
        flux_unit = u.dimensionless_unscaled
        
    flux = data * flux_unit
    
    return Spectrum(
        flux=flux,
        spectral_axis=spectral_axis,
        metadata=dict(header)
    )

def _parse_bintable_hdu(hdu) -> Spectrum:
    # A very simplified binary table reader
    # Look for 'FREQUENCY' or 'WAVELENGTH' array, and 'DATA' or 'FLUX' array
    # often SDFITS has DATA as an array in a cell
    header = hdu.header
    data = hdu.data
    
    if len(data) == 0:
        raise ValueError("Empty binary table")
        
    # Just grab the first row for now
    row = data[0]
    names = [n.upper() for n in data.columns.names]
    
    # Find flux column
    flux_col = None
    for name in ['DATA', 'FLUX', 'INTENSITY', 'POWER', 'SPECTRUM']:
        if name in names:
            flux_col = name
            break
            
    if not flux_col:
        raise ValueError("Could not find a flux/data column in binary table")
        
    flux_arr = row[flux_col]
    if np.isscalar(flux_arr):
        # We might have a table where each row is a channel
        flux_arr = data[flux_col]
        # Try to find frequency column
        freq_col = None
        for name in ['FREQUENCY', 'FREQ', 'WAVELENGTH', 'WAVE']:
            if name in names:
                freq_col = name
                break
        if freq_col:
            freq_arr = data[freq_col]
        else:
            freq_arr = np.arange(len(flux_arr))
            
    else:
        # The cell contains the whole spectrum
        # Look for frequency array or build from CRVAL etc in the table
        freq_col = None
        for name in ['FREQUENCY', 'FREQ', 'WAVELENGTH', 'WAVE']:
            if name in names:
                freq_col = name
                break
        if freq_col:
            freq_arr = row[freq_col]
        else:
            crval = header.get('CRVAL1', 1.0)
            cdelt = header.get('CDELT1', 1.0)
            crpix = header.get('CRPIX1', 1.0)
            freq_arr = crval + (np.arange(len(flux_arr)) + 1 - crpix) * cdelt

    # Units
    flux_unit = u.dimensionless_unscaled
    freq_unit = u.dimensionless_unscaled # Unknown by default
    
    # Fallback to dimensionless
    return Spectrum(
        flux=np.array(flux_arr) * flux_unit,
        spectral_axis=SpectralCoord(np.array(freq_arr), unit=freq_unit),
        metadata=dict(header)
    )
