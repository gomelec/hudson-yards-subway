"""
build_paper.py — compile Writing/main.tex to Writing/main.pdf with latexmk (pdfLaTeX + BibTeX).

Skipped (exit 0, with a message) when latexmk is not installed, so the rest of the
pipeline does not depend on a TeX installation.
"""
import shutil
import subprocess
import sys
from pathlib import Path

WRITING = Path(__file__).resolve().parents[1]

if shutil.which("latexmk") is None:
    print("SKIPPED: latexmk not found — skipping the PDF build (install TeX Live / MacTeX to build Writing/main.pdf).")
    sys.exit(0)

rc = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], cwd=WRITING).returncode
if rc == 0:
    subprocess.run(["latexmk", "-c"], cwd=WRITING)  # remove auxiliary files, keep main.pdf
    print("wrote Writing/main.pdf")
sys.exit(rc)
