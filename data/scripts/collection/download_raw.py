"""
download_raw.py — fetch every raw file the replication needs into data/raw/.

    python data/scripts/collection/download_raw.py                 # download what is missing
    python data/scripts/collection/download_raw.py --link-from DIR # use copies you already have

Files (listed with sizes and MD5 checksums in raw_manifest.csv next to this script):
  data/raw/pluto/   12 archived PLUTO releases, 09v2 ... 20v8 (NYC Department of City Planning)
  data/raw/lodes/   LODES 8 NY origin-destination files, JT01, 2009-2020 (U.S. Census Bureau)
  data/raw/tracts/  2020 cartographic-boundary census tracts for NY (U.S. Census Bureau)

Files that already exist are skipped. After each download the MD5 is compared with the
checksum of the copy used for the paper; a mismatch is reported as a WARNING (the source
may have re-released the file), not an error.

--link-from DIR [DIR ...] searches the given folders (recursively, by file name) for files
that are missing and symlinks them instead of downloading. For LODES the uncompressed
`.csv` is accepted as well as the `.csv.gz`.
"""
import argparse
import csv
import gzip
import hashlib
import os
import shutil
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import config  # noqa: E402

MANIFEST = Path(__file__).with_name("raw_manifest.csv")

# DCP has moved its archive more than once; the first URL that works is used.
# Manual fallback: https://www.nyc.gov/content/planning/pages/resources (Bytes of the Big Apple archive, PLUTO).
PLUTO_URLS = [
    "https://s-media.nyc.gov/agencies/dcp/assets/files/zip/data-tools/bytes/{zip}",
    "https://www1.nyc.gov/assets/planning/download/zip/data-maps/open-data/{zip}",
]


def targets():
    """(folder, file name, candidate URLs) for every raw file."""
    out = [(config.RAW_PLUTO, z, [u.format(zip=z) for u in PLUTO_URLS])
           for z, _, _ in config.PLUTO_RELEASES.values()]
    out += [(config.RAW_LODES, config.LODES_FILE.format(year=y), [config.LODES_URL.format(year=y)])
            for y in config.YEARS]
    out.append((config.RAW_TRACTS, config.TRACTS_FILE, [config.TRACTS_URL]))
    return out


def md5(path: Path, decompress: bool = False) -> str:
    h = hashlib.md5()
    opener = gzip.open if decompress else open
    with opener(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest():
    if not MANIFEST.exists():
        return {}
    with open(MANIFEST, newline="") as f:
        return {r["file"]: r for r in csv.DictReader(f)}


def verify(path: Path, manifest):
    """Compare with the checksum of the file used for the paper.
    LODES checksums refer to the *uncompressed* CSV (the paper used .csv, the server ships .csv.gz)."""
    name = path.name if not path.name.endswith(".csv") else path.name + ".gz"
    row = manifest.get(name)
    if not row or not row.get("md5"):
        print(f"   (no reference checksum for {name})")
        return
    gz = path.suffix == ".gz" and row.get("md5_of") == "uncompressed"
    got = md5(path, decompress=gz)
    if got == row["md5"]:
        print(f"   checksum OK ({row['md5_of']})")
    else:
        print(f"   WARNING: checksum differs from the copy used in the paper "
              f"({got} vs {row['md5']}) — the source may have re-released the file.")


def download(urls, dest: Path) -> bool:
    for url in urls:
        try:
            print(f"   GET {url}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (replication script)"})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest.with_suffix(dest.suffix + ".part"), "wb") as f:
                shutil.copyfileobj(r, f, 1 << 20)
            dest.with_suffix(dest.suffix + ".part").rename(dest)
            return True
        except Exception as e:  # noqa: BLE001 — try the next URL
            print(f"   failed: {e}")
            dest.with_suffix(dest.suffix + ".part").unlink(missing_ok=True)
    return False


def find_local(name: str, dirs):
    alts = [name] + ([name[:-3]] if name.endswith(".csv.gz") else [])
    for d in dirs:
        for alt in alts:
            hits = sorted(Path(d).expanduser().rglob(alt))
            if hits:
                return hits[0]
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--link-from", nargs="+", metavar="DIR", default=[],
                    help="folders with copies of the raw files; missing files are symlinked from there")
    ap.add_argument("--no-verify", action="store_true", help="skip checksum comparison")
    args = ap.parse_args()
    manifest = read_manifest()

    failed = []
    for folder, name, urls in targets():
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / name
        existing = dest if dest.exists() else (dest.with_suffix("") if name.endswith(".gz") and dest.with_suffix("").exists() else None)
        print(f"{folder.relative_to(config.ROOT)}/{name}")
        if existing:
            print(f"   present: {existing.name}")
            continue
        local = find_local(name, args.link_from) if args.link_from else None
        if local:
            link = folder / local.name
            link.symlink_to(os.path.relpath(local.resolve(), folder.resolve()))  # relative: survives moving the parent folder
            print(f"   linked -> {local}")
            existing = link
        elif download(urls, dest):
            existing = dest
        else:
            failed.append(name)
            continue
        if not args.no_verify:
            verify(existing, manifest)

    if failed:
        print("\nCould not obtain:\n  " + "\n  ".join(failed))
        print("Download them by hand (see data/raw/README.md) and re-run.")
        return 1
    print("\nAll raw files present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
