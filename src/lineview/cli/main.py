import typer
from pathlib import Path
from lineview.io.reader import read_spectrum

app = typer.Typer(help="LineView - A lightweight scientific viewer for astronomical spectra.")

@app.command()
def inspect(path: Path):
    """
    Open and print spectrum metadata to the terminal.
    """
    s = read_spectrum(path)
    typer.echo(f"File: {path}")
    typer.echo(f"Channels: {len(s.flux)}")
    typer.echo(f"Spectral axis unit: {s.spectral_axis.unit}")
    typer.echo(f"Flux unit: {s.flux.unit}")
    if s.metadata.rest_frequency is not None:
        typer.echo(f"Rest frequency: {s.metadata.rest_frequency}")
    
    # print some basic metadata
    typer.echo("\n--- Metadata ---")
    if s.metadata.target:
        typer.echo(f"Target: {s.metadata.target}")
    
    for k, v in list(s.metadata._data.items())[:10]:
        typer.echo(f"{k}: {v}")

@app.command()
def measure(path: Path, min_val: float, max_val: float):
    """
    Measure basic statistics over a specified region.
    """
    from lineview.core.measure import measure_region
    from astropy import units as u
    
    s = read_spectrum(path)
    # assume same unit as axis for the input values
    unit = s.spectral_axis.unit
    res = measure_region(s, min_val * unit, max_val * unit)
    
    for k, v in res.items():
        typer.echo(f"{k}: {v}")
        
@app.command()
def fit(path: Path, min_val: float, max_val: float):
    """
    Fit a Gaussian to the specified region.
    """
    from lineview.core.fit import fit_gaussian
    from astropy import units as u
    
    s = read_spectrum(path)
    unit = s.spectral_axis.unit
    try:
        res = fit_gaussian(s, min_val * unit, max_val * unit)
        for k, v in res.items():
            if not k.endswith('flux') and k != 'axis':
                typer.echo(f"{k}: {v}")
    except Exception as e:
        typer.echo(f"Fit failed: {e}")

def main():
    app()
