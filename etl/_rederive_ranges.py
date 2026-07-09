"""One-off: re-seed the corrected data_source registry and re-derive TDWG ranges
with the doubtful/extinct skip (etl.run.load_ranges). Guarded so a flaky WCVP/GBIF
fetch cannot silently shrink the live range data — commits only if coverage holds.
Run:  PYTHONPATH=api .venv/bin/python -m etl._rederive_ranges
"""
from sqlalchemy import delete, func, select

from app import models as m
from app.db import SessionLocal
from etl.run import load_sources, load_ranges


def main() -> None:
    with SessionLocal() as s:
        old_rows = s.scalar(select(func.count()).select_from(m.RangeRegion))
        old_species = s.scalar(select(func.count(func.distinct(m.RangeRegion.species_id))))
        print(f"before: {old_rows} range rows across {old_species} species")

        # re-seed sources so a later bake carries the corrected notes
        s.execute(delete(m.DataSource))
        load_sources(s)

        # re-derive ranges (now skips doubtful/extinct WCVP occurrences)
        s.execute(delete(m.RangeRegion))
        s.flush()
        load_ranges(s)

        new_rows = s.scalar(select(func.count()).select_from(m.RangeRegion))
        new_species = s.scalar(select(func.count(func.distinct(m.RangeRegion.species_id))))
        print(f"after:  {new_rows} range rows across {new_species} species")

        # guard: expect a small drop (doubtful/extinct removed), not a collapse
        if new_species < old_species * 0.95 or new_rows < old_rows * 0.85:
            s.rollback()
            print("ABORTED — coverage dropped more than expected; rolled back. "
                  "Likely a transient fetch failure. Nothing changed.")
            return
        s.commit()
        print(f"committed. species coverage {old_species}->{new_species}, "
              f"rows {old_rows}->{new_rows} (removed {old_rows - new_rows} doubtful/extinct/stale).")


if __name__ == "__main__":
    main()
