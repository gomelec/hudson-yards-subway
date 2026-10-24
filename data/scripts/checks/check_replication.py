"""
check_replication.py — compare pipeline outputs with (1) the output of the original notebooks and
(2) the frozen baseline in archive/baseline/.

    python data/scripts/checks/check_replication.py                 # check
    python data/scripts/checks/check_replication.py --set-baseline  # freeze current outputs

(1) Legacy check. The only intermediate file the original notebooks saved is
    `pluto_agg_MN_all_years.csv` (kept in archive/legacy_outputs/). The new
    data/clean/pluto/pluto_agg_MN_all_years.csv must match it cell by cell.
(2) Baseline check. Every output listed in OUTPUTS is compared with its copy in archive/baseline/.
    Outputs without a baseline copy are reported and skipped.

Numbers are compared with a relative tolerance of 1e-9 (CSV float round-trips differ in the
last digit across platforms); everything else must be identical. Exit code 0 = no differences.
"""
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import config  # noqa: E402

LEGACY = config.ROOT / "archive" / "legacy_outputs" / "pluto_agg_MN_all_years.csv"
OUTPUTS = [
    config.CLEAN / "pluto" / "pluto_agg_MN_all_years.csv",
    config.CLEAN / "lodes" / "hudson_commuters.csv",
    config.CLEAN / "lodes" / "total_workers.csv",
    config.PROCESSED / "commute_distance.csv",
    config.TABLES / "panel_a_built_area.csv",
    config.TABLES / "panel_b_commuters_by_distance.csv",
]
RTOL = 1e-9


def compare(label, ref_path, new_path):
    ref = pd.read_csv(ref_path, dtype=str, keep_default_na=False)
    new = pd.read_csv(new_path, dtype=str, keep_default_na=False)
    problems = []
    if list(ref.columns) != list(new.columns):
        problems.append(f"columns differ: {sorted(set(ref.columns) ^ set(new.columns))}")
    if len(ref) != len(new):
        problems.append(f"rows differ: {len(ref)} vs {len(new)}")
    if not problems:
        n_diff = 0
        for col in ref.columns:
            a, b = ref[col], new[col]
            neq = a != b
            if not neq.any():
                continue
            an, bn = pd.to_numeric(a[neq], errors="coerce"), pd.to_numeric(b[neq], errors="coerce")
            both_num = an.notna() & bn.notna()
            close = both_num & np.isclose(an, bn, rtol=RTOL, atol=0)
            bad = (~close).sum()
            if bad:
                n_diff += bad
                problems.append(f"{col}: {bad} cells differ, e.g. {a[neq][~close].iloc[0]!r} vs {b[neq][~close].iloc[0]!r}")
        if not problems:
            print(f"  OK         {label} ({len(ref):,} rows)")
            return True
    print(f"  DIFFERENT  {label}")
    for p in problems:
        print(f"             {p}")
    return False


def main():
    rel = lambda p: p.relative_to(config.ROOT)  # noqa: E731
    if "--set-baseline" in sys.argv:
        config.BASELINE.mkdir(parents=True, exist_ok=True)
        for p in OUTPUTS:
            if p.exists():
                shutil.copy2(p, config.BASELINE / p.name)
                print(f"  frozen {rel(p)}")
        return 0

    ok = True
    print("(1) original notebook output")
    new = OUTPUTS[0]
    if not LEGACY.exists():
        print(f"  missing {rel(LEGACY)}")
        ok = False
    elif new.exists():
        ok &= compare(f"{rel(new)} vs {rel(LEGACY)}", LEGACY, new)
    else:
        print(f"  missing {rel(new)} — run the cleaning stage first")
        ok = False

    print("\n(2) frozen baseline (archive/baseline)")
    for p in OUTPUTS:
        base = config.BASELINE / p.name
        if not p.exists():
            print(f"  skipped    {rel(p)} (not produced yet)")
        elif not base.exists():
            print(f"  skipped    {rel(p)} (no baseline copy; run --set-baseline once to freeze it)")
        else:
            ok &= compare(str(rel(p)), base, p)

    print("\nRESULT:", "all outputs identical" if ok else "DIFFERENCES FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
