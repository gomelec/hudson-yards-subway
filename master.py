"""
master.py — runs the whole Hudson Yards replication, from raw downloads to Figure 1.

Usage (from the project folder):
    uv run python master.py                      # everything: download, clean, build, figures
    uv run python master.py --check              # ... then compare with the original output and the baseline
    uv run python master.py --set-baseline       # ... then freeze the current outputs as the new baseline
    uv run python master.py --stage cleaning     # one stage only (collection, cleaning, processing, empirics)
    uv run python master.py --only panel_b       # one step only
    uv run python master.py --from processing    # this stage and all later ones
    uv run python master.py --list               # show the steps without running anything
    uv run python master.py --link-from ~/old/project   # collection: symlink raw files you already have

Each step runs in a fresh process with the project folder as working directory.
Its full output goes to one log per step and run in logs/ ; the master log lists all steps.
The master stops at the first step that fails.
"""
import argparse
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / "logs"

# ---------------------------------------------------------------------------
# Pipeline definition: (stage, step name, script path relative to ROOT). Steps run top to bottom.
# ---------------------------------------------------------------------------
STEPS = [
    ("collection", "download_raw",          "data/scripts/collection/download_raw.py"),          # PLUTO, LODES, tract boundaries -> data/raw
    ("cleaning",   "clean_pluto",           "data/scripts/cleaning/clean_pluto.py"),             # Manhattan PLUTO -> tract x year (~1 min)
    ("cleaning",   "clean_lodes",           "data/scripts/cleaning/clean_lodes.py"),             # LODES OD -> HY commuters, workers by tract (~3 min)
    ("processing", "build_commute_distance", "data/scripts/processing/build_commute_distance.py"), # per-1,000 shares + distance to HY
    ("empirics",   "panel_a",               "empirics/scripts/01_panel_a_construction.py"),       # Figure 1A
    ("empirics",   "panel_b",               "empirics/scripts/02_panel_b_commuters.py"),          # Figure 1B
    ("empirics",   "figure1",               "empirics/scripts/03_figure1_combined.py"),           # Figure 1 (A over B)
    ("robustness", "robustness_checks",     "robustness/robustness_checks.py"),                   # Panel B robustness (see robustness/README.md)
    ("writing",    "paper",                 "Writing/scripts/build_paper.py"),                    # Writing/main.pdf (skipped without LaTeX)
]
STAGES = ["collection", "cleaning", "processing", "empirics", "robustness", "writing"]
CHECK_SCRIPT = "data/scripts/checks/check_replication.py"


def run_step(stage, name, cmd_args, stamp, master_log):
    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / f"{name}_{stamp}.log"
    cmd = [sys.executable] + cmd_args

    def say(msg):
        print(msg, flush=True)
        master_log.write(msg + "\n")
        master_log.flush()

    say(f"[{datetime.now():%H:%M:%S}] {stage:<10} {name:<24} ...")
    t0 = time.time()
    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"step     : {name}\ncommand  : {' '.join(cmd_args)}\n"
                  f"started  : {datetime.now():%Y-%m-%d %H:%M:%S}\nmachine  : {platform.platform()}\n"
                  f"python   : {sys.version.split()[0]}\n{'-' * 70}\n")
        log.flush()
        rc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
        log.write(f"{'-' * 70}\nfinished : {datetime.now():%Y-%m-%d %H:%M:%S}\n"
                  f"duration : {time.time() - t0:.1f}s\nexit code: {rc}\n")
    skipped = rc == 0 and "SKIPPED:" in log_path.read_text(encoding="utf-8", errors="replace")
    status = "SKIPPED (see log)" if skipped else ("OK" if rc == 0 else f"FAILED (exit {rc})")
    say(f"{'':>12}-> {status} in {time.time() - t0:.1f}s, log: {log_path.relative_to(ROOT)}")
    if rc != 0:
        say(f"{'':>12}   last lines of the log:")
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-15:]:
            say(f"{'':>15}{line}")
    return rc == 0


def main():
    ap = argparse.ArgumentParser(description="Run the Hudson Yards replication pipeline.")
    ap.add_argument("--stage", choices=STAGES + ["all"], default="all", help="run one stage (default: all)")
    ap.add_argument("--from", dest="from_stage", choices=STAGES, help="run this stage and all later ones")
    ap.add_argument("--only", metavar="STEP", help="run a single step by name (see --list)")
    ap.add_argument("--link-from", nargs="+", metavar="DIR", help="collection: symlink raw files from these folders")
    ap.add_argument("--check", action="store_true", help="afterwards, compare outputs with the original output and the baseline")
    ap.add_argument("--set-baseline", action="store_true", help="afterwards, freeze the current outputs in archive/baseline")
    ap.add_argument("--list", action="store_true", help="list the steps and exit")
    args = ap.parse_args()

    if args.list:
        for stage, name, script in STEPS:
            print(f"{stage:<11}{name:<25}{script}")
        return 0

    if args.only:
        steps = [s for s in STEPS if s[1] == args.only]
        if not steps:
            sys.exit(f"unknown step {args.only!r}; use --list")
    elif args.from_stage:
        steps = [s for s in STEPS if STAGES.index(s[0]) >= STAGES.index(args.from_stage)]
    else:
        steps = [s for s in STEPS if args.stage == "all" or s[0] == args.stage]

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    LOGS.mkdir(parents=True, exist_ok=True)
    with open(LOGS / f"master_{stamp}.log", "w", encoding="utf-8") as master_log:
        master_log.write(f"master run {stamp} | args: {' '.join(sys.argv[1:]) or '(none)'}\n")
        for stage, name, script in steps:
            cmd_args = [script] + (["--link-from", *args.link_from] if name == "download_raw" and args.link_from else [])
            if not run_step(stage, name, cmd_args, stamp, master_log):
                print("\nStopped: fix the failing step and re-run (use --only or --from to resume).")
                return 1
        if args.set_baseline:
            run_step("check", "set_baseline", [CHECK_SCRIPT, "--set-baseline"], stamp, master_log)
        if args.check and not run_step("check", "check_replication", [CHECK_SCRIPT], stamp, master_log):
            print("\nReplication check reported differences — open the check_replication log.")
            return 1
    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
