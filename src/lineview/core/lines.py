import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from astropy import units as u
from astropy.units import Quantity

@dataclass
class LineEntry:
    species: str
    transition: str
    rest_frequency: Quantity
    uncertainty: Optional[Quantity]
    source: str
    aliases: List[str]
    notes: str = ""

# Verified built-in lines
# Sources should be documented.
# H I 21cm: 1420.4057517667 MHz (Kramida et al. 2012, NIST)
# OH lines: 1612.231, 1665.4018, 1667.359, 1720.530 MHz (e.g. CDMS/JPL, terrestrial standards)
# CO(1-0): 115271.2018 MHz (CDMS)
BUILTIN_LINES = [
    LineEntry(
        species="H I",
        transition="21 cm",
        rest_frequency=1420.4057517667 * u.MHz,
        uncertainty=0.0000000009 * u.MHz,
        source="NIST ASD / Kramida et al.",
        aliases=["HI", "Hydrogen"]
    ),
    LineEntry(
        species="OH",
        transition="1612 MHz",
        rest_frequency=1612.23101 * u.MHz,
        uncertainty=None,
        source="CDMS",
        aliases=["Hydroxyl"]
    ),
    LineEntry(
        species="OH",
        transition="1665 MHz",
        rest_frequency=1665.40184 * u.MHz,
        uncertainty=None,
        source="CDMS",
        aliases=["Hydroxyl"]
    ),
    LineEntry(
        species="OH",
        transition="1667 MHz",
        rest_frequency=1667.35903 * u.MHz,
        uncertainty=None,
        source="CDMS",
        aliases=["Hydroxyl"]
    ),
    LineEntry(
        species="OH",
        transition="1720 MHz",
        rest_frequency=1720.52998 * u.MHz,
        uncertainty=None,
        source="CDMS",
        aliases=["Hydroxyl"]
    ),
    LineEntry(
        species="CO",
        transition="J=1-0",
        rest_frequency=115271.2018 * u.MHz,
        uncertainty=0.0005 * u.MHz,
        source="CDMS",
        aliases=["Carbon Monoxide", "12CO"]
    ),
    LineEntry(
        species="13CO",
        transition="J=1-0",
        rest_frequency=110201.3543 * u.MHz,
        uncertainty=0.0005 * u.MHz,
        source="CDMS",
        aliases=["13CO"]
    )
]

class LineCatalog:
    def __init__(self):
        self.lines: List[LineEntry] = list(BUILTIN_LINES)
        
    def add_user_catalog(self, path: str | Path):
        """
        Load lines from a simple CSV.
        Expected columns: species, transition, frequency_mhz, uncertainty_mhz, source
        """
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                unc = row.get('uncertainty_mhz', '').strip()
                self.lines.append(
                    LineEntry(
                        species=row['species'],
                        transition=row['transition'],
                        rest_frequency=float(row['frequency_mhz']) * u.MHz,
                        uncertainty=float(unc) * u.MHz if unc else None,
                        source=row.get('source', 'User Catalog'),
                        aliases=[],
                        notes=row.get('notes', '')
                    )
                )

    def between(self, min_freq: Quantity, max_freq: Quantity) -> List[LineEntry]:
        """
        Return lines between min_freq and max_freq.
        """
        min_f = min_freq.to(u.MHz).value
        max_f = max_freq.to(u.MHz).value
        # ensure min < max
        if min_f > max_f:
            min_f, max_f = max_f, min_f
            
        results = []
        for line in self.lines:
            f = line.rest_frequency.to(u.MHz).value
            if min_f <= f <= max_f:
                results.append(line)
        return results
        
    def match(self, freq: Quantity, tolerance: Quantity) -> List[LineEntry]:
        """
        Return lines within tolerance of a frequency.
        """
        min_f = freq - tolerance
        max_f = freq + tolerance
        return self.between(min_f, max_f)
