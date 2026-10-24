# Writing

| File | Content |
|---|---|
| `main.tex`, `references.bib` | The note in LaTeX: cover page, one-page text, Figure 1, references. Text as submitted; Figure 1 is read from `empirics/results/figures/fig1_combined.pdf`, so the paper updates whenever the pipeline is re-run. |
| `main.pdf` | Built by `master.py` (step `paper`) or `latexmk -pdf main.tex`. |
| `original/Fedor_Shafranov_Housing.pdf` | The note as submitted on 31 July 2025 (made in Word), without the cover page. |
| `scripts/build_paper.py` | Compiles `main.tex`; skipped when LaTeX is not installed. |

Differences from the submitted PDF: references formatted with BibTeX; the first author of Gonzalez-Navarro and
Turner (2018) corrected to Marco Gonzalez-Navarro; Fisher and Leite (2018) cited by its authors' names
(the submitted text has "Fishe and Leite").
