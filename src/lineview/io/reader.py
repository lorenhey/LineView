from pathlib import Path
from lineview.core.spectrum import Spectrum
from lineview.io.fits import read_fits
from lineview.io.csv import read_csv

def read_spectrum(path: str | Path) -> Spectrum:
    p = Path(path)
    ext = p.suffix.lower()
    
    if ext in ['.fits', '.fit']:
        return read_fits(p)
    elif ext in ['.csv', '.tsv', '.txt']:
        return read_csv(p)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
