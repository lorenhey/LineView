# LineView

`LineView` is a lightweight scientific viewer for astronomical spectra: open a spectrum, understand its spectral coordinates, overlay known transitions, switch between frequency and radial velocity, measure spectral features and export the result.

It is designed to answer “what am I looking at?” before you reach for a full reduction package.

## Quick Start

```bash
lineview spectrum.fits
```

## Features
- **Open First**: Drag and drop FITS, SDFITS, CSV, TSV, or TXT files and see them instantly.
- **Scientifically Rigorous Axes**: Seamlessly switch between frequency and velocity using radio, optical, or relativistic Doppler conventions.
- **Reference Frame Aware**: Clearly displays topocentric, LSRK, and other frames, refusing to guess when metadata is missing.
- **Interactive Measurements**: Select regions to measure centroids, FWHMs, integrated areas, and local RMS.
- **Line Catalog**: Includes a curated, provenance-aware catalog of common radio lines (H I, OH, CO) with support for custom user catalogs.
- **CLI & Python API**: Perform quick terminal inspections or integrate `LineView` into your Python scripts.

## Installation

```bash
pip install lineview
```

Or using `pipx`:

```bash
pipx install lineview
```

## Documentation
Full documentation is available in the `docs/` directory.

## License
MIT License.
