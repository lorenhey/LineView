import numpy as np
from astropy import units as u
from astropy.coordinates import SpectralCoord
from typing import Optional, Dict, Any

class SpectrumMetadata:
    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self._data = data or {}
    
    @property
    def target(self) -> Optional[str]:
        return self._data.get('TARGET') or self._data.get('OBJECT')
    
    @property
    def rest_frequency(self) -> Optional[u.Quantity]:
        # Return rest frequency if found
        val = self._data.get('RESTFRQ')
        if val is not None:
            return val * u.Hz
        return None
        
    def __getitem__(self, key: str) -> Any:
        return self._data[key]
        
    def __contains__(self, key: str) -> bool:
        return key in self._data

class Spectrum:
    """
    Core representation of a scientific spectrum.
    """
    def __init__(
        self,
        flux: u.Quantity,
        spectral_axis: SpectralCoord,
        uncertainty: Optional[u.Quantity] = None,
        mask: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        if not isinstance(flux, u.Quantity):
            raise TypeError("Flux must be an astropy Quantity")
        if not isinstance(spectral_axis, SpectralCoord):
            raise TypeError("Spectral axis must be an astropy SpectralCoord")
            
        if len(flux) != len(spectral_axis):
            raise ValueError("Flux and spectral axis must have the same length")
            
        self.flux = flux
        self.spectral_axis = spectral_axis
        self.uncertainty = uncertainty
        
        if mask is not None:
            self.mask = np.asarray(mask, dtype=bool)
            if len(self.mask) != len(self.flux):
                raise ValueError("Mask must have same length as flux")
        else:
            self.mask = np.zeros(len(self.flux), dtype=bool)
            
        self.metadata = SpectrumMetadata(metadata)

    def with_velocity_axis(self, rest_value: u.Quantity, convention: str = 'radio') -> 'Spectrum':
        """
        Return a new Spectrum with a velocity spectral axis, using the specified 
        rest value and Doppler convention.
        
        conventions: 'radio', 'optical', 'relativistic'
        """
        new_axis = self.spectral_axis.to(
            u.km / u.s, 
            doppler_rest=rest_value, 
            doppler_convention=convention
        )
        return Spectrum(
            flux=self.flux.copy(),
            spectral_axis=new_axis,
            uncertainty=self.uncertainty.copy() if self.uncertainty is not None else None,
            mask=self.mask.copy(),
            metadata=self.metadata._data.copy()
        )
