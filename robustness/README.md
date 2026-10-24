# Robustness checks for Figure 1, Panel B

Stand-alone; nothing in the main pipeline is changed. Run from the project root after `master.py`:

```bash
uv run python robustness/robustness_checks.py     # ~2 min; reads data/raw and data/processed
```

Outputs in `results/`: `tables/` (CSV), `figures/` (PNG), `data/flows_by_home_tract.csv`
(LODES flows by NYC home tract and year, cached; delete it to rebuild from the raw files).

## Specifications

| | Change relative to the paper | Why |
|---|---|---|
| S0 | none — reproduces Panel B (pre means 8.12, 3.71, 3.21, 2.90, 2.50, 1.89) | check |
| S1 | SEs clustered by home tract | the same tract appears up to 36 times (3 destinations × 12 years) |
| S2 | centroid-to-centroid distance | edge distance puts every adjacent tract at 0 km |
| S3 | one row per home tract × year (99.01–99.03 summed) | paper weights tract × destination pairs |
| **S4** | **all 2,279 NYC home tracts every year, zeros included (balanced)** | **paper drops tracts with no HY commuters, so the sample changes over time** |
| S5 | S4 + centroid distance | |
| S6 | S4, LODES 2015 counted as *before* | LODES measures jobs in April; the station opened 13 Sep 2015 |
| S7 | S4 without 2015 | transition year |
| S8 | S4 without 2018 | tract 99.02 jumps from 4,900 jobs (2017) to 22,788 (2018) |
| S9 | S4 weighted by workers | ratio of totals instead of mean of tract ratios |
| S10 | S4, "before" = 2011–14 and without 2018 | 2009–10 lie far below all later years; 2018 is a one-year spike |
| E | event study on S4: tract + year FE, bin × year effects vs. 2014 and vs. > 10 km | pre-trends / timing |
| P | placebo destinations: Midtown ring (71 tracts, 0.5–3 km from HY) and Manhattan excl. HY | is it a citywide trend? |

## Results

**Change after vs. before 2015 in HY commuters per 1,000 workers (95 % CI, clustered by home tract)**

| | < 1 km | 1–3 km | 3–5 km | 5–7 km | 7–10 km | > 10 km |
|---|---|---|---|---|---|---|
| S0 paper (iid) | −1.28 [−2.52, −0.04] | +0.68 [+0.43, +0.92] | +0.77 [+0.55, +0.99] | +0.95 [+0.73, +1.18] | +0.70 [+0.53, +0.86] | +0.10 [+0.03, +0.17] |
| S1 clustered | −1.28 [−3.22, +0.67] | +0.68 [+0.51, +0.84] | +0.77 [+0.60, +0.94] | +0.95 [+0.74, +1.17] | +0.70 [+0.56, +0.83] | +0.10 [+0.01, +0.19] |
| S4 zeros incl. | −1.96 [−5.99, +2.07] | +2.40 [+1.98, +2.82] | +2.78 [+2.16, +3.39] | +2.94 [+2.50, +3.38] | +2.41 [+2.07, +2.76] | +0.40 [+0.31, +0.49] |
| S8 without 2018 | −4.53 [−8.81, −0.25] | +0.36 [−0.08, +0.79] | +1.15 [+0.53, +1.77] | +1.19 [+0.84, +1.55] | +1.17 [+0.89, +1.45] | +0.11 [+0.02, +0.20] |
| S9 worker-weighted | **+1.47** [+0.46, +2.48] | +2.38 [+1.97, +2.78] | +2.51 [+2.04, +2.98] | +2.85 [+2.38, +3.32] | +2.52 [+2.20, +2.84] | +0.45 [+0.37, +0.53] |

All specifications: `results/tables/pre_post_by_spec.csv`, `results/figures/r1_pre_post_by_spec.png`.

**Means by period (S4), per 1,000 workers** — the comparison the before/after split hides:

| | 2009–10 | 2011–14 | 2015–17 | 2011–14 → 2015–17 |
|---|---|---|---|---|
| < 1 km | 15.2 | 22.4 | 15.4 | −31 % |
| 1–3 km | 5.3 | 11.7 | 9.3 | −20 % |
| 3–5 km | 4.9 | 9.3 | 8.5 | −9 % |
| 5–7 km | 5.2 | 7.4 | 7.3 | −2 % |
| 7–10 km | 3.7 | 6.0 | 5.9 | −1 % |
| > 10 km | 2.2 | 3.9 | 3.5 | −11 % |

## What holds and what does not

1. **The paper's numbers replicate** (S0), and the far-bin increases survive clustering, centroid distances,
   zeros, per-tract aggregation, worker weights and the 2015 timing choices (S1–S7, S9).
2. **It is specific to Hudson Yards.** For the Midtown ring and the rest of Manhattan, the same before/after
   change is −7 % to +8 % in every bin, against +25 % to +46 % for Hudson Yards in 1–10 km (`r4`).
   So it is not a citywide shift towards longer commutes.
3. **But the timing does not point to the station.** The before/after gap comes from two jumps that are
   not in 2015 (`r2`, `r3`, `r5`):
   - **2011**: commuting to HY rises in all bins at once, when jobs in tract 99.01 triple (2,322 → 7,032).
     That is before the station and before construction started (2012).
   - **2018**: a one-year spike in all bins, driven by tract 99.02 (4,900 → 22,788 → 12,598 jobs).
     Rises like this usually come from an employer reporting its jobs under a different address, or from a
     large tenant moving in. It is not a gradual response.

   Between 2011–14 and 2015–17, the years right around the opening, shares **fall** in every bin. The
   event study has significant pre-period coefficients (1–3, 3–5 and 7–10 km in 2009–10). For 1–10 km the
   post-period coefficients stay close to zero until 2018, while the < 1 km bin drops significantly in
   2015–17 (−2.5 to −5.7 per 1,000 relative to 2014 and to > 10 km). Dropping 2018 (S8) cuts the 1–10 km effects by half or more.
4. **The before/after decline in the closest bin is not robust.** It rests on 32 home tracts, its CI covers
   zero once SEs are clustered (S1–S4, S6, S7), and it turns positive when tracts are weighted by workers
   (S9). The comparison around the opening (point 5 and the event study) is more informative.
5. **What survives in relative terms:** around the opening, nearby shares fall much more (−31 %, −20 %) than
   shares at 5–10 km (−1 %, −2 %), so the distance gradient flattens. The most defensible version of the fact is
   *"the Hudson Yards commuting catchment became less local"*, not *"more people from far away commute
   because of the station"*.

## Suggested next steps

- Use 2016+ as "after" and report the yearly series (`r2`) instead of a two-period pool.
- Treat 2018 explicitly: show it with and without tract 99.02, and check employer moves
  (the first towers, 10 and 30 Hudson Yards, opened in 2016–19).
- Use a difference-in-differences against the Midtown ring (`placebo_destinations.csv`) as the comparison.
- Panel A has the same timing issue: built area rises in 2014 and again in 2016. Construction began in
  2012, so the station and the development cannot be told apart with one treated tract.
